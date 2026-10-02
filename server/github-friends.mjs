// Opt-in public-network discovery. Supabase tokens only go to Supabase.
export class DiscoveryError extends Error {
 constructor(status,code,message){super(message);this.status=status;this.code=code;}
}
export async function githubFriends({authorization,query={},config,fetcher=fetch}){
 if(Object.keys(query).length) throw new DiscoveryError(400,'unexpected_query','This request uses your own linked GitHub account.');
 if(!/^Bearer \S+$/.test(authorization||'')) throw new DiscoveryError(401,'sign_in_required','Sign in to find friends.');
 const request=async(url,options)=>fetcher(url,{...options,signal:AbortSignal.timeout(8000),cache:'no-store'});
 const authHeaders={apikey:config.SB_KEY,Authorization:authorization};
 const auth=await request(config.SB_URL+'/auth/v1/user',{headers:authHeaders});
 if(!auth.ok)throw new DiscoveryError(401,'sign_in_required','Sign in again to find friends.');
 const user=await auth.json();
 const identity=user.identities?.find(i=>i.provider==='github');
 const id=String(identity?.identity_data?.sub||'');
 const data=identity?.identity_data||{};
 const login=data.user_name||data.preferred_username||data.login;
 if(!/^[0-9]+$/.test(id)||!/^[-a-z0-9]{1,39}$/i.test(login||''))throw new DiscoveryError(409,'github_link_required','Connect your GitHub account first.');
 const ghHeaders={Accept:'application/vnd.github+json','User-Agent':'STRIVE-friend-discovery'};
 const github=async path=>{
  const r=await request('https://api.github.com'+path,{headers:ghHeaders});
  if(!r.ok)throw new DiscoveryError(r.status===403||r.status===429?429:502,'github_unavailable','GitHub could not load your connections. Please try again later.');
  return r.json();
 };
 const current=await github('/users/'+encodeURIComponent(login));
 if(String(current.id)!==id)throw new DiscoveryError(409,'github_identity_changed','Reconnect GitHub to confirm your current username.');
 if(current.private||current.user_view_type==='private')throw new DiscoveryError(409,'public_graph_unavailable','Your GitHub connections are private. Private-network import is not available yet.');
 const ids=[];let truncated=false;
 for(let page=1;page<=5;page++){
  const rows=await github('/users/'+encodeURIComponent(login)+'/following?per_page=100&page='+page);
  if(!Array.isArray(rows))throw new DiscoveryError(502,'github_unavailable','GitHub returned an unreadable connection list.');
  ids.push(...rows.filter(r=>Number.isSafeInteger(r.id)&&r.id>0).map(r=>String(r.id)));
  if(rows.length<100)break;
  if(page===5)truncated=true;
 }
 // No-match is distinct from a failed database read or a failed graph request.
 const r=await request(config.SB_URL+'/rest/v1/rpc/strava_github_matches',{
  method:'POST',headers:{...authHeaders,'Content-Type':'application/json','Content-Profile':'strava'},body:JSON.stringify({github_ids:ids})});
 if(!r.ok)throw new DiscoveryError(503,'matching_unavailable','Your STRIVE friends could not load. Please try again later.');
 const people=await r.json();
 if(!Array.isArray(people))throw new DiscoveryError(503,'matching_unavailable','Your STRIVE friends could not load.');
 return {people,scanned:ids.length,truncated,scope:'public_github_following'};
}
