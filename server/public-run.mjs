import {runtimeConfig} from './runtime-config.mjs';
import {BRAND,TAGLINE} from './brand.mjs';
const config=runtimeConfig();
export const origin=config.ORIGIN;
export const validId=id=>typeof id==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function readPublic(id,fetcher=fetch){
 if(!validId(id))return null;
 const query=new URLSearchParams({id:'eq.'+id,visibility:'eq.public',select:'id,title,caption,output_url,repo_url,receipts,shipped,artifact_url,image_url,project,harness,started_at,duration_s,wall_time_s,prompts,tool_calls,shell_calls,files_touched,artifacts_produced,commits,rhythm,route,trace_basis,ridge,worker_bins,commit_bins,ridge_basis,ridge_wall_seconds,ridge_tool_calls,code_route,visibility,profiles!runs_profile_id_fkey(github_handle,handle,display_name)',limit:'1'});
 const response=await fetcher(config.SB_URL+'/rest/v1/runs?'+query,{headers:{apikey:config.SB_KEY,"Accept-Profile":config.SB_SCHEMA},cache:'no-store',signal:AbortSignal.timeout(8000)});
 if(!response.ok)throw new Error('Public run unavailable');const rows=await response.json();
 // The query asks for public rows only. The row is checked again here, so a lost filter or a
 // permissive REST layer still cannot put a close friends, link or only-me run on this page.
 return Array.isArray(rows)&&rows.length===1&&rows[0]?.visibility==='public'?rows[0]:null;
}
const pageStyle=`*{box-sizing:border-box}body{background:#f8f8f6;color:#111;font:17px/1.5 system-ui;margin:0;padding:clamp(16px,4vw,32px)}main{max-width:760px;margin:24px auto}a{color:#123cff}a.home{display:inline-block;font-weight:750;text-decoration:none;padding:10px 0;margin-bottom:20px}article{background:#fff;border:1px solid #d9deea;border-radius:20px;padding:clamp(20px,4vw,32px);min-width:0}h1{font-size:clamp(28px,6vw,42px);line-height:1.15;margin:0 0 16px;overflow-wrap:anywhere}p{overflow-wrap:anywhere}.caption{white-space:pre-wrap}.byline,.note{color:#596174;font-size:15px}.byline{margin:0 0 12px}figure{margin:24px 0}.run-map h2{font-size:18px;margin:0 0 12px}.run-map svg{display:block;width:100%;height:150px;overflow:visible}.run-map figcaption{font-size:14px;color:#596174;margin-top:10px}dl{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:20px 16px;margin:24px 0}dt{font-size:14px;color:#596174}dd{font-size:22px;font-weight:700;margin:4px 0 0;line-height:1.2;overflow-wrap:anywhere}a.open{display:inline-block;background:#123cff;color:white;text-decoration:none;padding:14px 20px;border-radius:8px;margin:8px 8px 8px 0}a.open-profile{display:inline-block;color:#123cff;text-decoration:none;padding:14px 0;font-weight:650;margin:8px 0}a:focus-visible{outline:3px solid #111;outline-offset:4px}.note{margin-bottom:0}.outcome{margin:24px 0 0;padding:16px 18px;border:1px solid #d9deea;border-radius:12px}.outcome h2{font-size:14px;color:#596174;font-weight:600;margin:0 0 8px;text-transform:none}.outcome p,.outcome li{font-size:15px;margin:6px 0}.outcome ul{margin:8px 0;padding-left:20px}.code-route{margin:8px 0 0;color:#123cff;min-width:0;overflow-wrap:anywhere}.code-route h2{font-size:14px;color:#123cff;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin:0 0 8px}.code-route svg{display:block;width:100%;height:auto}.code-route-projects{list-style:none;margin:8px 0 0;padding:0;display:grid;gap:4px;color:#111;font-size:14px}.code-route-projects li{display:flex;gap:8px;align-items:baseline;min-width:0}.code-route-projects li[data-dense="1"] .code-route-project-name{font-weight:650}.code-route-lane-mark{flex:none;min-width:1.1em;color:#123cff;font-weight:600;font-variant-numeric:tabular-nums}.code-route-insight{font-size:18px;line-height:1.35;color:#111;margin:12px 0 0;font-weight:600}.code-route-stats,.code-route-harnesses,.code-route-why{font-size:14px;color:#596174;margin:8px 0 0;overflow-wrap:anywhere}.code-route-stops{margin:8px 0 0;display:grid;gap:6px;min-width:0}.code-route-point summary{cursor:pointer;display:flex;flex-wrap:wrap;gap:4px 8px;align-items:baseline;min-width:0}.code-route-kind{color:#123cff;font-size:12px;font-weight:600;text-transform:uppercase}.code-route-stop-label,.code-route-stop-project{min-width:0;overflow-wrap:anywhere}.code-route-basis{color:#596174}`;
const recordedCount=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0?String(value):null;
const pageMetrics=run=>{
 const session=duration((run.ridge_basis==='wall-time'?run.ridge_wall_seconds:null)??run.wall_time_s??run.duration_s);
 return [
  ['Session',session==='Unknown'?null:session],
  ['Turns',recordedCount(run.prompts)],
  ['Tool calls',recordedCount(toolCallCount(run))],
  ['Files touched',recordedCount(run.files_touched)],
  ['Commits',recordedCount(run.commits)],
 ].filter(([,value])=>value!==null);
};
// The social preview is a fixed 1200px image, not a phone layout. Keep its metadata but
// draw the measured map natively here; labels and counts remain readable HTML.
const pageRunMap=run=>{
 const ridge=ridgeSeries(run);
 const basis=run.ridge_basis==='wall-time'?'wall time':run.ridge_basis==='turn-order'?'turn order':run.ridge_basis==='call-index'?'call order':null;
 if(!ridge||!basis||!ridge.values.every(Number.isSafeInteger))return '';
 const values=ridge.values,width=800,baseline=132,peak=Math.max(1,...values);
 const points=values.map((v,i)=>`${(i*width/(values.length-1)).toFixed(1)},${(baseline-v*116/peak).toFixed(1)}`).join(' ');
 const commits=Array.isArray(run.commit_bins)?run.commit_bins.filter(v=>Number.isSafeInteger(v)&&v>=0&&v<values.length):[];
 const ticks=commits.map(v=>{const x=(v*width/(values.length-1)).toFixed(1);return `<line x1="${x}" y1="132" x2="${x}" y2="122" stroke="#111" stroke-width="2" vector-effect="non-scaling-stroke"/>`;}).join('');
 return `<figure class="run-map"><h2>Run map</h2><svg viewBox="0 0 800 150" preserveAspectRatio="none" role="img" aria-label="Tool calls over ${basis}"><polygon points="0,132 ${points} 800,132" fill="#123cff" fill-opacity="0.1"/><polyline points="${points}" fill="none" stroke="#123cff" stroke-width="3" vector-effect="non-scaling-stroke"/>${ticks}</svg><figcaption>Tool calls over ${basis}${commits.length?' · Commit marks show recorded locations':''}</figcaption></figure>`;
};
// A stored row is untrusted input: it was written by an agent through the upload endpoint. Every
// link is re-checked here before it reaches a signed-out page, with the same rule the database and
// the browser contract use.
const safeUrl=u=>typeof u==='string'&&u.length>=12&&u.length<=300&&/^https:\/\//.test(u)&&!/[\s<>"'\\]/.test(u)&&!/javascript:/i.test(u);
const outcomeLink=(href,text)=>safeUrl(href)?`<a href="${esc(href)}" rel="noopener noreferrer nofollow">${esc(text)}</a>`:'';
// Declared by the uploader, never measured, so this block sits under its own heading and never
// joins the counts. No remote image is embedded: an arbitrary third party host would learn the IP
// and user agent of every visitor to a public page, and a dead link would show a broken box. The
// screenshot is offered as a link the reader chooses to open.
const pageOutcome=run=>{
 const parts=[];
 if(safeUrl(run.repo_url))parts.push(`<p class="outcome-repo">${outcomeLink(run.repo_url,String(run.repo_url).replace(/^https:\/\//,''))}</p>`);
 const shipped=Array.isArray(run.shipped)?run.shipped.filter(l=>typeof l==='string'&&l.trim()).slice(0,5):[];
 if(shipped.length)parts.push(`<ul class="outcome-shipped">${shipped.map(l=>`<li>${esc(l.trim().slice(0,120))}</li>`).join('')}</ul>`);
 const links=(Array.isArray(run.receipts)?run.receipts:[]).filter(r=>r&&typeof r.label==='string'&&safeUrl(r.url)).slice(0,5)
  .map(r=>outcomeLink(r.url,r.label.trim().slice(0,60)));
 if(safeUrl(run.artifact_url))links.push(outcomeLink(run.artifact_url,'Open the demo'));
 if(safeUrl(run.image_url)&&/\.(png|jpe?g|webp)([?#].*)?$/i.test(run.image_url))links.push(outcomeLink(run.image_url,'Open the screenshot'));
 if(links.length)parts.push(`<p class="outcome-links">${links.join(' · ')}</p>`);
 return parts.length?`<section class="outcome"><h2>Said by the uploader, not measured</h2>${parts.join('')}</section>`:'';
};

const routeInsight=route=>{
 if(!route||typeof route!=='object'||Array.isArray(route)||route.v!==1||route.unavailable)return '';
 const projects=Array.isArray(route.projects)?route.projects:[];
 const stops=Array.isArray(route.stops)?route.stops:[];
 if(!projects.length||!stops.length)return '';
 const connectors=Array.isArray(route.connectors)?route.connectors:[];
 const handoffs=connectors.filter(c=>c&&c.kind==='handoff');
 const measured=stops.filter(s=>s&&s.basis==='measured').length;
 const declared=stops.filter(s=>s&&s.basis==='declared').length;
 const counts=Object.create(null);
 for(const stop of stops){if(!stop||!stop.project)continue;counts[stop.project]=(counts[stop.project]||0)+1;}
 let densest=null,densestN=0,ties=0;
 for(const project of projects){const n=counts[project.id]||0;if(n>densestN){densest=project;densestN=n;ties=1;}else if(n===densestN&&n>0)ties+=1;}
 const finishStop=route.finish&&stops.find(s=>s.id===route.finish.stop);
 const finishProject=finishStop&&projects.find(p=>p.id===finishStop.project);
 const parts=[];
 if(densest&&ties===1&&densestN>0&&densestN<stops.length)parts.push(densest.label+' held the densest stretch ('+densestN+' of '+stops.length+' stops)');
 if(handoffs.length){
  if(finishProject&&densest&&finishProject.id!==densest.id)parts.push(handoffs.length+(handoffs.length===1?' handoff carried the work to ':' handoffs carried the work to ')+finishProject.label);
  else parts.push(handoffs.length+(handoffs.length===1?' handoff across the route':' handoffs across the route'));
 }
 if(measured+declared===stops.length){
  if(declared===0&&measured===stops.length)parts.push('every stop is measured');
  else if(declared>0)parts.push(measured+' measured, '+declared+' declared');
 }
 if(route.finish&&route.finish.kind==='artifact'&&route.finish.label&&parts.length<2)parts.push('finish '+route.finish.label);
 if(!parts.length)return '';
 return parts[0]+parts.slice(1).map(part=>'. '+part.charAt(0).toUpperCase()+part.slice(1)).join('')+'.';
};

const pageCodeRoute=run=>{
 const route=run&&run.code_route;
 if(!route||route.v!==1)return '';
 if(route.unavailable){
  const harness=route.harnesses?`<p class="code-route-harnesses">Harness populations · basis ${esc(route.harnesses.basis)} · observed: ${(route.harnesses.observed||[]).map(esc).join(', ')||'none'} · absent: ${(route.harnesses.absent||[]).map(esc).join(', ')||'none'}</p>`:'';
  return `<section class="code-route"><h2>Code Route</h2><p class="code-route-why">${esc(route.unavailable.why||'')}</p>${harness}</section>`;
 }
 const projects=Array.isArray(route.projects)?route.projects:[];
 const stops=Array.isArray(route.stops)?route.stops:[];
 if(!projects.length||!stops.length)return '';
 const idx=Object.fromEntries(projects.map((p,i)=>[p.id,i]));
 const left=28,width=360,rowH=28,top=18,height=top+projects.length*rowH+12;
 const finishId=route.finish&&route.finish.stop;
 const handoffTo=new Set((Array.isArray(route.connectors)?route.connectors:[]).filter(c=>c&&c.kind==='handoff'&&c.to).map(c=>c.to));
 const insight=routeInsight(route);
 const counts=Object.create(null);for(const stop of stops){if(stop&&stop.project)counts[stop.project]=(counts[stop.project]||0)+1;}
 let dense=null,denseN=0,ties=0;for(const p of projects){const n=counts[p.id]||0;if(n>denseN){dense=p;denseN=n;ties=1;}else if(n===denseN&&n>0)ties+=1;}
 const denseId=ties===1&&denseN>0?dense.id:null;
 const points=stops.map((stop,i)=>{const row=idx[stop.project]??0;const x=left+(i*(width-left-16))/Math.max(1,stops.length-1);const y=top+row*rowH+rowH/2;return {stop,x,y,finish:stop.id===finishId,handoff:handoffTo.has(stop.id)};});
 const line=points.map((p,i)=>`${i?'L':'M'}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');
 const dots=points.map(p=>`<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${p.finish?5.5:p.handoff?4.5:3.5}" fill="${p.finish?'#111':'#123cff'}" ${p.handoff&&!p.finish?'stroke="#111" stroke-width="1.5"':''}/>`).join('');
 const lanes=projects.map((p,i)=>{const y=top+i*rowH+rowH/2+4;return `<text x="0" y="${y}" fill="#596174" font-size="11">${i+1}</text>`;}).join('');
 const projectList=projects.map((p,i)=>`<li${denseId===p.id?' data-dense="1"':''}><span class="code-route-lane-mark" aria-hidden="true">${i+1}</span><span class="code-route-project-name">${esc(p.label)}</span></li>`).join('');
 const names=projects.map(p=>p.label).join(', ');
 const measured=stops.filter(s=>s.basis==='measured').length,declared=stops.filter(s=>s.basis==='declared').length;
 const aria=`Code Route across ${projects.length} projects: ${names}. ${stops.length} ordered checkpoints · ${measured} measured · ${declared} declared${insight?' · '+insight:''}`;
 const stopList=stops.map(stop=>{const project=projects.find(p=>p.id===stop.project);const lane=project?(idx[project.id]??0)+1:null;const evidence=Array.isArray(stop.evidence)&&stop.evidence.length?`<ul>${stop.evidence.map(line=>`<li>${esc(line)}</li>`).join('')}</ul>`:'';return `<details class="code-route-point"${stop.id===finishId?' data-finish="1"':''}><summary><span class="code-route-kind">${esc(stop.kind)}</span><span class="code-route-stop-label">${esc(stop.label)}</span><span class="code-route-basis">${esc(stop.basis)}</span>${project?`<span class="code-route-stop-project">${lane!=null?`${lane} · `:''}${esc(project.label)}</span>`:''}</summary>${evidence}</details>`;}).join('');
 const harness=route.harnesses?`<p class="code-route-harnesses">Harness populations · basis ${esc(route.harnesses.basis)} · observed: ${(route.harnesses.observed||[]).map(esc).join(', ')||'none'} · absent: ${(route.harnesses.absent||[]).map(esc).join(', ')||'none'}</p>`:'';
 return `<section class="code-route" aria-label="${esc(aria)}"><h2>Code Route</h2><svg viewBox="0 0 ${width} ${height}" role="img" aria-hidden="true"><path class="code-route-line" pathLength="1" d="${line}" fill="none" stroke="#123cff" stroke-width="2.5"/>${dots}${lanes}</svg><ol class="code-route-projects">${projectList}</ol>${insight?`<p class="code-route-insight">${esc(insight)}</p>`:''}<div class="code-route-stops">${stopList}</div>${harness}</section>`;
};

export function html(run){const title=esc(run.title||'Agent run'),insight=routeInsight(run&&run.code_route),description=esc(insight||run.caption||'See the work, its recorded activity and the conversation.'),id=encodeURIComponent(run.id),image=origin+'/api/run?id='+id+'&image=1',url=origin+'/r/'+id;
 const facts=pageMetrics(run),handle=run.profiles?.handle||run.profiles?.github_handle;
 const profileHref=handle?'/?u='+encodeURIComponent(handle):'';
 const byline=handle?`<a href="${esc(profileHref)}">@${esc(handle)}</a>${projectName(run)?' · '+esc(projectName(run)):''}${run.harness?' · '+esc(run.harness):''}`:[projectName(run),run.harness].filter(Boolean).map(esc).join(' · ');
 const routeHtml=pageCodeRoute(run);
 const metrics=facts.length&&!routeHtml?`<dl aria-label="Recorded activity">${facts.map(([label,value])=>`<div><dt>${label}</dt><dd>${esc(value)}</dd></div>`).join('')}</dl>`:'';
 const output=outputKind(run)?`<p><a href="${esc(run.output_url)}" rel="noopener noreferrer">View linked output</a></p>`:'';
 const profileAct=profileHref?`<a class="open-profile" href="${esc(profileHref)}">Open builder profile</a>`:'';
 return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title} · ${BRAND}</title><meta property="og:type" content="article"><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${url}"><meta property="og:image" content="${image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="${image}"><link rel="canonical" href="${url}"><style>${pageStyle}</style></head><body><main><a class="home" href="/" aria-label="${BRAND} home">${BRAND} · Home</a><article>${byline?`<p class="byline">${byline}</p>`:''}<h1>${title}</h1>${run.caption?`<p class="caption">${esc(run.caption)}</p>`:''}${routeHtml||pageRunMap(run)}${output}${pageOutcome(run)}<p>${profileAct}<a class="open" href="/?run=${id}">Open run and discussion</a></p>${metrics}<p class="note">Counts describe activity, not result quality.</p></article></main></body></html>`;
}
// The page for a run that is missing or not public. Same words as privateCard, same neutral
// image, and nothing from a row, because there is no row: the public-only query returns
// nothing for a close friends, link or only-me run exactly as it does for an id that never
// existed, and the page must not tell those apart. The run link goes to /?run=id, where a
// signed-in reader who was given access can open it.
export function neutralHtml(id){const safe=encodeURIComponent(id),image=origin+'/api/run?id='+safe+'&image=1',url=origin+'/r/'+safe,title=esc(`This run is private on ${BRAND}`),description='Sign in and open the shared run link to check your access.';
 // Crawlers and strangers keep this neutral card. A signed-in permitted reader is sent to
 // /?run=<id>, where the SPA enforces follow or close-friends before showing the truthful card.
 return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><meta name="robots" content="noindex"><meta property="og:type" content="article"><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${url}"><meta property="og:image" content="${image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="${title}"><meta name="twitter:description" content="${description}"><meta name="twitter:image" content="${image}"><style>${pageStyle}</style></head><body><main><a class="home" href="/" aria-label="${BRAND} home">${BRAND} · Home</a><article><h1>${title}</h1><p>${description}</p><a class="open" href="/?run=${safe}">Sign in and open the run</a></article></main><script>try{var id=${JSON.stringify(String(id||''))};if(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id))location.replace("/?run="+encodeURIComponent(id))}catch(e){}</script></body></html>`;
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
 // Legacy rhythm/route remain readable when no ridge bins exist. A flat all-zero leftover
 // rhythm is not a route — that reads as a measured empty trace, so it stays undrawn.
 for(const [values,label] of [[run.rhythm,'Session trace'],[run.route,'Project ridge']]){
  if(Array.isArray(values)&&values.length>1&&values.length<=10000&&values.every(v=>Number.isFinite(v)&&v>=0)&&values.some(v=>v>0))return{values,label,filled:false};
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
// real call count, print that count so the label matches the graph and the SPA strip.
// A recorded zero beside a live ridge with no ridge_tool_calls contradicts the map; omit it.
export const toolCallCount=run=>{
 const recorded=run.tool_calls;
 const fromRidge=run.ridge_tool_calls;
 if((recorded==null||recorded===0)&&Number.isFinite(fromRidge)&&fromRidge>0)return fromRidge;
 const ridge=Array.isArray(run.ridge)?run.ridge:null;
 const ridgeLive=ridge&&ridge.length&&ridge.every(v=>Number.isFinite(v)&&v>=0)&&ridge.some(v=>v>0);
 if(recorded===0&&ridgeLive&&!(Number.isFinite(fromRidge)&&fromRidge>0))return null;
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
 if(run.shell_calls!=null)facts.push(run.shell_calls+' shell calls');
 if(run.files_touched!=null)facts.push(run.files_touched+' files changed');
 if(run.commits!=null)facts.push(run.commits+' commits');
 return facts.join(' · ')||null;
};
const codeRoutePlot=run=>{
 const route=run&&run.code_route;
 if(!route||route.v!==1||route.unavailable||!Array.isArray(route.projects)||!Array.isArray(route.stops)||!route.projects.length||!route.stops.length)return null;
 const idx=Object.fromEntries(route.projects.map((p,i)=>[p.id,i]));
 const n=Math.max(1,route.projects.length);
 return {projects:route.projects,stops:route.stops,idx,n,finish:route.finish&&route.finish.stop,stats:route.stats||{},label:(route.stats&&route.stats.projects_touched!=null)?`${route.stats.projects_touched} projects touched · Code Route`:'Code Route'};
};
export function card(run){
 const routePlot=codeRoutePlot(run);
 const insight=routePlot?routeInsight(run.code_route):'';
 const plotted=routePlot?null:series(run),max=plotted?Math.max(...plotted.values)||1:1;
 const points=plotted?plotted.values.map((v,i)=>`${i/(plotted.values.length-1)*1030},${125-v/max*105}`).join(' '):'';
 const area=plotted?`0,125 ${points} 1030,125`:'';
 const session=run.ridge_basis==='wall-time'?run.ridge_wall_seconds:null;
 const metric=(label,value)=>[label,recordedCount(value)];
 const effort=[
  ['Session',duration(session??run.wall_time_s??run.duration_s)],
  metric('Turns',run.prompts),
  metric('Tool calls',toolCallCount(run)),
 ].filter(([,value])=>value!==null&&value!=='Unknown');
 const story=[];
 const output=outputKind(run);if(output)story.push(['Output',output]);
 const project=projectName(run);if(project)story.push(['Project touched',project]);
 const code=codeFacts(run);if(code)story.push(['Code activity',code]);
 const handle=run.visibility==='public'&&(run.profiles?.handle||run.profiles?.github_handle);
 return el('div',{style:{width:'100%',height:'100%',background:'#f5f7fb',color:'#111',display:'flex',padding:'30px',fontFamily:'sans-serif'}},
  el('div',{style:{width:'100%',height:'100%',background:'#fff',border:'1px solid #d9deea',borderRadius:22,display:'flex',flexDirection:'column',padding:'34px 48px'}},
   el('div',{style:{display:'flex',justifyContent:'space-between',alignItems:'center'}},
    el('div',{style:{display:'flex',color:'#123cff',fontSize:27,fontWeight:800}},BRAND),
    handle?el('div',{style:{display:'flex',fontSize:20,color:'#555'}},'@'+handle):null),
   el('div',{style:{display:'flex',fontSize:13,color:'#123cff',fontWeight:700,letterSpacing:1.2,marginTop:10}},'ACHIEVED'),
   el('div',{style:{display:'flex',fontSize:(plotted||routePlot)?38:48,fontWeight:750,marginTop:(plotted||routePlot)?3:18,height:(plotted||routePlot)?56:74,lineHeight:1.2,overflow:'hidden'}},String(run.title||'Agent run').slice(0,120)),
   run.caption?el('div',{style:{display:'flex',fontSize:18,color:'#333',marginTop:2,height:24,overflow:'hidden'}},String(run.caption).slice(0,160)):null,
   story.length?el('div',{style:{display:'flex',marginTop:10,borderTop:'1px solid #d9deea',borderBottom:'1px solid #d9deea'}},
    ...story.map(([label,value])=>el('div',{style:{display:'flex',flexDirection:'column',width:1030/story.length,padding:'9px 8px 10px 0'}},
     el('div',{style:{display:'flex',fontSize:13,color:'#687083'}},label),
     el('div',{style:{display:'flex',fontSize:19,fontWeight:650,marginTop:3,color:label==='Output'?'#123cff':'#111',height:26,overflow:'hidden',border:label==='Output'?'1px solid #c4d2ff':'none',background:label==='Output'?'#f2f5ff':'transparent',padding:label==='Output'?'2px 7px':'0'}},value)))):null,
   routePlot?el('div',{style:{display:'flex',flexDirection:'column',marginTop:9}},
    el('svg',{width:1030,height:Math.max(90,routePlot.n*22+20),viewBox:`0 0 1030 ${Math.max(90,routePlot.n*22+20)}`},
     el('path',{d:routePlot.stops.map((stop,i)=>{const row=routePlot.idx[stop.project]||0;const x=36+i/Math.max(1,routePlot.stops.length-1)*960;const y=16+row*22+11;return `${i?'L':'M'}${x} ${y}`;}).join(' '),stroke:'#123cff',strokeWidth:4,fill:'none'}),
     ...routePlot.stops.map((stop,i)=>{const row=routePlot.idx[stop.project]||0;const x=36+i/Math.max(1,routePlot.stops.length-1)*960;const y=16+row*22+11;const finish=routePlot.finish===stop.id;return el('circle',{cx:x,cy:y,r:finish?7:4.5,fill:finish?'#111':'#123cff'});})
    ),
    el('div',{style:{display:'flex',flexDirection:'column',fontSize:15,color:'#333',marginTop:6,gap:2}},
     ...routePlot.projects.map((p,i)=>el('div',{style:{display:'flex'}},`${i+1} · ${p.label}`))),
    insight?el('div',{style:{display:'flex',fontSize:18,color:'#111',fontWeight:650,marginTop:8,height:52,overflow:'hidden'}},insight):el('div',{style:{display:'flex',fontSize:13,color:'#687083',marginTop:4}},routePlot.label))
    :plotted?el('div',{style:{display:'flex',flexDirection:'column',marginTop:9}},
    el('svg',{width:1030,height:100,viewBox:'0 0 1030 130'},...(plotted.filled?[
     el('polygon',{points:area,fill:'#123cff',fillOpacity:0.16}),
     el('line',{x1:0,y1:125,x2:1030,y2:125,stroke:'#d9deea',strokeWidth:2}),
     el('polyline',{points,stroke:'#123cff',strokeWidth:4,strokeLinejoin:'round',strokeLinecap:'round',fill:'none'})]:[
     el('polyline',{points,stroke:'#123cff',strokeWidth:5,strokeLinejoin:'round',strokeLinecap:'round',fill:'none'})])),
    el('div',{style:{display:'flex',fontSize:13,color:'#687083',marginTop:1}},plotted.label))
    :null,
   !routePlot&&effort.length?el('div',{style:{display:'flex',fontSize:13,color:'#123cff',fontWeight:700,letterSpacing:1.2,marginTop:plotted?7:32}},'ACTIVITY'):null,
   !routePlot&&effort.length?el('div',{style:{display:'flex',marginTop:3,borderTop:'1px solid #d9deea',paddingTop:plotted?8:18}},
    ...effort.map(([label,value])=>el('div',{style:{display:'flex',flexDirection:'column',width:1030/effort.length}},
     el('div',{style:{display:'flex',fontSize:13,color:'#687083'}},label),
     el('div',{style:{display:'flex',fontSize:plotted?27:64,fontWeight:700,marginTop:3,color:'#111'}},value)))):null,
   el('div',{style:{display:'flex',fontSize:13,color:'#687083',marginTop:'auto'}},'Counts describe activity, not result quality.')));
}
export function privateCard(){
 return el('div',{style:{width:'100%',height:'100%',background:'#f5f7fb',display:'flex',padding:'30px',fontFamily:'sans-serif',color:'#111'}},
  el('div',{style:{width:'100%',height:'100%',background:'#fff',border:'1px solid #d9deea',borderRadius:22,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}},
   el('div',{style:{display:'flex',color:'#123cff',fontSize:28,fontWeight:800}},BRAND),
   el('div',{style:{display:'flex',fontSize:42,fontWeight:700,marginTop:34}},`This run is private on ${BRAND}`),
   el('div',{style:{display:'flex',fontSize:21,color:'#687083',marginTop:18}},'Sign in and open the shared run link to check your access')));
}
// THE HOME PAGE'S OWN CARD. Until now `/` carried no og: or twitter: tags at all, so a post that
// sent a thousand people to the address showed them a bare link with no title, no description and
// no image — the first impression of the product was the URL. This reuses the run image pipeline
// (@vercel/og at 1200x630, served by api/og.js) rather than committing a static PNG, so the
// brand and tagline come from server/brand.mjs like every other name on the site.
export function homeCard(){
 return el('div',{style:{width:'100%',height:'100%',background:'#f5f7fb',display:'flex',padding:'30px',fontFamily:'sans-serif',color:'#111'}},
  el('div',{style:{width:'100%',height:'100%',background:'#fff',border:'1px solid #d9deea',borderRadius:22,display:'flex',flexDirection:'column',justifyContent:'center',padding:'54px'}},
   el('div',{style:{display:'flex',color:'#123cff',fontSize:30,fontWeight:800,letterSpacing:6}},BRAND),
   el('div',{style:{display:'flex',fontSize:64,fontWeight:700,marginTop:26,lineHeight:1.1}},TAGLINE),
   el('div',{style:{display:'flex',fontSize:26,color:'#687083',marginTop:24,lineHeight:1.35}},
     'Every run your agent made, on a card you can share.'),
   el('div',{style:{display:'flex',fontSize:20,color:'#687083',marginTop:'auto'}},
     'Capture a Cursor, Claude Code, Codex or Grok Bot session · private until you choose to share')));
}

