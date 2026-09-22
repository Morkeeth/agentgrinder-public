# STRIVE analytics

## Hosted check (22 Sep 2026)

`https://agentic-strava.vercel.app/_vercel/insights/script.js` returned HTTP 404.
Web Analytics is off on the Vercel project, so pageviews and custom events do not land.

## What this change does

`site/index.html` loads the Vercel Insights script and queues `window.va` calls.
Oscar enables Web Analytics on the Production project, then redeploys. After that the script returns 200 and rule-3 outside numbers can be read from the dashboard.

## Outside number (profiles that are not Oscar)

Still read from the product DB, not from Analytics. Analytics is for page and share traffic after the script is live.
