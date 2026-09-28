/* Result-first presentation. Every visible claim is copied from one stored field,
   then checked against the same run before it can render. */
(function(root){
'use strict';
function redact(value){
 return String(value??'').split('\n').map(line=>line.split(/\s+/).map(raw=>{
  if(!raw)return raw;
  const parts=raw.match(/^([,.;:()[\]{}'"`]*)(.*?)([,.;:()[\]{}'"`]*)$/),token=parts?parts[2]:raw;
  if(token.startsWith('/')||token.startsWith('~')||token.includes('\\')||token.includes('/')||/^[A-Za-z]:/.test(token))return(parts?parts[1]:'')+'[file]'+(parts?parts[3]:'');
  return raw;
 }).join(' ')).join('\n');
}
function duration(seconds){
 if(typeof seconds!=='number'||!Number.isFinite(seconds)||seconds<0)return null;
 const minutes=Math.round(seconds/60);
 return minutes>=60?Math.floor(minutes/60)+'h '+minutes%60+'m':minutes+'m';
}
function durationFact(run){
 const ridgeWall=run.ridge_basis==='wall-time'&&typeof run.ridge_wall_seconds==='number'?run.ridge_wall_seconds:null;
 const wall=typeof run.wall_time_s==='number'?run.wall_time_s:ridgeWall;
 if(typeof wall==='number'&&Number.isFinite(wall)&&wall>=0){
  return{label:'Elapsed',value:duration(wall),source:typeof run.wall_time_s==='number'?'runs.wall_time_s':'runs.ridge_wall_seconds',basis:'wall clock',window:windowLabel(run)};
 }
 if(typeof run.duration_s==='number'&&Number.isFinite(run.duration_s)&&run.duration_s>=0){
  const recorded=['elapsed','elapsed-agent-tool-calls'].includes(run.trace_basis);
  return{label:recorded?'Recorded time':'Duration · basis unknown',value:duration(run.duration_s),source:'runs.duration_s',basis:recorded?'elapsed trace':'unknown trace basis',window:windowLabel(run)};
 }
  return{label:'Duration',value:null,source:null,basis:'not stored',window:'not stored'};
}
function windowLabel(run){
 const raw=typeof run.started_at==='string'?run.started_at:(typeof run.started==='string'?run.started:null);
 if(!raw||Number.isNaN(Date.parse(raw)))return'run boundary not stored';
 return 'run starting '+new Date(raw).toISOString();
}
function sourceMeta(source,run){
 const window=windowLabel(run);
 if(source==='runs.coach_verdict')return{basis:'stored coach report',window};
 if(source==='runs.note')return{basis:'builder-authored account',window};
 if(source==='runs.route')return{basis:'captured touch order',window};
 if(source==='runs.is_ship')return{basis:'stored ship flag',window};
 if(source==='runs.commits')return{basis:'stored run count',window};
 if(source==='runs.coach_tool_calls')return{basis:'stored coach count',window};
 return{basis:'not stored',window:'not stored'};
}
const LIMITS={
 'runs.coach_verdict':'Stored coach report. It does not independently verify result quality. Counts are activity, not a result.',
 'runs.note':'Builder-authored account. It is not checked against the route or commits. Counts are activity, not result quality.',
 none:'No result account is stored for this view. Duration and counts are activity, not result quality.'
};
function validRoute(route){return Array.isArray(route)&&route.length>0&&route.length<=10000&&route.every(n=>Number.isInteger(n)&&n>=0)}
function present(run,surface){
 if(!run||typeof run!=='object'||Array.isArray(run))throw new Error('missing run');
 if(!['view','og','share'].includes(surface))throw new Error('unknown surface');
 const verdict=typeof run.coach_verdict==='string'?run.coach_verdict.trim():'';
 const note=typeof run.note==='string'?run.note.trim():'';
 const noteAllowed=surface==='view'||surface==='og'||(surface==='share'&&run.visibility==='public');
 let outcome=null,source=null,label='Outcome not recorded';
 if(verdict){outcome=redact(verdict);source='runs.coach_verdict';label='Observed outcome'}
 else if(note&&noteAllowed){outcome=redact(note);source='runs.note';label='Builder’s account'}
 const support=[];
 const add=(field,value,text)=>support.push({source:field,value,text,...sourceMeta(field,run)});
 if(validRoute(run.route))add('runs.route',new Set(run.route).size,new Set(run.route).size+' regions in touch order · runs.route');
 if(run.is_ship===true)add('runs.is_ship',true,'Marked shipped · runs.is_ship');
 if(Number.isSafeInteger(run.commits)&&run.commits>=0)add('runs.commits',run.commits,run.commits+' commits recorded · runs.commits');
 if(source==='runs.coach_verdict'&&Number.isSafeInteger(run.coach_tool_calls)&&run.coach_tool_calls>=0)add('runs.coach_tool_calls',run.coach_tool_calls,run.coach_tool_calls+' coach tool calls · runs.coach_tool_calls');
 const timing=durationFact(run);
 const outcomeMeta=source?sourceMeta(source,run):{basis:'not stored',window:'not stored'};
 const sourceLine=source
  ?'Evidence: '+source+' · basis: '+outcomeMeta.basis+' · window: '+outcomeMeta.window
  :'Evidence: no stored result account · basis: not stored · window: not stored';
 return{surface,label,outcome,outcomeSource:source,sourceLine,support,limit:LIMITS[source||'none'],duration:timing.value,durationLabel:timing.label,durationSource:timing.source,durationBasis:timing.basis||'not stored',durationWindow:timing.window||windowLabel(run)};
}
function guard(lead,run){
 const expected=present(run,lead&&lead.surface);
 for(const key of ['label','outcome','outcomeSource','sourceLine','limit','duration','durationLabel','durationSource','durationBasis','durationWindow'])if(lead?.[key]!==expected[key])throw new Error('result source guard: '+key+' changed');
 if(JSON.stringify(lead.support)!==JSON.stringify(expected.support))throw new Error('result source guard: support changed');
 return lead;
}
function esc(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function html(lead,escape){
 const e=escape||esc;
 const support=(lead.support||[]).slice(0,3).map(row=>'<li data-result-claim data-source="'+e(row.source)+'">'+e(row.text)+'<span class="result-basis">Source: '+e(row.source)+' · basis: '+e(row.basis)+' · window: '+e(row.window)+'</span></li>').join('');
 const duration=lead.duration?'<p class="result-duration" data-result-claim data-source="'+e(lead.durationSource||'none')+'"><span>'+e(lead.durationLabel||'Duration')+'</span><strong>'+e(lead.duration)+'</strong><small class="result-basis">Source: '+e(lead.durationSource||'none')+' · basis: '+e(lead.durationBasis)+' · window: '+e(lead.durationWindow)+'</small></p>':'';
 return '<details class="result-evidence" data-result-lead><summary>How this card was made</summary><div><p class="result-source" data-result-claim data-source="'+e(lead.outcomeSource||'none')+'">'+e(lead.sourceLine)+'</p>'+(support?'<ul>'+support+'</ul>':'')+duration+'<p class="result-limit" data-result-claim data-source="limit">'+e(lead.limit)+'</p></div></details>';
}
const api={redact,formatDuration:duration,durationFact,windowLabel,sourceMeta,present,guard,html};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.GrinderResultLead=api;
})(typeof globalThis!=='undefined'?globalThis:this);
