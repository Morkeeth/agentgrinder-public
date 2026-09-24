import {BRAND} from './brand.mjs';
import {origin as defaultOrigin, validId} from './public-run.mjs';

const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({
 '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;',
}[char]));

const routeFacts=route=>{
 if(!route||route.v!==1||route.unavailable||!Array.isArray(route.projects)||!Array.isArray(route.stops))return null;
 const projects=route.projects.filter(project=>project&&typeof project.id==='string'&&typeof project.label==='string');
 const stops=route.stops.filter(stop=>stop&&typeof stop.id==='string'&&typeof stop.project==='string');
 if(!projects.length||!stops.length)return null;
 const counts=Object.create(null);
 for(const stop of stops)counts[stop.project]=(counts[stop.project]||0)+1;
 let dense=null,denseCount=0,tied=false;
 for(const project of projects){
  const count=counts[project.id]||0;
  if(count>denseCount){dense=project;denseCount=count;tied=false;}
  else if(count===denseCount&&count>0)tied=true;
 }
 if(tied)dense=null;
 const finish=route.finish&&stops.find(stop=>stop.id===route.finish.stop);
 const finishProject=finish&&projects.find(project=>project.id===finish.project);
 const handoffs=(Array.isArray(route.connectors)?route.connectors:[]).filter(connector=>connector&&connector.kind==='handoff');
 const measured=stops.filter(stop=>stop.basis==='measured');
 return {projects,stops,dense,denseCount,finish,finishProject,handoffs,measured};
};

const stopEvidence=stop=>{
 const evidence=Array.isArray(stop?.evidence)?stop.evidence.find(item=>typeof item==='string'&&item.trim()):null;
 return evidence?evidence.trim():'';
};

const actionUrl=(runId,canonical,finish)=>{
 const title='Challenge the fleet-ops handoff';
 const body=[
  'Decision story: '+canonical,
  '',
  'Decision to challenge: carry the measured route beyond its densest stretch to fleet-ops.',
  finish?.label?'Last measured stop: '+finish.label+'.':'',
  '',
  'Challenge or next verified stop:',
 ].filter(Boolean).join('\n');
 const url=new URL('https://github.com/Morkeeth/agentgrinder-public/issues/new');
 url.searchParams.set('title',title);
 url.searchParams.set('body',body);
 return url.href;
};

const routePlot=facts=>{
 const width=330,left=9,right=9,top=8,rowHeight=15;
 const height=top+facts.projects.length*rowHeight+8;
 const rows=Object.fromEntries(facts.projects.map((project,index)=>[project.id,index]));
 const points=facts.stops.map((stop,index)=>({
  stop,
  x:left+index/Math.max(1,facts.stops.length-1)*(width-left-right),
  y:top+(rows[stop.project]??0)*rowHeight+rowHeight/2,
 }));
 const path=points.map((point,index)=>`${index?'L':'M'}${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ');
 const dots=points.map(point=>{
  const finish=point.stop.id===facts.finish?.id;
  return `<circle cx="${point.x.toFixed(1)}" cy="${point.y.toFixed(1)}" r="${finish?4.5:3}" fill="${finish?'#111':'#123cff'}"/>`;
 }).join('');
 return `<svg class="decision-route" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(`${facts.stops.length} ordered stops across ${facts.projects.map(project=>project.label).join(', ')}`)}"><path d="${path}" fill="none" stroke="#123cff" stroke-width="2.2"/>${dots}</svg>`;
};

const styles=`*{box-sizing:border-box}html,body{margin:0;min-height:100%;background:#f7f7f5;color:#111}body{font:14px/1.38 'IBM Plex Sans',system-ui,-apple-system,sans-serif;padding:0 12px 24px}a{color:inherit}main{width:min(100%,390px);margin:0 auto}.brand{display:flex;align-items:center;min-height:46px;color:#123cff;font-size:12px;font-weight:700;letter-spacing:.08em;text-decoration:none}.story{background:#fff;border:1px solid #dfe2e9;border-radius:14px;padding:15px 14px 14px;box-shadow:0 8px 24px rgba(23,35,70,.04)}.preview{margin:-3px 0 8px;color:#687083;font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}.preview strong{color:#123cff}h1{font-size:25px;line-height:1.04;letter-spacing:-.025em;margin:0 0 10px}.goal{margin:0 0 13px;color:#363b46;font-size:13px}.label{display:block;color:#123cff;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px}.route-wrap{border-top:1px solid #edf0f5;border-bottom:1px solid #edf0f5;padding:9px 0 8px}.decision-route{display:block;width:100%;height:auto}.lanes{display:flex;flex-wrap:wrap;gap:2px 11px;margin-top:2px;color:#4c5361;font-size:10px}.lanes b{color:#123cff;margin-right:3px}.decision{margin:12px 0 0;border-left:3px solid #123cff;padding:0 0 0 10px}.decision h2{font-size:18px;line-height:1.14;margin:0}.because{margin:5px 0 0;color:#596174;font-size:11px}.evidence{margin-top:12px}.evidence-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px}.evidence-head h2{font-size:13px;margin:0}.measured{color:#596174;font-size:10px}.receipts{list-style:none;padding:0;margin:6px 0 0;display:grid;gap:5px}.receipts li{display:grid;grid-template-columns:auto 1fr;gap:7px;font-size:11px;line-height:1.25}.receipt-mark{color:#123cff;font-weight:700;text-transform:uppercase}.receipt-copy strong{display:block;font-size:12px}.receipt-copy span{color:#687083}.finish{margin:7px 0 0;color:#111;font-size:11px}.action{display:block;background:#123cff;color:#fff;text-align:center;text-decoration:none;font-weight:600;border-radius:5px;padding:11px 12px;margin-top:13px}.boundary{color:#687083;text-align:center;font-size:9px;margin:5px 5px 0}.story a:focus-visible,.brand:focus-visible{outline:3px solid #7b96ff;outline-offset:3px}.neutral{padding:22px}.neutral h1{font-size:22px}.neutral p{color:#596174}@media(min-width:600px){body{padding-top:8px}}`;
const head=(title,description,canonical)=>`<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} · ${BRAND}</title><meta name="description" content="${esc(description)}"><meta property="og:type" content="article"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}"><meta property="og:url" content="${esc(canonical)}"><link rel="canonical" href="${esc(canonical)}"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght%40400;500;600;700&display=swap" rel="stylesheet"><style>${styles}</style>`;

