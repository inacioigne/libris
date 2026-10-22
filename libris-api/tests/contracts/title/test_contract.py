import json
import pytest
from pathlib import Path
from rdflib import Graph, URIRef
from pydantic import ValidationError
from app.catalog.shared.title.models import (
    WorkTitleRecord,
    InstanceTitleRecord
)
from app.catalog.shared.title.rdf import (
    to_graph,
    to_jsonld,
    from_graph,
    from_jsonld,
    ContractError,
)

BASE = Path(__file__).resolve().parent

EXAMPLES = BASE / "fixtures" / "examples"

SHAPES = (
    Path(__file__).resolve().parents[3]
    / "app/catalog/shared/title/shapes"
)

@pytest.mark.parametrize('filename,cls,kind', [('work.json',WorkTitleRecord,'work'),('instance.json',InstanceTitleRecord,'instance')])
def test_roundtrip(filename,cls,kind):
    record = cls.model_validate_json(
        (EXAMPLES / filename).read_text(encoding="utf-8")
    )
    result=from_graph(to_graph(record),record.id,kind)
    assert result==record
    assert from_jsonld(to_jsonld(record),record.id,kind)==record
    assert Graph().parse(data=json.dumps(to_jsonld(record)),format='json-ld').isomorphic(to_graph(record))

def test_blank_title():
    with pytest.raises(ValidationError):
        WorkTitleRecord.model_validate({'id':'https://example.org/w','titles':{'title':{'main_title':'  '}}})

def test_duplicate_title():
    with pytest.raises(ValidationError):
        WorkTitleRecord.model_validate({'id':'https://example.org/w','titles':{'title':{'main_title':'A'},'variant_titles':[{'main_title':'a'}]}})

def test_unknown_field():
    with pytest.raises(ValidationError):
        WorkTitleRecord.model_validate({'id':'https://example.org/w','titles':{'title':{'main_title':'A','unknown':1}}})

def test_lossy_import_rejected():
    record=WorkTitleRecord.model_validate({'id':'https://example.org/w','titles':{'title':{'main_title':'A'}}})
    g=to_graph(record)
    g.add((URIRef(record.id),URIRef('https://example.org/extra'),URIRef('https://example.org/value')))
    with pytest.raises(ContractError): from_graph(g,record.id,'work')

def test_shacl_if_installed():
    pytest.importorskip('pyshacl')
    from pyshacl import validate
    for name,cls in [('work.json',WorkTitleRecord),('instance.json',InstanceTitleRecord)]:
        record = cls.model_validate_json(
            (EXAMPLES / name).read_text(encoding="utf-8")
        )
        graph=to_graph(record)
        if record.kind=='instance':
            from rdflib.namespace import RDF
            from app.catalog.shared.title.rdf import BF
            graph.add((URIRef(record.work_id),RDF.type,BF.Work))
        conforms, _, report = validate(
            graph,
            shacl_graph=str(SHAPES / "title-v1.ttl"),
            use_shapes=[
                f"https://example.org/libris/shapes/"
                f"{record.kind.capitalize()}TitleShape"
            ],
        )
        assert conforms,report
