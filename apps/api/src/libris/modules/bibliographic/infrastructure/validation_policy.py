"""Deterministic supplemental SHACL for resolved v2 policies (ADR 0022).

Historical shapes remain authoritative for qualified/relational constraints.
This adapter adds only the expressible field contract; it never edits RDF data.
"""

import json
from hashlib import sha256

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import RDF, SH, XSD
from rdflib.term import Node

from libris.modules.bibliographic.domain.profile_contract import (
    IRIDefault,
    ReferenceValue,
    ResolvedProfile,
    StructuredValue,
    TextValue,
    TypedValue,
)
from libris.modules.bibliographic.domain.profile_registry import ProfileError


def _list(graph: Graph, owner: Node, predicate: URIRef, values: list[Node]) -> None:
    head = BNode()
    Collection(graph, head, values)
    graph.add((owner, predicate, head))


def _datatypes(graph: Graph, owner: Node, datatypes: tuple[str, ...]) -> None:
    if len(datatypes) == 1:
        graph.add((owner, SH.datatype, URIRef(datatypes[0])))
    else:
        choices: list[Node] = []
        for datatype in datatypes:
            choice = BNode()
            graph.add((choice, SH.datatype, URIRef(datatype)))
            choices.append(choice)
        _list(graph, owner, SH["or"], choices)


def _constraint_values(
    shapes: Graph, node: Node, predicate: URIRef, visited: frozenset[Node] = frozenset()
) -> set[str]:
    """Inspect the local sh:node/sh:or patterns; do not traverse sh:not or SPARQL."""
    if node in visited:
        return set()
    visited = visited | {node}
    values = {str(value) for value in shapes.objects(node, predicate)}
    for child in shapes.objects(node, SH.node):
        values.update(_constraint_values(shapes, child, predicate, visited))
    for head in shapes.objects(node, SH["or"]):
        for child in shapes.items(head):
            values.update(_constraint_values(shapes, child, predicate, visited))
    return values


