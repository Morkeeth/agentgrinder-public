import {runtimeConfig} from './runtime-config.mjs';
const config=runtimeConfig();
export const origin=config.ORIGIN;
export const validId=id=>typeof id==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function readPublic(id,fetcher=fetch){
 if(!validId(id))return null;
 const query=new URLSearchParams({id:'eq.'+id,visibility:'eq.public',select:'id,title,caption,output_url,project,harness,started_at,duration_s,prompts,artifacts_produced,commits,rhythm,trace_basis,profiles!runs_profile_id_fkey(github_handle,handle,display_name)',limit:'1'});
 const response=await fetcher(config.SB_URL+'/rest/v1/runs?'+query,{headers:{apikey:config.SB_KEY,"Accept-Profile":config.SB_SCHEMA},cache:'no-store',signal:AbortSignal.timeout(8000)});
 if(!response.ok)throw new Error('Public run unavailable');const rows=await response.json();
 return Array.isArray(rows)&&rows.length===1?rows[0]:null;
}
export function html(run){const title=esc(run.title||'Agent run'),description=esc(run.caption||'See the work, its recorded activity and the conversation.'),id=encodeURIComponent(run.id),image=origin+'/api/run?id='+id+'&image=1',url=origin+'/r/'+id;
 return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title} · Agentic Strava</title><meta property="og:type" content="article"><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${url}"><meta property="og:image" content="${image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="${image}"><link rel="canonical" href="${url}"><style>body{background:#f8f8f6;color:#111;font:18px system-ui;margin:0;padding:32px}main{max-width:900px;margin:40px auto}img{width:100%;height:auto;border:1px solid #ddd}a{color:#123cff}h1{font-size:clamp(28px,5vw,48px);line-height:1.1}a.open{display:inline-block;background:#123cff;color:white;text-decoration:none;padding:16px 24px;margin:24px 0}</style></head><body><main><a href="/">Agentic Strava</a><h1>${title}</h1><p>${description}</p><img src="${image.replaceAll('&','&amp;')}" alt="Recorded activity for ${title}" width="1200" height="630"><a class="open" href="/?run=${id}">Open run and discussion</a><p>Recorded counts describe activity. They do not independently verify the result.</p></main></body></html>`;
}
const el=(type,props,...children)=>({type,props:{...props,children:children.length===1?children[0]:children}});
export function card(run){const values=run.rhythm,valid=Array.isArray(values)&&values.length>1&&values.length<=10000&&values.every(v=>Number.isFinite(v)&&v>=0);const max=valid?Math.max(...values)||1:1;
 const points=valid?values.map((v,i)=>`${i/(values.length-1)*1080},${135-v/max*125}`).join(' '):'';
 const metrics=[['Typed turns',run.prompts],['Artifacts',run.artifacts_produced],['Commits',run.commits]];
 return el('div',{style:{width:'100%',height:'100%',background:'#f8f8f6',color:'#111',display:'flex',flexDirection:'column',padding:'46px 60px',fontFamily:'sans-serif'}},
 el('div',{style:{display:'flex',color:'#123cff',fontSize:24,fontWeight:700}},'AGENTIC STRAVA'),
 el('div',{style:{display:'flex',fontSize:46,fontWeight:700,marginTop:22,height:112,overflow:'hidden'}},String(run.title||'Agent run').slice(0,120)),
 el('div',{style:{display:'flex',color:'#666',fontSize:22}},[(run.profiles?.handle||run.profiles?.github_handle)?'@'+(run.profiles.handle||run.profiles.github_handle):null,run.harness].filter(Boolean).join(' · ')||'Public run'),
 run.caption?el('div',{style:{display:'flex',fontSize:22,marginTop:18,height:54,overflow:'hidden'}},String(run.caption).slice(0,280)):null,
 valid?el('svg',{width:1080,height:140,viewBox:'0 0 1080 140',style:{marginTop:20}},el('polyline',{points,stroke:'#123cff',strokeWidth:4,fill:'none'})):el('div',{style:{display:'flex',height:140,alignItems:'center',color:'#666'}},'Trace unavailable'),
 el('div',{style:{display:'flex',marginTop:22,gap:90}},...metrics.map(([label,value])=>el('div',{style:{display:'flex',flexDirection:'column',width:270}},el('div',{style:{display:'flex',fontSize:18,color:'#666'}},label),el('div',{style:{display:'flex',fontSize:36,marginTop:6}},value==null?'Unknown':String(value))))),
 el('div',{style:{display:'flex',fontSize:16,color:'#666',marginTop:22}},'Recorded activity · open the run for evidence and discussion'));
}