export function decisionHtml(run,options={}){
 const facts=routeFacts(run?.code_route);
 if(!run||!validId(run.id)||!facts)throw new Error('Decision story requires a valid measured Code Route');
 const pageOrigin=options.origin||defaultOrigin;
 const canonical=`${pageOrigin}/d/${encodeURIComponent(run.id)}`;
 const dense=facts.dense;
 const finishProject=facts.finishProject;
 const decision=dense&&finishProject&&dense.id!==finishProject.id
  ?`Carry the work beyond ${dense.label} to ${finishProject.label}.`
  :'Carry the measured route through to its recorded finish.';
 const insight=[
  dense?`${dense.label} held ${facts.denseCount} of ${facts.stops.length} stops`:null,
  facts.handoffs.length?`${facts.handoffs.length} handoffs carried it onward`:null,
  facts.measured.length===facts.stops.length?'every stop was measured':null,
 ].filter(Boolean).join(' · ')+'.';
 const chosen=['strive-live','fleet-fail',facts.finish?.id].filter((id,index,all)=>id&&all.indexOf(id)===index)
  .map(id=>facts.stops.find(stop=>stop.id===id)).filter(Boolean);
 const receipts=chosen.map(stop=>`<li><span class="receipt-mark">${esc(stop.kind)}</span><span class="receipt-copy"><strong>${esc(stop.label)}</strong>${stopEvidence(stop)?`<span>${esc(stopEvidence(stop))}</span>`:''}</span></li>`).join('');
 const lanes=facts.projects.map((project,index)=>`<span><b>${index+1}</b>${esc(project.label)}</span>`).join('');
 // The public runs query already carries the title. Keep preview and cold public render identical
 // instead of relying on the fixture-only note.
 const goal=run.title;
 const action=actionUrl(run.id,canonical,facts.finish);
 const description=`${decision} ${insight}`;
 return `<!doctype html><html lang="en"><head>${head(run.title,description,canonical)}</head><body><main><a class="brand" href="/" aria-label="${BRAND} home">${BRAND} · decision story</a><article class="story">${options.preview?`<p class="preview"><strong>Local preview</strong> of ${esc(run.id.slice(0,8))} · not a public run</p>`:''}<h1>${esc(run.title)}</h1><p class="goal"><span class="label">Human goal</span>${esc(goal)}</p><div class="route-wrap">${routePlot(facts)}<div class="lanes">${lanes}</div></div><section class="decision"><span class="label">Agent decision that changed the route</span><h2>${esc(decision)}</h2><p class="because">${esc(insight)}</p></section><section class="evidence"><div class="evidence-head"><h2>Evidence on this route</h2><span class="measured">${facts.measured.length}/${facts.stops.length} measured stops</span></div><ul class="receipts">${receipts}</ul><p class="finish">Finish · <strong>${esc(facts.finish?.label||'Recorded finish')}</strong></p></section><a class="action" href="${esc(action)}" rel="noopener noreferrer">Challenge the fleet handoff</a><p class="boundary">Opens a prefilled agentgrinder-public issue draft. GitHub sign-in is required to post; opening it posts nothing.</p></article></main></body></html>`;
}

export function neutralDecisionHtml(id,options={}){
 const pageOrigin=options.origin||defaultOrigin;
 const canonical=`${pageOrigin}/d/${encodeURIComponent(id)}`;
 const title='This decision story is not public';
 const description='The run owner must make the run Public before strangers can read its decision story.';
 return `<!doctype html><html lang="en"><head>${head(title,description,canonical)}<meta name="robots" content="noindex"></head><body><main><a class="brand" href="/">${BRAND} · decision story</a><article class="story neutral"><h1>${title}</h1><p>${description}</p><a class="action" href="/r/${encodeURIComponent(id)}">Open the run link</a></article></main></body></html>`;
}

export {routeFacts};
