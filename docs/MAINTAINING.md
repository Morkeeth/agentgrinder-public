# Maintainer guidelines

These are the review guidelines for Agentic Strava. Repository maintainers make merge and release decisions; contributors can propose changes through issues and PRs. Do not imply a contributor has maintainer access or assign work without agreement.

## Triage

Acknowledge the user problem when reviewing an issue. Reproduce bugs where possible. Ask for the smallest missing detail, not a complete private transcript. Link duplicates and explain closures. For feature requests, check PRODUCT.md: does this improve capture, posting, cards, browsing or lightweight social interaction?

Keep proposals visible in issues. A larger product decision should result in an update to PRODUCT.md, not a new conflicting brief. Small fixes do not need a design process.

## Review a PR

Check the resulting user behaviour, not just test counts. Read the diff, inspect screenshots where relevant, and check for accidental scope expansion or private data. Require appropriate focused tests for behavioural changes. Documentation changes need accurate links and commands.

Automated contributor checks are a baseline, not a full product test. Ask for hosted access-rule checks when changing privacy or database behaviour. Distinguish fixture results from real users. Agent-written PRs receive the same review as human-written PRs.

Explain requested changes concretely. Merge focused improvements when the result is understood and checks relevant to the change pass. Close unsuitable PRs with a reason and, when useful, a smaller alternative.

## Releases

A merge is not a deployment. Record the revision, deployment, migrations and the user path actually checked. Use independent services for this public product; leave the hackathon release alone. Check the bytes being published for credentials or personal data. Do not publish test activity as a populated community.

## Community

Apply the conduct expectations in CONTRIBUTING.md consistently. Keep technical disagreement respectful. Remove harmful content when needed and avoid repeating private information in public moderation notes. Do not promise review or support response times that the project cannot sustain.
