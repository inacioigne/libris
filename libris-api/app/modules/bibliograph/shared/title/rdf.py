from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import RDF, RDFS
from .models import WorkTitleRecord, InstanceTitleRecord, Title, VariantTitle, ParallelTitle, TitleSet

BF = Namespace('http://id.loc.gov/ontologies/bibframe/')
CONTEXT = {'bf':str(BF),'rdfs':str(RDFS)}

class ContractError(ValueError):
    pass

def _literal(text, language):
    return Literal(text, lang=language) if language else Literal(text)

def to_graph(record):
    g = Graph()
    g.bind('bf', BF)
    g.bind('rdfs', RDFS)
    subject = URIRef(record.id)
    g.add((subject,RDF.type,BF.Work if record.kind == 'work' else BF.Instance))
    if record.kind == 'instance':
        g.add((subject,BF.instanceOf,URIRef(record.work_id)))
    for title,cls in [(record.titles.title,BF.Title), *[(t,BF.VariantTitle) for t in record.titles.variant_titles], *[(t,BF.ParallelTitle) for t in record.titles.parallel_titles]]:
        node = BNode()
        g.add((subject,BF.title,node))
        g.add((node,RDF.type,cls))
        for field,predicate in [('main_title',BF.mainTitle),('subtitle',BF.subTitle),('part_number',BF.partNumber),('part_name',BF.partName)]:
            value = getattr(title,field)
            if value is not None:
                g.add((node,predicate,_literal(value,title.language)))
        label = ' '.join(filter(None,[title.main_title,(': '+title.subtitle) if title.subtitle else None,title.part_number,title.part_name])).replace(' : ',': ')
        g.add((node,RDFS.label,_literal(label,title.language)))
    return g

def to_jsonld(record):
    import json
    return json.loads(to_graph(record).serialize(format='json-ld', context=CONTEXT, auto_compact=True))

def from_graph(graph, resource_id, kind):
    subject = URIRef(resource_id)
    expected = BF.Work if kind == 'work' else BF.Instance
    if (subject,RDF.type,expected) not in graph:
        raise ContractError('missing expected resource type')
    allowed_subject = {RDF.type,BF.title} | ({BF.instanceOf} if kind == 'instance' else set())
    if any(p not in allowed_subject for p in graph.predicates(subject,None)):
        raise ContractError('unsupported resource predicates: lossless import unavailable')
    titles = {'main':[],'variant':[],'parallel':[]}
    for node in graph.objects(subject,BF.title):
        types = set(graph.objects(node,RDF.type))
        if len(types) != 1 or not types <= {BF.Title,BF.VariantTitle,BF.ParallelTitle}:
            raise ContractError('unsupported title type')
        allowed_node = {RDF.type,RDFS.label,BF.mainTitle,BF.subTitle,BF.partNumber,BF.partName}
        if any(p not in allowed_node for p in graph.predicates(node,None)):
            raise ContractError('unsupported title predicates: lossless import unavailable')
        vals = {}
        languages = set()
        for field,pred in [('main_title',BF.mainTitle),('subtitle',BF.subTitle),('part_number',BF.partNumber),('part_name',BF.partName)]:
            objects = list(graph.objects(node,pred))
            if len(objects)>1 or (field=='main_title' and len(objects)!=1) or any(not isinstance(x,Literal) for x in objects):
                raise ContractError('invalid title cardinality or literal')
            if objects:
                vals[field]=str(objects[0])
                if objects[0].language: languages.add(objects[0].language)
        if len(languages)>1: raise ContractError('mixed language tags')
        vals['language']=next(iter(languages),None)
        for pred in (BF.mainTitle,BF.subTitle,BF.partNumber,BF.partName,RDFS.label):
            for obj in graph.objects(node,pred):
                if not isinstance(obj,Literal) or obj.language != vals['language']:
                    raise ContractError('inconsistent language tags')
        cls = next(iter(types))
        key = {BF.Title:'main',BF.VariantTitle:'variant',BF.ParallelTitle:'parallel'}[cls]
        titles[key].append(({ 'main':Title,'variant':VariantTitle,'parallel':ParallelTitle}[key])(**vals))
    if len(titles['main']) != 1:
        raise ContractError('exactly one main title required')
    payload={'id':resource_id,'titles':TitleSet(title=titles['main'][0],variant_titles=titles['variant'],parallel_titles=titles['parallel'])}
    if kind=='instance':
        works=list(graph.objects(subject,BF.instanceOf))
        if len(works)!=1 or not isinstance(works[0],URIRef): raise ContractError('exactly one work link required')
        return InstanceTitleRecord(**payload,work_id=str(works[0]))
    return WorkTitleRecord(**payload)

def from_jsonld(data, resource_id, kind):
    g=Graph().parse(data=__import__('json').dumps(data),format='json-ld')
    return from_graph(g,resource_id,kind)
