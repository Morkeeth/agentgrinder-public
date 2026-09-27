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
 if(validRoute(run.route))support.push({source:'runs.route',value:new Set(run.route).size,text:new Set(run.route).size+' regions in touch order · runs.route'});
 if(run.is_ship===true)support.push({source:'runs.is_ship',value:true,text:'Marked shipped · runs.is_ship'});
 if(Number.isSafeInteger(run.commits)&&run.commits>=0)support.push({source:'runs.commits',value:run.commits,text:run.commits+' commits recorded · runs.commits'});
 if(source==='runs.coach_verdict'&&Number.isSafeInteger(run.coach_tool_calls)&&run.coach_tool_calls>=0)support.push({source:'runs.coach_tool_calls',value:run.coach_tool_calls,text:run.coach_tool_calls+' coach tool calls · runs.coach_tool_calls'});
 return{surface,label,outcome,outcomeSource:source,sourceLine:source?'Evidence source: '+source:'Evidence source: none stored for this view',support,limit:LIMITS[source||'none'],duration:duration(run.duration_s),durationSource:typeof run.duration_s==='number'?'runs.duration_s':null};
}
function guard(lead,run){
 const expected=present(run,lead&&lead.surface);
 for(const key of ['label','outcome','outcomeSource','sourceLine','limit','duration','durationSource'])if(lead?.[key]!==expected[key])throw new Error('result source guard: '+key+' changed');
 if(JSON.stringify(lead.support)!==JSON.stringify(expected.support))throw new Error('result source guard: support changed');
 return lead;
}
function esc(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function html(lead,escape){
 const e=escape||esc,outcome=lead.outcome?e(lead.outcome):'No result account is stored for this view.';
 const support=(lead.support||[]).map(row=>'<p data-result-claim data-source="'+e(row.source)+'">'+e(row.text)+'</p>').join('');
 return '<section class="result-lead" data-result-lead><p class="result-label">'+e(lead.label)+'</p><p class="result-outcome" data-result-claim data-source="'+e(lead.outcomeSource||'none')+'">'+outcome+'</p><p class="result-source" data-result-claim data-source="'+e(lead.outcomeSource||'none')+'">'+e(lead.sourceLine)+'</p>'+support+'<p class="result-limit" data-result-claim data-source="limit"><strong>Limit:</strong> '+e(lead.limit)+'</p><p class="result-duration" data-result-claim data-source="'+e(lead.durationSource||'runs.duration_s')+'"><span>Session time</span><strong>'+(lead.duration?e(lead.duration):'Unknown')+'</strong></p></section>';
}
const api={redact,formatDuration:duration,present,guard,html};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.GrinderResultLead=api;
})(typeof globalThis!=='undefined'?globalThis:this);
