const GIT_SHA = /^[0-9a-f]{40}$/;

export function deploymentGitSha(env = process.env) {
 const value = env.VERCEL_GIT_COMMIT_SHA;
 return typeof value === 'string' && GIT_SHA.test(value) ? value : null;
}
