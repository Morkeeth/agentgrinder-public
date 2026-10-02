"""The privacy page may not promise a channel that does not exist.

`site/privacy.html` said "You may also email the address below" under the deletion right. There
was no address below, and `grep -rio "mailto:" site/` returned nothing anywhere in the site. For a
product that stores personal data in an EU-region Postgres and offers a deletion right, the data
request channel was a sentence pointing at a sentence that did not exist.
"""
import glob
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRIVACY = open(os.path.join(REPO, "site", "privacy.html"), encoding="utf-8").read()


def test_the_page_does_not_promise_an_email_it_does_not_carry():
    promised = re.search(r"email the address", PRIVACY, re.I)
    if promised:
        assert "mailto:" in PRIVACY, "an address is promised and none is on the page"


def test_the_data_request_channel_is_a_real_reachable_url():
    m = re.search(r'href="(https://github\.com/[^"]+/issues)"', PRIVACY)
    assert m, "the privacy page names no contact channel"
    assert "Morkeeth/strive/issues" in m.group(1)


def test_no_page_on_the_site_promises_a_mailto_that_is_not_there():
    for f in glob.glob(os.path.join(REPO, "site", "*.html")):
        html = open(f, encoding="utf-8").read()
        if re.search(r"email (the|us at) ", html, re.I):
            assert "mailto:" in html, os.path.basename(f)
