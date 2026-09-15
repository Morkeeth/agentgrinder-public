module.exports=async function handler(req,res) {
 res.setHeader('Cache-Control','no-store');
 try {
  const {runtimeConfig}=await import('../server/runtime-config.mjs');
  const config=runtimeConfig();
  const response=await fetch(config.SB_URL+'/rest/v1/profiles?select=id&limit=0',{headers:{apikey:config.SB_KEY,'Accept-Profile':'strava'},signal:AbortSignal.timeout(5000),cache:'no-store'});
  res.status(response.ok?200:503).json({service:'pacecard',database:response.ok?'ready':'unavailable'});
 }catch {res.status(503).json({service:'pacecard',database:'unavailable'});}
}
