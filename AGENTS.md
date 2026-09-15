# Agentic Strava public product

Read README.md and PRODUCT.md first. This repository is the free, social, Cursor-first product. The separate hackathon repository is out of scope.

Build the card → post → response → return path. Preserve the white card and blue trace. Missing metrics stay unknown. Never fabricate people, output, engagement or results.

Runtime defaults are local. App data uses only the dedicated `strava` schema and shared Auth. Keep every table, function and migration schema-qualified. Do not apply public-schema migrations or change project-wide Auth triggers.

Keep credentials and local sessions out of commits. Use small PRs with a working user path, and report local, tested, hosted and used separately. Do not send invites, messages or public posts without explicit approval.
