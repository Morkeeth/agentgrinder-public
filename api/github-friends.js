module.exports=async function handler(req,res){
 res.setHeader('Cache-Control','private, no-store');
 res.setHeader('Vary','Authorization');
 if(req.method!=='GET'){res.setHeader('Allow','GET');return res.status(405).json({error:'method_not_allowed'});}
 try{
  const {runtimeConfig}=await import('../server/runtime-config.mjs');
  const {githubFriends}=await import('../server/github-friends.mjs');
  return res.status(200).json(await githubFriends({authorization:req.headers.authorization,query:req.query||{},config:runtimeConfig()}));
 }catch(e){return res.status(e.status||503).json({error:e.code||'discovery_unavailable',message:e.status?e.message:'Friends could not load. Please try again later.'});}
};
