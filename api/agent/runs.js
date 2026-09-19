module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
 try{
  const {upload}=await import('../../server/agent-upload.mjs');
  const {runtimeConfig}=await import('../../server/runtime-config.mjs');
  let body;try{body=req.body}catch{body=undefined} // invalid JSON reads as no object
  const out=await upload({method:req.method,headers:req.headers,body},runtimeConfig());
  for(const [k,v] of Object.entries(out.headers||{})) res.setHeader(k,v);
  res.status(out.status).json(out.body);
 }catch(_){res.status(503).json({error:'STRIVE is unavailable.'});}
};
