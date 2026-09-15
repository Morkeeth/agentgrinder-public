#!/usr/bin/env bash
# Agent Grinder — 2-minute pitch demo script. Run from repo root.
set -euo pipefail
cd "$(dirname "$0")/.."

SAMPLE="samples/sample_run.json"
if python3 -c "from agentgrinder.flex import latest_any; raise SystemExit(0 if latest_any() else 1)" 2>/dev/null; then
  SAMPLE_MODE=0
else
  SAMPLE_MODE=1
  echo "(no local agent sessions — steps 2-5 use bundled sample)"
  echo ""
fi

echo ""
echo "=== AGENT GRINDER pitch demo ==="
echo ""

echo "1/6 flex — your agents on this machine"
python3 -m agentgrinder flex || true
echo ""

echo "2/6 vibe — meme label (no streaks)"
if [ "$SAMPLE_MODE" = 1 ]; then
  python3 -m agentgrinder vibe "$SAMPLE"
else
  python3 -m agentgrinder vibe
fi
echo ""

echo "3/6 roast — honest shape clowning"
if [ "$SAMPLE_MODE" = 1 ]; then
  python3 -m agentgrinder roast "$SAMPLE"
else
  python3 -m agentgrinder roast
fi
echo ""

echo "4/6 grind card — latest session"
if [ "$SAMPLE_MODE" = 1 ]; then
  python3 -m agentgrinder card "$SAMPLE" --no-open -o /tmp/pitch-grind.html
else
  python3 -m agentgrinder grind --harness auto --no-rank --no-open -o /tmp/pitch-grind.html
fi
echo "   -> /tmp/pitch-grind.html"
echo ""

echo "5/6 share card — claim-your-handle + vibe + roast"
if [ "$SAMPLE_MODE" = 1 ]; then
  python3 -m agentgrinder share "$SAMPLE" --vibe --roast --no-open -o /tmp/pitch-share.html
else
  python3 -m agentgrinder share --harness auto --vibe --roast --no-open -o /tmp/pitch-share.html
fi
echo "   -> /tmp/pitch-share.html"
echo ""

echo "6/6 rig card — stack for friends"
python3 -m agentgrinder rig --share-names --no-open -o /tmp/pitch-rig.html
echo "   -> /tmp/pitch-rig.html"
echo ""

echo "Optional: heist card (rig ACK)"
echo "  python3 -m agentgrinder heist oscar --thief friend -o /tmp/pitch-heist.html"
echo ""
echo "Web path: open site → /?onboard → grind --push → /?explore"
echo "Pitch doc: archive/hackathon-2026-09/docs/PITCH-2026-09-01.md"
echo ""
