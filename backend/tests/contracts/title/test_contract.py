import json
import pytest
from pathlib import Path
from rdflib import Graph, URIRef
from pydantic import ValidationError
from libris_title import WorkTitleRecord,InstanceTitleRecord,to_graph,to_jsonld,from_graph,from_jsonld,ContractError

BASE=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('filename,cls,kind', [('work.json',WorkTitleRecord,'work'),('instance.json',InstanceTitleRecord,'instance')])
def test_roundtrip(filename,cls,kind):
    record=cls.model_validate_json((BASE/'examples'/filename).read_text())
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
        record=cls.model_validate_json((BASE/'examples'/name).read_text())
        graph=to_graph(record)
        if record.kind=='instance':
            from rdflib.namespace import RDF
            from libris_title.rdf import BF
            graph.add((URIRef(record.work_id),RDF.type,BF.Work))
        conforms,_,report=validate(graph,shacl_graph=str(BASE/'shapes/title-v1.ttl'))
        assert conforms,report