def add_profile_constraints(shapes: Graph, profile: ResolvedProfile) -> None:
    """A reproducible supplement; schema/presentation/defaults are not RDF rules."""
    content = {
        "release_id": profile.release_id,
        "validation": [ref.model_dump(mode="json") for ref in profile.validation],
        "resources": [
            {
                "class": resource.rdf_class,
                "fields": [
                    {
                        "name": field.name,
                        "property": field.property,
                        "value": field.value.model_dump(mode="json"),
                        "policy": field.policy.model_dump(mode="json"),
                        "derived": field.derived,
                    }
                    for field in sorted(resource.fields, key=lambda f: f.name)
                ],
            }
            for resource in sorted(profile.resources, key=lambda r: r.rdf_class)
        ],
    }
    digest = sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    # Take a snapshot of local rules before adding policy shapes.
    baseline = list(shapes.triples((None, SH.targetClass, None)))
    for resource in profile.resources:
        owner = URIRef(
            f"urn:libris:policy:v1:{digest}:{sha256(resource.rdf_class.encode()).hexdigest()}"
        )
        shapes.add((owner, RDF.type, SH.NodeShape))
        shapes.add((owner, SH.targetClass, URIRef(resource.rdf_class)))
        for field in resource.fields:
            if field.derived:
                continue  # Ownership/composed shapes govern inverse properties.
            path = URIRef(field.property)
            rules = [
                rule
                for node, _, rdf_class in baseline
                if str(rdf_class) == resource.rdf_class
                for rule in shapes.objects(node, SH.property)
                if (rule, SH.path, path) in shapes
            ]
            for rule in rules:
                minimum = shapes.value(rule, SH.minCount)
                maximum = shapes.value(rule, SH.maxCount)
                node_kind = shapes.value(rule, SH.nodeKind)
                baseline_datatypes = _constraint_values(shapes, rule, SH.datatype)
                classes = _constraint_values(shapes, rule, SH["class"])
                value = field.value
                incompatible_datatype = (
                    isinstance(value, TypedValue)
                    and bool(baseline_datatypes)
                    and not set(value.datatypes) <= baseline_datatypes
                )
                incompatible_target = (
                    isinstance(value, (StructuredValue, ReferenceValue))
                    and bool(classes)
                    and bool(value.target_classes)
                    and not set(value.target_classes) <= classes
                )
                if (
                    incompatible_datatype
                    or incompatible_target
                    or (minimum is not None and field.policy.min_count < int(str(minimum)))
                    or (
                        maximum is not None
                        and (
                            field.policy.max_count is None
                            or field.policy.max_count > int(str(maximum))
                        )
                    )
                    or (node_kind is not None and node_kind != SH[field.value.node_kind])
                ):
                    raise ProfileError(
                        "contradictory_shapes",
                        f"Política contradiz shapes locais: {resource.rdf_class}/{field.name}.",
                    )
            rule = URIRef(f"{owner}:{field.name}")
            shapes.add((owner, SH.property, rule))
            shapes.add((rule, RDF.type, SH.PropertyShape))
            shapes.add((rule, SH.path, path))
            if not any(
                shapes.value(base, SH.nodeKind) == SH[field.value.node_kind] for base in rules
            ):
                shapes.add((rule, SH.nodeKind, SH[field.value.node_kind]))
            if field.policy.min_count and not any(
                shapes.value(base, SH.minCount) == Literal(field.policy.min_count) for base in rules
            ):
                shapes.add((rule, SH.minCount, Literal(field.policy.min_count)))
            if field.policy.max_count is not None and not any(
                shapes.value(base, SH.maxCount) == Literal(field.policy.max_count) for base in rules
            ):
                shapes.add((rule, SH.maxCount, Literal(field.policy.max_count)))
            value = field.value
            if isinstance(value, TextValue):
                language = value.language
                datatypes = (
                    (str(RDF.langString),)
                    if language.required
                    else (
                        (str(XSD.string), str(RDF.langString))
                        if language.enabled
                        else (str(XSD.string),)
                    )
                )
                covered_datatypes = set().union(
                    *(_constraint_values(shapes, base, SH.datatype) for base in rules)
                )
                if set(datatypes) != covered_datatypes:
                    _datatypes(shapes, rule, datatypes)
                if not any(shapes.value(base, SH.minLength) == Literal(1) for base in rules):
                    shapes.add((rule, SH.minLength, Literal(1)))
                if language.unique and not any(
                    shapes.value(base, SH.uniqueLang) == Literal(True) for base in rules
                ):
                    shapes.add((rule, SH.uniqueLang, Literal(True)))
                if language.allowed:
                    language_rule: Node = rule
                    if not language.required:
                        # An allowlist restricts tagged values; it does not require a tag.
                        language_rule, untagged, language_choice = BNode(), BNode(), BNode()
                        shapes.add((rule, SH.node, language_choice))
                        shapes.add((untagged, SH.datatype, XSD.string))
                        _list(shapes, language_choice, SH["or"], [untagged, language_rule])
                    _list(
                        shapes,
                        language_rule,
                        SH.languageIn,
                        [Literal(tag) for tag in language.allowed],
                    )
            elif isinstance(value, TypedValue):
                covered_datatypes = set().union(
                    *(_constraint_values(shapes, base, SH.datatype) for base in rules)
                )
                if set(value.datatypes) != covered_datatypes:
                    _datatypes(shapes, rule, value.datatypes)
            elif (
                not rules
                and isinstance(value, (ReferenceValue, StructuredValue))
                and value.target_classes
            ):
                choices: list[Node] = []
                if isinstance(value, ReferenceValue):
                    # Undescribed references are allowed; never fabricate their types.
                    absent, typed, has_type = BNode(), BNode(), BNode()
                    shapes.add((absent, SH["not"], typed))
                    shapes.add((typed, SH.property, has_type))
                    shapes.add((has_type, SH.path, RDF.type))
                    shapes.add((has_type, SH.minCount, Literal(1)))
                    choices.append(absent)
                for rdf_class in value.target_classes:
                    choice = BNode()
                    shapes.add((choice, SH["class"], URIRef(rdf_class)))
                    choices.append(choice)
                _list(shapes, rule, SH["or"], choices)
            if field.policy.allowed_values:
                terms: list[Node] = []
                for allowed in field.policy.allowed_values:
                    terms.append(
                        URIRef(allowed.iri)
                        if isinstance(allowed, IRIDefault)
                        else Literal(
                            allowed.value,
                            lang=allowed.language,
                            datatype=URIRef(allowed.datatype) if allowed.datatype else None,
                            normalize=False,
                        )
                    )
                _list(shapes, rule, SH["in"], terms)

            if set(shapes.predicates(rule, None)) <= {RDF.type, SH.path}:
                shapes.remove((owner, SH.property, rule))
                shapes.remove((rule, None, None))
        if not list(shapes.objects(owner, SH.property)):
            shapes.remove((owner, None, None))
