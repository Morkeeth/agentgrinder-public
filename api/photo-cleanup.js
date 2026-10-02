const {timingSafeEqual}=require('node:crypto');
module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','no-store');
 if(req.method!=='GET')return res.status(405).json({error:'Method not allowed'});
 const secret=process.env.CRON_SECRET;
 const actual=Buffer.from(req.headers.authorization||'');
 const expected=Buffer.from('Bearer '+(secret||''));
 if(!secret||actual.length!==expected.length||!timingSafeEqual(actual,expected))
  return res.status(401).json({error:'Unauthorized'});
 try{
  const {runtimeConfig}=await import('../server/runtime-config.mjs');
  const {cleanupPhotos}=await import('../scripts/cleanup-run-photos.mjs');
  const result=await cleanupPhotos({...runtimeConfig(),STORAGE_KEY:process.env.STRIVE_STORAGE_SERVICE_ROLE_KEY});
  return res.status(200).json(result);
 }catch{return res.status(503).json({error:'Photo cleanup incomplete; queued items retained.'});}
};
