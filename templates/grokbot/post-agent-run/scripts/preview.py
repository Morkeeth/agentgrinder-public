"""Prepare a private Grok run preview; no network requests or social writes."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from agentgrinder.native_sittings import read_sitting
from agentgrinder.push import export_run, import_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    parser.add_argument('--base-url', default='http://localhost:8000')
    args = parser.parse_args()
    url = urlsplit(args.base_url)
    local = url.hostname in ('localhost', '127.0.0.1', '::1')
    if (url.scheme != 'https' and not (local and url.scheme == 'http')) or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ('', '/'):
        parser.error('Use an HTTPS product origin, or HTTP localhost.')
    if url.hostname == 'agentgrinder.vercel.app':
        parser.error('Use the independent public-product origin, not the hackathon service.')
    try:
        run = read_sitting(str(args.export), 'grokbot')
        print(json.dumps({'status': 'private preview; not posted', 'metrics': export_run(run),
                          'preview_url': import_url(run, args.base_url)}, indent=2))
    except (OSError, ValueError):
        parser.exit(1, 'Could not read a supported Grok Bot sitting. Check the selected export.\n')


if __name__ == '__main__':
    main()
