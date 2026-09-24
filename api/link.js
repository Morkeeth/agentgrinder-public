// /l/<id> (the unlisted drop-in card), its share image, its delete page, and the create and
// delete calls behind "Get a link". server/dropin-link.mjs holds the rules.
module.exports=async function handler(req,res){
 res.setHeader('X-Content-Type-Options','nosniff');
 res.setHeader('Cache-Control','private, no-store, max-age=0');
 res.setHeader('X-Robots-Tag','noindex, nofollow');
 try{
  const L=await import('../server/dropin-link.mjs');
  const {runtimeConfig}=await import('../server/runtime-config.mjs');
  const config=runtimeConfig();
  const json=out=>{for(const [k,v] of Object.entries(out.headers||{}))res.setHeader(k,v);res.status(out.status).json(out.body)};
  let body;try{body=req.body}catch{body=undefined}
  if(req.method==='POST'&&req.query.action==='delete') return json(await L.deleteLink({method:req.method,body},config));
  if(req.method==='POST') return json(await L.createLink({method:req.method,headers:req.headers,body},config));
  if(req.method!=='GET'&&req.method!=='HEAD'){res.setHeader('Allow','GET, POST');return res.status(405).json({error:'Use GET or POST.'});}
  const id=req.query.id;
  if(req.query.view==='delete'){res.setHeader('Content-Type','text/html; charset=utf-8');return res.status(200).end(L.deleteHtml(id));}
  const link=await L.readLink(id,config);
  if(req.query.image==='1'){
   const {ImageResponse}=await import('@vercel/og');const {card,privateCard}=await import('../server/public-run.mjs');
   const image=new ImageResponse(link?card(L.linkRow(link)):privateCard(),{width:1200,height:630});
   res.setHeader('Content-Type','image/png');return res.status(200).end(Buffer.from(await image.arrayBuffer()));
  }
  res.setHeader('Content-Type','text/html; charset=utf-8');
  if(!link) return res.status(404).end(L.missingHtml());
  res.status(200).end(L.linkHtml(link,{origin:config.ORIGIN}));
 }catch(_){res.status(503).setHeader('Content-Type','text/plain; charset=utf-8');res.end('This link is temporarily unavailable.');}
};
