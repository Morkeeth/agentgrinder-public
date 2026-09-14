"""Explicit, scoped agent actions. Credentials are read once and never returned to a model."""
from __future__ import annotations
import json
import os
import uuid
import urllib.error
import urllib.parse
import urllib.request

from .a2a_client import DEFAULT_URL, DEFAULT_KEY, DEFAULT_SCHEMA
from .contract import validate_run
from .push import export_run

RUN_FIELDS = {"title","project","harness","turns_typed","duration_s","tool_calls","files_touched",
              "commits","claims","claims_verified","artifacts_produced","started","visibility",
              "rhythm","route","schema_version","measurement_revision","baseline_revision","note","trace_basis"}


def run_payload(run: dict, visibility: str = "private", *, title: str | None = None, note: str | None = None) -> dict:
    validate_run(run)
    if visibility not in ("private","public"):
        raise ValueError("Agent publishing supports private or explicitly authorised public grinds.")
    exported=export_run(run)
    payload={k:v for k,v in exported.items() if k in RUN_FIELDS}
    # A parser title can be the first typed prompt. Only separately chosen public text travels.
    for field,value,limit in (("title",title,200),("note",note,4000)):
        if value is not None:
            if not isinstance(value,str) or len(value)>limit:raise ValueError("Public text is invalid or too long.")
            payload[field]=value
    payload["visibility"]=visibility
    return payload


class AgentClient:
    def __init__(self,token: str | None = None,base_url: str = DEFAULT_URL,api_key: str = DEFAULT_KEY):
        self._token=token if token is not None else os.environ.get("AGENTGRINDER_AGENT_TOKEN")
        if not self._token:raise ValueError("Set AGENTGRINDER_AGENT_TOKEN to a credential granted by the agent's owner.")
        parsed=urllib.parse.urlsplit(base_url)
        local=parsed.hostname in ("localhost","127.0.0.1","::1")
        if (parsed.scheme!="https" and not (local and parsed.scheme=="http")) or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Agent credentials require HTTPS (HTTP is allowed only on localhost).")
        self._url=base_url.rstrip('/')+'/rest/v1/rpc/grinder_agent_action'
        self._key=api_key

    def questions(self) -> list:
        request=urllib.request.Request(self._url.replace('grinder_agent_action','grinder_agent_questions'),
            data=json.dumps({'token':self._token}).encode(),method='POST',
            headers={'Content-Type':'application/json','apikey':self._key,'Content-Profile':DEFAULT_SCHEMA})
        try:
            with urllib.request.urlopen(request,timeout=30) as response: result=json.load(response)
        except (urllib.error.URLError,ValueError):
            raise RuntimeError('Agent questions unavailable. Check public reply scope and expiry.') from None
        if not isinstance(result,list): raise RuntimeError('Agent endpoint returned an invalid question list.')
        return result

    def perform(self,action: str,payload: dict,request_id: str | None = None) -> dict:
        if action not in ("draft","publish","reply","ack"):raise ValueError("Unsupported agent action.")
        rid=str(uuid.UUID(request_id)) if request_id else str(uuid.uuid4())
        raw=json.dumps(dict(token=self._token,action=action,payload=payload,request_id=rid)).encode()
        request=urllib.request.Request(self._url,data=raw,method='POST',headers={
            'Content-Type':'application/json','apikey':self._key,'Content-Profile':DEFAULT_SCHEMA})
        try:
            with urllib.request.urlopen(request,timeout=30) as response:
                result=json.load(response)
        except urllib.error.HTTPError as error:
            # Do not echo a response body that may contain supplied credentials or private text.
            raise RuntimeError(f"Agent action rejected (HTTP {error.code}); request {rid}. Check the granted scope and expiry.") from None
        except urllib.error.URLError:
            raise RuntimeError(f"Agent endpoint unavailable; reuse request {rid} with the same payload when retrying.") from None
        if not isinstance(result,dict) or 'id' not in result:
            raise RuntimeError(f"Agent endpoint returned an invalid response; request {rid}.")
        try:
            result_id=str(uuid.UUID(result['id']))
            actor_id=str(uuid.UUID(result['agent_id'])) if result.get('agent_id') else None
        except (ValueError,TypeError,KeyError):
            raise RuntimeError(f'Agent endpoint returned an invalid identity; request {rid}.') from None
        if result.get('action')!=action:raise RuntimeError(f'Agent endpoint returned a mismatched action; request {rid}.')
        safe=dict(id=result_id,action=action,request_id=rid)
        if actor_id:safe['agent_id']=actor_id
        return safe


def add_parser(subparsers):
    parser=subparsers.add_parser('agent',help='use a human-granted agent credential for explicit network actions')
    parser.add_argument('--url',default=DEFAULT_URL)
    parser.add_argument('--request-id',help='reuse the same ID and payload after an uncertain network response')
    actions=parser.add_subparsers(dest='agent_action',required=True)
    capture=actions.add_parser('capture',help='capture an explicit Claude SDK/sidechain transcript locally; no network')
    capture.add_argument('transcript')
    for name in ('draft','publish'):
        action=actions.add_parser(name);action.add_argument('run_json')
        action.add_argument('--visibility',choices=['private','public'],default='private')
        action.add_argument('--title',help='explicit public title; parser-derived titles are not uploaded')
        action.add_argument('--note',help='explicit caption to share')
    actions.add_parser('questions',help='read bounded public questions and their permitted evidence')
    reply=actions.add_parser('reply');reply.add_argument('run_id');reply.add_argument('body');reply.add_argument('--question-id')
    ack=actions.add_parser('ack');ack.add_argument('run_id');ack.add_argument('--reason',required=True,choices=['shipped','focus','pace','rig','comeback','handoff'])


def run_cli(args):
    from pathlib import Path
    try:
        if args.agent_action=='capture':
            from .automated_capture import capture
            print(json.dumps(capture(args.transcript),indent=2));return 0
        if args.agent_action=='questions':
            print(json.dumps(AgentClient(base_url=args.url).questions(),indent=2));return 0
        if args.agent_action in ('draft','publish'):
            payload=run_payload(json.loads(Path(args.run_json).read_text()),args.visibility,title=args.title,note=args.note)
        elif args.agent_action=='reply':
            payload=dict(run_id=str(uuid.UUID(args.run_id)),body=args.body)
            if args.question_id:payload['question_id']=str(uuid.UUID(args.question_id))
        else:payload=dict(run_id=str(uuid.UUID(args.run_id)),reason=args.reason)
        result=AgentClient(base_url=args.url).perform(args.agent_action,payload,args.request_id)
        print(json.dumps(result,indent=2));return 0
    except (ValueError,RuntimeError,OSError) as error:
        print(str(error));return 1
