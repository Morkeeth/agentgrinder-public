module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','private, no-store, max-age=0');
 res.setHeader('Vary','Authorization');
 res.setHeader('X-Content-Type-Options','nosniff');
 try {
  const {runPhotos}=await import('../server/run-photos.mjs');
  const {runtimeConfig}=await import('../server/runtime-config.mjs');
  const out=await runPhotos({method:req.method,headers:req.headers,query:req.query,body:req.body},
   {...runtimeConfig(),STORAGE_KEY:process.env.STRIVE_STORAGE_SERVICE_ROLE_KEY});
  for(const [key,value] of Object.entries(out.headers)) res.setHeader(key,value);
  if(Buffer.isBuffer(out.body)) res.status(out.status).send(out.body);
  else res.status(out.status).json(out.body);
 } catch {res.status(503).json({error:'Photos are unavailable. Try again.'});}
};
