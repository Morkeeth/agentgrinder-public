module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','private, no-store, max-age=0');
 res.setHeader('X-Content-Type-Options','nosniff');
 try{
  const {readPublic,validId}=await import('../server/public-run.mjs');
  const {proofHtml,neutralProofHtml,proofFacts,routeNotRecordedHtml}=await import('../server/public-proof.mjs');
  const id=req.query.id;
  if(!validId(id)){
   res.statusCode=404;
   res.setHeader('Content-Type','text/plain; charset=utf-8');
   res.end('This public proof is unavailable.');
   return;
  }
  const run=await readPublic(id);
  res.statusCode=200;
  res.setHeader('Content-Type','text/html; charset=utf-8');
  res.end(!run?neutralProofHtml(id):proofFacts(run.code_route)?proofHtml(run):routeNotRecordedHtml(run));
 }catch(_){
  res.statusCode=503;
  res.setHeader('Content-Type','text/plain; charset=utf-8');
  res.end('Public proof temporarily unavailable.');
 }
};
