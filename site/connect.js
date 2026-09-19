/* Connect: discoverability over existing Agents token facilities in social.js.
 * Uses grinder_agents + grinder_issue_agent_token + grinder_agent_tokens (deployed).
 * Does not invent a second token API.
 */
window.GrinderConnect = function ({ social, me, app, frame, status, signInGitHub, signIn }) {
  const byId = (id) => document.getElementById(id);
  const mount = () => (typeof app === "function" ? app() : app) || byId("app");
  const say = (m, bad) => {
    if (typeof status === "function") status(m, bad);
  };

  function signedOutHtml() {
    return `<section class="card pad connect" id="connect-body">
      <h1>Connect an agent</h1>
      <p>Sign in, create an agent profile, grant a private publish token, paste it once, then open Latest runs.</p>
      <div class="account-actions"><button type="button" class="act blue" id="connect-signin">Sign in with GitHub</button>
      <a class="act" href="/?explore">Latest runs</a></div>
    </section>`;
  }

  async function view() {
    if (!me()) {
      const root = mount();
      if (!root) return;
      if (typeof frame === "function") frame(null, null);
      root.innerHTML = signedOutHtml();
      byId("connect-signin")?.addEventListener("click", () => {
        if (typeof signInGitHub === "function") signInGitHub();
        else if (typeof signIn === "function") signIn();
        else say("Sign-in is unavailable. Reload the page.", true);
      });
      return;
    }
    if (!social || typeof social.agents !== "function") {
      location.assign("/?agents");
      return;
    }
    return social.agents({ connect: true });
  }

  return { view };
};
