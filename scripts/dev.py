"""Small, cross-platform contributor commands. Run from any working directory."""
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / '.venv'
PYTHON = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def run(args, **kwargs):
    subprocess.run([str(a) for a in args], cwd=ROOT, check=True, **kwargs)


def setup():
    if not PYTHON.exists():
        run([sys.executable, '-m', 'venv', VENV])
    run([PYTHON, '-m', 'pip', 'install', '-e', '.[dev]'])
    print('Ready. Run: python3 scripts/dev.py serve', flush=True)


def check():
    if not PYTHON.exists():
        raise SystemExit('Run python3 scripts/dev.py setup first.')
    run([PYTHON, '-m', 'pytest', 'tests/test_agent_mcp.py', 'tests/test_cursor_headline.py', '-q'])
    messages = [
        {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'contributor-check', 'version': '1'}}},
        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
        {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'a2a_onboard', 'arguments': {}}},
    ]
    env = os.environ.copy()
    env['AGENTGRINDER_AGENT_TOKEN'] = ''
    result = subprocess.run([str(PYTHON), str(ROOT / 'scripts/cursor-mcp.py')],
        input='\n'.join(json.dumps(m) for m in messages) + '\n', text=True,
        capture_output=True, cwd=tempfile.gettempdir(), env=env, check=True)
    replies = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(replies) == 3 and 'protocolVersion' in replies[0]['result']
    names = {tool['name'] for tool in replies[1]['result']['tools']}
    assert 'preview_run' in names and 'agent_action' not in names
    assert not replies[2]['result'].get('isError')
    print('MCP launch and onboarding passed; no sessions read.', flush=True)
    node = shutil.which('node')
    if not node:
        raise SystemExit('JavaScript checks NOT RUN: install Node 20+ and run check again.')
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', (ROOT / 'site/index.html').read_text(), re.S)
    with tempfile.TemporaryDirectory(prefix='agentic-strava-check-') as folder:
        for index, source in enumerate(scripts):
            if source.strip():
                path = Path(folder) / f'inline-{index}.js'
                path.write_text(source)
                run([node, '--check', path])
    for path in sorted((ROOT / 'site').glob('*.js')):
        run([node, '--check', path])
    run([sys.executable, ROOT / 'scripts/cold-first-minute.py'])
    # Connect's device pairing lives in SQL and in the approve page, so its checks need the dev
    # dependencies (an in-process Postgres, jsdom, a reference QR encoder). Say so when they are
    # not installed rather than reporting a pass that never ran.
    if (ROOT / 'node_modules/@electric-sql/pglite').exists():
        run([node, '--test', ROOT / 'scripts/test-connect-device.mjs'])
        run([node, '--test', ROOT / 'scripts/test-connect-pair.mjs'])
    else:
        print('Connect device pairing checks NOT RUN: run npm install, then npm run test:connect and npm run test:pair.', flush=True)
    print('Contributor checks passed. These do not test hosted sign-in or social writes.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['setup', 'serve', 'check'])
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    if args.command == 'setup':
        setup()
    elif args.command == 'check':
        check()
    else:
        print(f'Local UI: http://127.0.0.1:{args.port}/ | No hosted database configured.', flush=True)
        run([sys.executable, '-m', 'http.server', str(args.port), '--bind', '127.0.0.1', '--directory', ROOT / 'site'])


if __name__ == '__main__':
    main()
