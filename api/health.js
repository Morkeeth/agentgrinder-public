module.exports=async function handler(req,res) {
 res.setHeader('Cache-Control','no-store');
 const {SERVICE}=await import('../server/brand.mjs');
 const {deploymentGitSha}=await import('../server/deployment-identity.mjs');
 const gitSha=deploymentGitSha();
 const identity=gitSha?{git_sha:gitSha}:{};
 if(gitSha) res.setHeader('X-Strive-Git-Sha',gitSha);
 try {
  const {runtimeConfig}=await import('../server/runtime-config.mjs');
  const config=runtimeConfig();
  const response=await fetch(config.SB_URL+'/rest/v1/profiles?select=id&limit=0',{headers:{apikey:config.SB_KEY,'Accept-Profile':'strava'},signal:AbortSignal.timeout(5000),cache:'no-store'});
  res.status(response.ok?200:503).json({service:SERVICE,database:response.ok?'ready':'unavailable',...identity});
 }catch {res.status(503).json({service:SERVICE,database:'unavailable',...identity});}
}
