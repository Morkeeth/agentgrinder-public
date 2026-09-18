import {runtimeConfig} from './runtime-config.mjs';
import {BRAND} from './brand.mjs';
const config=runtimeConfig();
export const origin=config.ORIGIN;
export const validId=id=>typeof id==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function readPublic(id,fetcher=fetch){
 if(!validId(id))return null;
 const query=new URLSearchParams({id:'eq.'+id,visibility:'eq.public',select:'id,title,caption,output_url,project,harness,started_at,duration_s,wall_time_s,prompts,tool_calls,shell_calls,files_touched,artifacts_produced,commits,rhythm,route,trace_basis,ridge,worker_bins,commit_bins,ridge_basis,ridge_wall_seconds,ridge_tool_calls,visibility,profiles!runs_profile_id_fkey(github_handle,handle,display_name)',limit:'1'});
 const response=await fetcher(config.SB_URL+'/rest/v1/runs?'+query,{headers:{apikey:config.SB_KEY,"Accept-Profile":config.SB_SCHEMA},cache:'no-store',signal:AbortSignal.timeout(8000)});
 if(!response.ok)throw new Error('Public run unavailable');const rows=await response.json();
 return Array.isArray(rows)&&rows.length===1?rows[0]:null;
}
export function html(run){const title=esc(run.title||'Agent run'),description=esc(run.caption||'See the work, its recorded activity and the conversation.'),id=encodeURIComponent(run.id),image=origin+'/api/run?id='+id+'&image=1',url=origin+'/r/'+id;
 return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title} · ${BRAND}</title><meta property="og:type" content="article"><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${url}"><meta property="og:image" content="${image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="${image}"><link rel="canonical" href="${url}"><style>body{background:#f8f8f6;color:#111;font:18px system-ui;margin:0;padding:32px}main{max-width:900px;margin:40px auto}img{width:100%;height:auto;border:1px solid #ddd}a{color:#123cff}h1{font-size:clamp(28px,5vw,48px);line-height:1.1}a.open{display:inline-block;background:#123cff;color:white;text-decoration:none;padding:16px 24px;margin:24px 0}</style></head><body><main><a href="/">${BRAND}</a><h1>${title}</h1><p>${description}</p><img src="${image.replaceAll('&','&amp;')}" alt="Recorded activity for ${title}" width="1200" height="630"><a class="open" href="/?run=${id}">Open run and discussion</a><p>Recorded counts describe activity. They do not independently verify the result.</p></main></body></html>`;
}
const el=(type,props,...children)=>({type,props:{...props,children:children.length===1?children[0]:children}});
// The persisted ridge wins when the run carries one. It is the same 40 to 60 bins the run page
// draws (site/run-contract.js, function ridge), so the share image and the page agree. A run
// saved before migration 003 has no bins and keeps its rhythm polyline.
const ridgeSeries=run=>{
 const values=run.ridge,workers=run.worker_bins;
 if(!Array.isArray(values)||values.length<40||values.length>60)return null;
 if(!values.every(v=>Number.isInteger(v)&&v>=0))return null;
 if(!Array.isArray(workers)||workers.length!==values.length)return null;
 return{values,label:'Agent ridge',filled:true};
};
const series=run=>{
 const ridge=ridgeSeries(run);
 if(ridge)return ridge;
 // A null ridge means the shape was never stored. Do not fall back to a flat rhythm line
 // that reads as a measured zero. Runs that omit the field still keep the legacy rhythm path.
 if(run.ridge===null)return null;
 for(const [values,label] of [[run.rhythm,'Session trace'],[run.route,'Project ridge']]){
  if(Array.isArray(values)&&values.length>1&&values.length<=10000&&values.every(v=>Number.isFinite(v)&&v>=0))return{values,label,filled:false};
 }
 return null;
};
const duration=value=>{
 if(value==null)return'Unknown';
 const seconds=Number(value);if(!Number.isFinite(seconds)||seconds<0)return'Unknown';
 if(seconds<60)return`${Math.round(seconds)}s`;
 const minutes=Math.round(seconds/60);return minutes>=60?`${Math.floor(minutes/60)}h ${minutes%60}m`:`${minutes}m`;
};
// Prefer the transcript count. When it is zero or missing and the stored ridge carried a
// real call count, print that count so the label matches the graph.
const toolCallCount=run=>{
 const recorded=run.tool_calls;
 const fromRidge=run.ridge_tool_calls;
 if((recorded==null||recorded===0)&&Number.isFinite(fromRidge)&&fromRidge>0)return fromRidge;
 return recorded;
};
const projectName=run=>{
 let value=typeof run.project==='string'?run.project.trim():'';
 if(!value||['session','unknown','project unknown'].includes(value.toLowerCase()))return null;
 const cleaned=value.replace(/^CODE-(?:worktrees-)?/i,'').replace(/-\d{8}$/,'');
 // Only turn dashes into spaces when we stripped a worktree prefix or date stamp.
 if(cleaned!==value)value=cleaned.replace(/-/g,' ').replace(/\s+/g,' ').trim();
 else value=cleaned;
 return value||null;
};
const outputKind=run=>{
 try{
  const url=new URL(run.output_url);
  if(!/^https?:$/.test(url.protocol))return null;
  if(/github\.com\/[^/]+\/[^/]+\/pull\/\d+/i.test(url.href))return'PR linked';
  if(/\.(png|jpe?g|webp)(?:[?#]|$)/i.test(url.href))return'Screenshot linked';
  return'Output linked';
 }catch(_){return null}
};
const codeFacts=run=>{
 const facts=[];
 const tools=toolCallCount(run);
 if(run.shell_calls!=null)facts.push(run.shell_calls+' shell calls');
 if(run.files_touched!=null)facts.push(run.files_touched+' files changed');
 if(run.commits!=null)facts.push(run.commits+' commits');
 if(!facts.length&&tools!=null)facts.push(tools+' tool calls');
 return facts.join(' · ')||'Unknown';
};
export function card(run){
 const plotted=series(run),max=plotted?Math.max(...plotted.values)||1:1;
 const points=plotted?plotted.values.map((v,i)=>`${i/(plotted.values.length-1)*1030},${125-v/max*105}`).join(' '):'';
 const area=plotted?`0,125 ${points} 1030,125`:'';
 const session=run.ridge_basis==='wall-time'?run.ridge_wall_seconds:null;
 const metric=(label,value)=>[label,value==null?'Unknown':String(value)];
 const missingShape=run.ridge===null;
 const effort=[
  ['Session',duration(session??run.wall_time_s??run.duration_s)],
  metric('Turns',run.prompts),
  metric('Tool calls',toolCallCount(run)),
 ];
 const story=[];
 const output=outputKind(run);if(output)story.push(['Output',output]);
 story.push(['Project touched',projectName(run)||'Unknown'],['Code activity',codeFacts(run)]);
 const handle=run.visibility==='public'&&(run.profiles?.handle||run.profiles?.github_handle);
 return el('div',{style:{width:'100%',height:'100%',background:'#f5f7fb',color:'#111',display:'flex',padding:'30px',fontFamily:'sans-serif'}},
  el('div',{style:{width:'100%',height:'100%',background:'#fff',border:'1px solid #d9deea',borderRadius:22,display:'flex',flexDirection:'column',padding:'34px 48px'}},
   el('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center'}},
    el('div',{style:{display:'flex',color:'#123cff',fontSize:27,fontWeight:800}},BRAND),
    handle?el('div',{style:{display:'flex',fontSize:20,color:'#555'}},'@'+handle):null),
   el('div',{style:{display:'flex',fontSize:13,color:'#123cff',fontWeight:700,letterSpacing:1.2,marginTop:10}},'ACHIEVED'),
   el('div',{style:{display:'flex',fontSize:38,fontWeight:750,marginTop:3,height:56,lineHeight:1.2,overflow:'hidden'}},String(run.title||'Agent run').slice(0,120)),
   run.caption?el('div',{style:{display:'flex',fontSize:18,color:'#333',marginTop:2,height:24,overflow:'hidden'}},String(run.caption).slice(0,160)):null,
   el('div',{style:{display:'flex',marginTop:10,borderTop:'1px solid #d9deea',borderBottom:'1px solid #d9deea'}},
    ...story.map(([label,value])=>el('div',{style:{display:'flex',flexDirection:'column',width:story.length===3?343:515,padding:'9px 8px 10px 0'}},
     el('div',{style:{display:'flex',fontSize:13,color:'#687083'}},label),
     el('div',{style:{display:'flex',fontSize:value==='Unknown'?17:19,fontWeight:value==='Unknown'?400:650,marginTop:3,color:value==='Unknown'?'#687083':label==='Output'?'#123cff':'#111',height:26,overflow:'hidden',border:label==='Output'?'1px solid #c4d2ff':'none',background:label==='Output'?'#f2f5ff':'transparent',padding:label==='Output'?'2px 7px':'0'}},value)))),
   plotted?el('div',{style:{display:'flex',flexDirection:'column',marginTop:9}},
    el('svg',{width:1030,height:100,viewBox:'0 0 1030 130'},...(plotted.filled?[
     el('polygon',{points:area,fill:'#123cff',fillOpacity:0.16}),
     el('line',{x1:0,y1:125,x2:1030,y2:125,stroke:'#d9deea',strokeWidth:2}),
     el('polyline',{points,stroke:'#123cff',strokeWidth:4,strokeLinejoin:'round',strokeLinecap:'round',fill:'none'})]:[
     el('polyline',{points,stroke:'#123cff',strokeWidth:5,strokeLinejoin:'round',strokeLinecap:'round',fill:'none'})])),
    el('div',{style:{display:'flex',fontSize:13,color:'#687083',marginTop:1}},plotted.label))
    :el('div',{style:{display:'flex',height:114,alignItems:'center',color:'#687083',fontSize:18,marginTop:9}},missingShape?'Shape was not recorded for this run':'Trace unavailable'),
   el('div',{style:{display:'flex',fontSize:13,color:'#123cff',fontWeight:700,letterSpacing:1.2,marginTop:7}},'EFFORT'),
   el('div',{style:{display:'flex',marginTop:3,borderTop:'1px solid #d9deea',paddingTop:8}},
    ...effort.map(([label,value])=>el('div',{style:{display:'flex',flexDirection:'column',width:343}},
     el('div',{style:{display:'flex',fontSize:13,color:'#687083'}},label),
     el('div',{style:{display:'flex',fontSize:value==='Unknown'?18:27,fontWeight:value==='Unknown'?400:700,marginTop:3,color:value==='Unknown'?'#687083':'#111'}},value)))),
   el('div',{style:{display:'flex',fontSize:13,color:'#687083',marginTop:7}},'Blue trace: this session · counts: activity, not quality · Unknown: not measured')));
}
export function privateCard(){
 return el('div',{style:{width:'100%',height:'100%',background:'#f5f7fb',display:'flex',padding:'30px',fontFamily:'sans-serif',color:'#111'}},
  el('div',{style:{width:'100%',height:'100%',background:'#fff',border:'1px solid #d9deea',borderRadius:22,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}},
   el('div',{style:{display:'flex',color:'#123cff',fontSize:28,fontWeight:800}},BRAND),
   el('div',{style:{display:'flex',fontSize:42,fontWeight:700,marginTop:34}},`This run is private on ${BRAND}`),
   el('div',{style:{display:'flex',fontSize:21,color:'#687083',marginTop:18}},'Sign in and open the shared run link to check your access')));
}
