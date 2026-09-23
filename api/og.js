// The home page's share image. /r/<id> has had one since it shipped; the address people
// actually post - the root - had none, so an X post of it was a bare link. Same pipeline,
// same size, no database read and nothing user-supplied in it.
module.exports=async function handler(req,res){
 res.setHeader('X-Content-Type-Options','nosniff');
 try{
  const {homeCard}=await import('../server/public-run.mjs');
  const {ImageResponse}=await import('@vercel/og');
  const image=new ImageResponse(homeCard(),{width:1200,height:630});
  res.statusCode=200;
  res.setHeader('Content-Type','image/png');
  // The card is the brand and the tagline: it changes when the site is deployed, not per reader.
  res.setHeader('Cache-Control','public, max-age=3600, s-maxage=86400');
  res.end(Buffer.from(await image.arrayBuffer()));
 }catch(_){res.statusCode=503;res.setHeader('Content-Type','text/plain; charset=utf-8');res.end('Share image temporarily unavailable.');}
};
