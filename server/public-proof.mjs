import {BRAND} from './brand.mjs';

// Keep this renderer independently testable on the supported local Node version. The API still
// obtains rows exclusively through public-run.readPublic(), which is the access boundary.
const defaultOrigin=process.env.AGENTGRINDER_ORIGIN||'https://agentic-strava.vercel.app';
const validId=id=>typeof id==='string'&&/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(id);

const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const safeUrl=value=>typeof value==='string'&&/^https:\/\/[^\s<>"']{1,300}$/i.test(value);

export function proofFacts(route){
 if(!route||route.v!==1||route.unavailable||!Array.isArray(route.projects)||!Array.isArray(route.stops))return null;
 const projects=route.projects.filter(project=>project&&typeof project.id==='string'&&typeof project.label==='string'&&project.label.trim());
 const projectIds=new Set(projects.map(project=>project.id));
 const stops=route.stops.filter(stop=>stop&&typeof stop.id==='string'&&projectIds.has(stop.project)&&typeof stop.label==='string'&&stop.label.trim());
 if(!projects.length||!stops.length)return null;
 const measured=stops.filter(stop=>stop.basis==='measured');
 return {projects,stops,measured};
}

const styles=`*{box-sizing:border-box}html,body{margin:0;background:#f7f7f5;color:#101321}body{font:15px/1.45 'IBM Plex Sans',system-ui,-apple-system,sans-serif;padding:0 12px 28px}main{width:min(100%,540px);margin:0 auto}.brand{display:flex;align-items:center;min-height:54px;color:#123cff;font-size:12px;font-weight:700;letter-spacing:.08em;text-decoration:none}.story{background:#fff;border:1px solid #dde2ee;border-radius:15px;padding:18px 16px;box-shadow:0 10px 28px rgba(23,35,70,.05)}h1{font-size:27px;line-height:1.06;letter-spacing:-.03em;margin:0 0 10px}.summary{color:#424a5a;margin:0}.label{display:block;color:#123cff;font-size:10px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px}.route{display:grid;grid-template-columns:repeat(var(--lanes),1fr);gap:4px;margin:17px 0 0}.lane{min-width:0;border-top:3px solid #123cff;padding:6px 3px 0;color:#4b5463;font-size:11px;overflow-wrap:anywhere}.lane:first-child{border-color:#ff6a2a}.facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin:16px 0}.fact{border:1px solid #e4e8f0;border-radius:8px;padding:8px}.fact b{display:block;font-size:21px;line-height:1.05}.fact span{color:#5d6676;font-size:11px}.section{border-top:1px solid #e8ebf1;padding-top:14px;margin-top:14px}.section h2{font-size:15px;margin:0 0 7px}.section p{color:#5d6676;font-size:12px;margin:0 0 8px}.checkpoints,.outcomes,.receipts{list-style:none;padding:0;margin:0;display:grid;gap:7px}.checkpoints li{display:grid;grid-template-columns:18px 1fr;gap:7px;font-size:13px}.mark{color:#123cff;font-weight:700}.basis{color:#687286;font-size:11px}.outcomes li{font-size:13px;padding-left:12px;position:relative}.outcomes li:before{content:'↗';position:absolute;left:0;color:#ff6a2a}.receipts a{color:#123cff;font-size:13px;overflow-wrap:anywhere}.open{display:block;margin-top:17px;background:#123cff;color:#fff;border-radius:6px;padding:12px;text-align:center;font-weight:700;text-decoration:none}.boundary{margin:7px 0 0;text-align:center;color:#687286;font-size:10px}.neutral{padding:24px}.neutral h1{font-size:23px}.neutral p{color:#596174}@media(min-width:600px){body{padding-top:8px}}`;
const head=(title,description,canonical)=>`<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} · ${BRAND}</title><meta name="description" content="${esc(description)}"><meta property="og:type" content="article"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}"><meta property="og:url" content="${esc(canonical)}"><link rel="canonical" href="${esc(canonical)}"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"><style>${styles}</style>`;

export function proofHtml(run,options={}){
 const facts=proofFacts(run?.code_route);
 if(!run||!validId(run.id)||!facts)throw new Error('Public proof requires a valid measured Code Route');
 const origin=options.origin||defaultOrigin;
 const canonical=`${origin}/proof/${encodeURIComponent(run.id)}`;
 const title=String(run.title||'A recorded STRIVE run').trim().slice(0,160)||'A recorded STRIVE run';
 const measured=`${facts.measured.length}/${facts.stops.length} checkpoints are recorded as measured`;
 const route=facts.projects.map(project=>`<div class="lane">${esc(project.label)}</div>`).join('');
 const checkpoints=facts.stops.map(stop=>`<li><span class="mark">${stop.basis==='measured'?'●':'○'}</span><span>${esc(stop.label)} <span class="basis">${esc(stop.basis||'recorded')}</span></span></li>`).join('');
 const outcomes=(Array.isArray(run.shipped)?run.shipped:[]).filter(value=>typeof value==='string'&&value.trim()).slice(0,5)
  .map(value=>`<li>${esc(value.trim().slice(0,160))}</li>`).join('');
 const receipts=(Array.isArray(run.receipts)?run.receipts:[]).filter(receipt=>receipt&&safeUrl(receipt.url)&&typeof receipt.label==='string'&&receipt.label.trim()).slice(0,5)
  .map(receipt=>`<li><a href="${esc(receipt.url)}" rel="noopener noreferrer nofollow">${esc(receipt.label.trim().slice(0,100))} ↗</a></li>`).join('');
 const description=`${facts.projects.length} projects, ${facts.stops.length} recorded checkpoints. ${measured}.`;
 return `<!doctype html><html lang="en"><head>${head(title,description,canonical)}</head><body><main><a class="brand" href="/" aria-label="${BRAND} home">${BRAND} · public proof</a><article class="story"><span class="label">Recorded agent run</span><h1>${esc(title)}</h1><p class="summary">A public route across ${facts.projects.length} projects. ${esc(measured)}.</p><div class="route" style="--lanes:${facts.projects.length}">${route}</div><div class="facts"><div class="fact"><b>${facts.projects.length}</b><span>projects</span></div><div class="fact"><b>${facts.stops.length}</b><span>recorded checkpoints</span></div></div><section class="section"><span class="label">Route evidence</span><h2>What was recorded</h2><ul class="checkpoints">${checkpoints}</ul></section>${outcomes?`<section class="section"><span class="label">Author-reported outcomes</span><h2>What the author says changed</h2><ul class="outcomes">${outcomes}</ul></section>`:''}${receipts?`<section class="section"><span class="label">Linked receipts</span><h2>Open the underlying work</h2><ul class="receipts">${receipts}</ul></section>`:''}<a class="open" href="/r/${encodeURIComponent(run.id)}">Open the public run</a><p class="boundary">The route is recorded activity. Author-reported outcomes are labelled separately.</p></article></main></body></html>`;
}

export function neutralProofHtml(id,options={}){
 const origin=options.origin||defaultOrigin;
 const canonical=`${origin}/proof/${encodeURIComponent(id||'')}`;
 const title='This public proof is unavailable';
 const description='A STRIVE proof appears only when its underlying run is Public.';
 return `<!doctype html><html lang="en"><head>${head(title,description,canonical)}<meta name="robots" content="noindex"></head><body><main><a class="brand" href="/">${BRAND} · public proof</a><article class="story neutral"><h1>${title}</h1><p>${description}</p></article></main></body></html>`;
}
