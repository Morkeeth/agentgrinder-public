"""Agent profile visibility stays separate from each run audience."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOCIAL = (ROOT / "site" / "social.js").read_text()
CONNECT = (ROOT / "site" / "connect.js").read_text()
INDEX = (ROOT / "site" / "index.html").read_text()
DATABASE = (ROOT / "scripts" / "test-database.mjs").read_text()


def test_agents_list_edits_visibility_after_create():
    assert "data-agent-visibility" in SOCIAL
    assert "Save visibility" in SOCIAL
    assert 'from("grinder_agents")' in SOCIAL
    assert "update({ visibility })" in SOCIAL
    assert "Run audiences stay unchanged" in SOCIAL
    assert SOCIAL.index("agentVisibilityForm") < SOCIAL.index("async function agents(")


def test_private_agent_does_not_intercept_owner_run_save():
    gate = SOCIAL[SOCIAL.index("async function attachAgentShareGate") : SOCIAL.index("async function thread(")]
    run_id = "11111111-1111-4111-8111-111111111111"
    actor_id = "22222222-2222-4222-8222-222222222222"
    script = f"""
      let inserted = null;
      let saved = 0;
      let updates = 0;
      const save = {{ dataset: {{}}, onclick: () => {{ saved += 1; }} }};
      const edit = {{
        dataset: {{}},
        querySelector: () => ({{ nextSibling: {{}} }}),
        insertBefore: (notice) => {{ inserted = notice; }},
        prepend: (notice) => {{ inserted = notice; }},
      }};
      const elements = {{ "run-save": save, "run-edit": edit }};
      const byId = (id) => elements[id] || null;
      const document = {{ createElement: () => ({{}}) }};
      const uuid = (value) => typeof value === "string" && value.length > 30;
      const me = () => ({{ id: "owner" }});
      const esc = (value) => String(value);
      const fail = (error) => {{ throw error; }};
      const rows = {{
        runs: [{{ id: {json.dumps(run_id)}, source_actor_id: {json.dumps(actor_id)}, profile_id: "owner" }}],
        grinder_agents: [{{ id: {json.dumps(actor_id)}, name: "Private runner", visibility: "private" }}],
      }};
      const db = {{
        from: (table) => ({{
          select() {{ return this; }},
          update() {{ updates += 1; return this; }},
          eq() {{ return this; }},
          limit() {{ return Promise.resolve({{ data: rows[table], error: null }}); }},
        }}),
      }};
      const result = async (query) => {{
        const response = await query;
        if (response.error) throw response.error;
        return response.data;
      }};
      {gate}
      (async () => {{
        const originalSave = save.onclick;
        await attachAgentShareGate({json.dumps(run_id)});
        await save.onclick();
        const output = {{
          saveHandlerPreserved: save.onclick === originalSave,
          saved,
          updates,
          notice: inserted ? inserted.innerHTML : "",
        }};
        process.stdout.write(JSON.stringify(output));
      }})().catch((error) => {{ console.error(error); process.exit(1); }});
    """
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(completed.stdout)
    assert observed["saveHandlerPreserved"] is True
    assert observed["saved"] == 1
    assert observed["updates"] == 0
    assert "You can still choose Followers, Close friends or Public" in observed["notice"]
    assert "does not publish the agent profile" in observed["notice"]


def test_connect_and_run_copy_keeps_profile_visibility_separate():
    assert "it does not change any run audience" in CONNECT
    assert "Run audiences stay unchanged" in SOCIAL
    for source in (SOCIAL, CONNECT):
        assert "needs the agent public first" not in source
        assert "run-agent-public-consent" not in source
    assert "Keep private" in DATABASE
    assert "Want public" in DATABASE
    assert "sibling Only-me runs stay private" in DATABASE


def test_private_run_still_offers_the_audience_control():
    assert 'href="#run-audience">Choose who can see this</a>' in INDEX
    assert "id=\"run-save\"" in INDEX or "id='run-save'" in INDEX
