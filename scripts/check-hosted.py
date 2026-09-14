"""Read-only PostgREST checks using the shipped public key and actual site queries."""
import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root/'site/index.html').read_text()
url = re.search(r'const SB_URL="([^"]+)"', html).group(1)
key = re.search(r'const SB_KEY="([^"]+)"', html).group(1)


def read(table, params, extra_headers=None):
    req = urllib.request.Request(url+'/rest/v1/'+table+'?'+urllib.parse.urlencode(params), headers={'apikey':key, 'Accept-Profile':'strava', **(extra_headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--private-run', help='an existing private test run that anonymous callers must not read')
parser.add_argument('--link-run', help='an existing link-only test run: hidden from collection reads, readable with its ID')
args = parser.parse_args()
queries = set()
for name in ('site/index.html', 'site/social.js'):
    source = (root/name).read_text()
    queries.update(re.findall(r"\.from\(['\"]runs['\"]\)\s*\.select\(['\"]([^'\"]+)['\"]\)", source))
assert queries, 'No real run queries discovered'
for query in sorted(queries):
    status, body = read('runs', {'select':query,'limit':'0'})
    assert status == 200, (query,status,body.get('code'),body.get('message'))
for table in ('grinder_notifications','grinder_agent_tokens','grinder_agent_requests','grinder_comparisons'):
    status, body = read(table, {'select':'*','limit':'0'})
    assert status in (401,403) and body.get('code')=='42501', (table,status,body)
status, body = read('profiles', {'select':'id','id':'in.(f2000000-0000-0000-0000-000000000001,f2000000-0000-0000-0000-000000000002)'})
assert status == 200 and body == [], 'Rollback test profiles remain or the check failed'
if args.private_run:
    status, body = read('runs', {'select':'id','id':'eq.'+args.private_run})
    assert status == 200 and body == [], 'Private run was exposed or the check failed'
if args.link_run:
    status, body = read('runs', {'select':'id','visibility':'eq.link'})
    assert status == 200 and body == [], 'Link-only collection was exposed or the check failed'
    status, body = read('runs', {'select':'id','id':'eq.'+args.link_run}, {'x-grinder-run-id':args.link_run})
    assert status == 200 and body == [{'id':args.link_run}], 'Known link was not readable'
print(f'Hosted checks passed: {len(queries)} actual run query shapes; anonymous access denied on private tables; rollback profiles absent; private run checked={bool(args.private_run)}')
