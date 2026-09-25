// Free Lunch confirm: STRIVE signs a finished action for a visitor Free Lunch sent. Off, with no
// request made, unless FAIR_PRODUCT_SECRET_STRIVE and FAIR_URL are set. server/fair-confirm.mjs.
module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','no-store');res.setHeader('X-Content-Type-Options','nosniff');
 try{
  const {confirm}=await import('../../server/fair-confirm.mjs');
  const {runtimeConfig}=await import('../../server/runtime-config.mjs');
  let body;try{body=req.body}catch{body=undefined}
  const out=await confirm({method:req.method,headers:req.headers,body},runtimeConfig());
  for(const [k,v] of Object.entries(out.headers||{})) res.setHeader(k,v);
  res.status(out.status).json(out.body);
 }catch(_){res.status(503).json({error:'STRIVE is unavailable.'});}
};
