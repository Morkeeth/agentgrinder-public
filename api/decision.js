module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','private, no-store, max-age=0');
 res.setHeader('X-Content-Type-Options','nosniff');
 try{
  const {readPublic,validId}=await import('../server/public-run.mjs');
  const {decisionHtml,neutralDecisionHtml,hasDecisionStory}=await import('../server/decision-story.mjs');
  const id=req.query.id;
  if(!validId(id)){
   res.statusCode=404;
   res.setHeader('Content-Type','text/plain; charset=utf-8');
   res.end('This decision story is unavailable.');
   return;
  }
  const run=await readPublic(id);
  // A public run with no Code Route has no decision to tell, but it is still a real public story.
  if(run&&!hasDecisionStory(run)){res.statusCode=302;res.setHeader('Location','/r/'+encodeURIComponent(id));res.end();return;}
  res.statusCode=200;
  res.setHeader('Content-Type','text/html; charset=utf-8');
  res.end(run?decisionHtml(run):neutralDecisionHtml(id));
 }catch(_){
  res.statusCode=503;
  res.setHeader('Content-Type','text/plain; charset=utf-8');
  res.end('Decision story temporarily unavailable.');
 }
};
