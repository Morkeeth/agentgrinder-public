import json
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import pytest
from agentgrinder.agent_api import AgentClient,run_payload


def test_private_source_and_coach_prose_are_not_sent():
    payload=run_payload({'turns_typed':3,'source_path':'/private/transcript','coach_verdict':'private text','title':'Chosen title'})
    assert payload['visibility']=='private'
    assert 'private text' not in str(payload) and '/private' not in str(payload)


def test_network_client_sends_one_scoped_request_and_returns_no_credential():
    seen=[]
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            assert self.headers['Content-Profile'] == 'strava'
            seen.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(b'{"id":"00000000-0000-0000-0000-000000000099","action":"draft","debug_token":"fixture-token"}')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        client=AgentClient('fixture-token',f'http://127.0.0.1:{server.server_port}')
        rid='00000000-0000-0000-0000-000000000001'
        result=client.perform('draft',run_payload({'turns_typed':2}),rid)
        assert len(seen)==1 and seen[0]['request_id']==rid and seen[0]['token']=='fixture-token'
        assert 'fixture-token' not in json.dumps(result)
    finally:server.shutdown();server.server_close();thread.join()


def test_credentials_never_travel_over_remote_plain_http():
    with pytest.raises(ValueError):AgentClient('fixture-token','http://example.com')


def test_parser_derived_title_is_not_automatically_uploaded():
    payload=run_payload({'turns_typed':2,'harness':'Cursor','title':'PRIVATE_TYPED_PROMPT','note':'PRIVATE_NOTE'})
    assert 'PRIVATE_TYPED_PROMPT' not in str(payload)
    assert 'PRIVATE_NOTE' not in str(payload)


def test_separately_chosen_public_title_can_be_shared():
    assert run_payload({'turns_typed':2,'title':'private'},title='Chosen public title')['title']=='Chosen public title'


def _serve(body):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
            self.wfile.write(json.dumps(body).encode())
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server


def test_publish_reports_the_stored_audience_not_the_requested_one():
    rid='00000000-0000-0000-0000-000000000001'
    server=_serve({'id':'00000000-0000-0000-0000-000000000099','action':'publish','existing':True,'visibility':'private'})
    try:
        result=AgentClient('fixture-token',f'http://127.0.0.1:{server.server_port}').perform('publish',run_payload({'turns_typed':2},'public'),rid)
        assert result['existing'] is True and result['visibility']=='private'
    finally:server.shutdown();server.server_close()


def test_publish_without_a_stored_audience_is_an_error():
    server=_serve({'id':'00000000-0000-0000-0000-000000000099','action':'publish'})
    try:
        with pytest.raises(RuntimeError,match='no stored audience'):
            AgentClient('fixture-token',f'http://127.0.0.1:{server.server_port}').perform('publish',run_payload({'turns_typed':2}))
    finally:server.shutdown();server.server_close()


def test_ridge_fields_travel_to_publish():
    ridge=[1]*50
    payload=run_payload({'turns_typed':2,'ridge':ridge,'worker_bins':[0]*50,'commit_bins':[3],'ridge_basis':'turn-order'})
    assert payload['ridge']==ridge and payload['ridge_basis']=='turn-order' and payload['commit_bins']==[3]
