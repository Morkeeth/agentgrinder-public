/* The preview and downloaded PNG use the same canvas and explicit share fields. */
(function(root){
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function sessionSeconds(run){
 const values=[run.ridge_basis==='wall-time'?run.ridge_wall_seconds:null,run.wall_time_s,run.duration_s];
 const value=values.find(v=>typeof v==='number'&&Number.isFinite(v)&&v>=0);
 return value==null?null:value;
}
function duration(value){
 if(value==null)return'Unknown';
 if(value<60)return Math.round(value)+'s';
 const minutes=Math.round(value/60);
 return minutes>=60?Math.floor(minutes/60)+'h '+minutes%60+'m':minutes+'m';
}
function contractApi(){
 return (typeof GrinderContract==='object'&&GrinderContract)||root.GrinderContract||null;
}
function metricStrip(run){
 const contract=contractApi();
 if(contract&&contract.heroStats){
  return contract.heroStats(run);
 }
 const tools=contract&&contract.toolCallCount
  ?contract.toolCallCount(run):(run.tool_calls??null);
 const cells=[
  ['Session',sessionSeconds(run)==null?null:duration(sessionSeconds(run))],
  ['Turns',run.prompts??run.turns_typed??null],
  ['Tool calls',tools],
 ].filter(([,value])=>value!=null);
 return cells.map(([label,value])=>[label,String(value)]);
}
function whole(value){
 if(value==null||value==='')return null;
 const number=Number(value);
 return Number.isSafeInteger(number)&&number>=0?number:null;
}
function shareFacts(run){
 const facts=[];
 const add=(label,value)=>{if(value!=null&&facts.length<3)facts.push([label,String(value)]);};
 const checks=whole(run.checks_passed),checkLabel=typeof run.check_label==='string'?run.check_label.trim():'';
 const commits=whole(run.commits),files=whole(run.files_changed);
 if(checks!=null&&checkLabel)add(checkLabel,checks+' passed');
 else if(commits>0)add(commits===1?'commit':'commits',commits);
 else if(files>0)add(files===1?'file changed':'files changed',files);
 const wall=whole(run.wall_time_s)??(run.ridge_basis==='wall-time'?whole(run.ridge_wall_seconds):null);
 if(wall!=null)add('Elapsed',duration(wall));
 else{const recorded=whole(run.duration_s);if(recorded!=null)add('Recorded time',duration(recorded));}
 const prompts=whole(run.prompts??run.turns_typed);
 if(prompts!=null)add('Your prompts',prompts);
 return facts;
}
function dateLabel(run){
 const raw=run.started_at||run.created_at||run.started;
 if(!raw)return'';
 const date=new Date(raw);
 return Number.isNaN(date.getTime())?'':date.toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'});
}
function workLabel(run){
 try{
  const url=new URL(run.output_url);
  if(url.protocol!=='https:')return null;
  const label=/github\.com\/[^/]+\/[^/]+\/pull\/\d+/i.test(url.href)?'View pull request':'Open work';
  return {label,host:url.hostname.replace(/^www\./,'')};
 }catch(_){return null}
}
function projectName(run){
 // One rule for the label a reader sees (site/run-contract.js projectLabel): it also takes the
 // home directory out of a flattened workspace name.
 const contract=(typeof globalThis!=='undefined'&&globalThis.GrinderContract)||null;
 if(contract&&typeof contract.projectLabel==='function')return contract.projectLabel(run.project);
 const value=typeof run.project==='string'?run.project.trim():'';
 return value&&!['session','unknown','project unknown'].includes(value.toLowerCase())?value:null;
}
function outputKind(run){
 try{
  const url=new URL(run.output_url);
  if(!/^https?:$/.test(url.protocol))return null;
  if(/github\.com\/[^/]+\/[^/]+\/pull\/\d+/i.test(url.href))return'PR linked';
  if(/\.(png|jpe?g|webp)(?:[?#]|$)/i.test(url.href))return'Screenshot linked';
  return'Output linked';
 }catch(_){return null}
}
function codeFacts(run){
 const facts=[];
 if(run.shell_calls!=null)facts.push(run.shell_calls+' shell calls');
 if(run.files_touched!=null)facts.push(run.files_touched+' files changed');
 if(run.commits!=null)facts.push(run.commits+' commits');
 const contract=contractApi();
 const tools=contract&&contract.toolCallCount
  ?contract.toolCallCount(run):run.tool_calls;
 if(!facts.length&&tools!=null)facts.push(tools+' tool calls');
 return facts;
}
function storyFacts(run){
 const project=projectName(run),code=codeFacts(run).join(' · ');return {project:project||null,output:outputKind(run),code:code||null};
}
function routeInsight(route){
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
}
function ridgeBasisLabel(basis){
 if(basis==='wall-time')return'wall time';
 if(basis==='turn-order')return'turn order';
 if(basis==='call-index')return'call order';
 return'unknown basis';
}
function traceSeries(run){
 const ridge=run.ridge,workers=run.worker_bins;
 if(Array.isArray(ridge)&&ridge.length>=40&&ridge.length<=60
  &&ridge.every(v=>Number.isSafeInteger(v)&&v>=0)
  &&Array.isArray(workers)&&workers.length===ridge.length){
  return {values:ridge,label:'Tool calls over '+ridgeBasisLabel(run.ridge_basis)};
 }
 const rhythm=run.rhythm;
 if(Array.isArray(rhythm)&&rhythm.length>1&&rhythm.length<=10000
  &&rhythm.every(v=>Number.isFinite(v)&&v>=0)){
  const label=run.trace_basis==='elapsed-agent-tool-calls'?'Agent tool requests · elapsed time'
   :run.trace_basis==='elapsed'?'Session activity · elapsed time'
   :run.trace_basis==='position'?'Session activity · event order'
   :'Session activity · time basis unknown';
  return {values:rhythm,label};
 }
 return null;
}
function mount({run,slot,status,moment=null,review=null}){
 if(moment&&(moment.run_id!==run.id||moment.measurement_revision!==run.measurement_revision)){
  slot.innerHTML='<p>This moment belongs to a different measurement. Return to the grind and choose a current moment before making a card.</p>';return;
 }
 const publicShare=run.visibility==='public', handle=run.profiles?.github_handle;
 const shareLead=(!moment&&!review&&typeof GrinderResultLead==='object')?GrinderResultLead.guard(GrinderResultLead.present(run,'share'),run):null;
 const url=moment?location.origin+'/?run='+encodeURIComponent(run.id)+'&moment='+encodeURIComponent(moment.id):location.origin+(publicShare?'/r/':'/?run=')+encodeURIComponent(run.id);
 slot.innerHTML=`<div class="head"><h2>${review?"Share my outcome":"Share your run"}</h2>${review?"":`<a href="/?run=${encodeURIComponent(run.id)}">Back to run</a>`}</div>
 <p class="hint">${publicShare?'Public run · anyone can read it at /r/.':run.visibility==='link'?'Link run · signed-in followers and close friends can open /?run=.':'Private run · exporting an image does not change who can read the run.'}</p>
 <div class="share-studio"><form id="post-editor" class="panel reply-form">
 <label>Title<input name="title" maxlength="100" required value="${esc(run.title)}"></label>
 <label>Caption (optional, copied below the image)<textarea name="result" maxlength="240" placeholder="Add context without changing the stored account.">${esc(run.caption||'')}</textarea></label>
 <label>Image format<select name="format"><option value="square">Square · 1080 × 1080</option><option value="portrait">Portrait · 1080 × 1350</option></select></label>
 <label><input type="checkbox" name="identity" ${handle?'checked':''}> Include public handle and agent name</label>
 <p class="hint">The image is built from this run: title, caption, Code Route when recorded or the blue activity trace, and measured facts. It never includes command text, paths, code, prompts, secrets, or tool output.</p>
 <label><input type="checkbox" name="review"> I have reviewed this image and caption for sharing.</label>
 <div class="cta"><button type="button" id="post-download" disabled>Download PNG</button><button type="button" class="ghost" id="post-copy" disabled>Copy caption</button></div>
 </form><div class="post-preview"><canvas aria-label="Exact share image preview" role="img"></canvas><label>Caption<textarea id="post-caption" readonly rows="8"></textarea></label><p class="hint" id="post-message" role="status"></p></div></div>`;
 const form=slot.querySelector('form'),canvas=slot.querySelector('canvas'),ctx=canvas.getContext('2d');
 let contributionText=(()=>{
  const facts=storyFacts(run);
  const bits=[run.harness?String(run.harness)+' session':'Agent session'];
  if(facts.code) bits.push(facts.code);
  if(facts.project) bits.push('project '+facts.project);
  return bits.join(' · ');
 })();
 let nextText='';
 const fields=()=>({title:form.elements.title.value.trim(),contribution:contributionText,result:form.elements.result.value.trim(),next:nextText,identity:form.elements.identity.checked});
 function lines(text,x,y,width,font,lineHeight,maxLines){ctx.font=font;let words=String(text).split(/\s+/),line='',rows=[];for(const word of words){const candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width>width&&line){rows.push(line);line=word}else line=candidate;}if(line)rows.push(line);rows=rows.flatMap(row=>{if(ctx.measureText(row).width<=width)return[row];const parts=[];let part='';for(const c of row){if(ctx.measureText(part+c).width>width){parts.push(part);part=''}part+=c}if(part)parts.push(part);return parts});const clipped=rows.length>maxLines;rows=rows.slice(0,maxLines);if(clipped){let last=rows.at(-1);while(last&&ctx.measureText(last+'…').width>width)last=last.slice(0,-1);rows[rows.length-1]=last+'…'}rows.forEach((row,i)=>ctx.fillText(row,x,y+i*lineHeight));return clipped;}
 function draw(){const f=fields(),portrait=form.elements.format.value==='portrait';canvas.width=1080;canvas.height=portrait?1350:1080;let clipped=false;ctx.fillStyle='#f8f8f6';ctx.fillRect(0,0,1080,canvas.height);
 ctx.fillStyle='#123cff';ctx.fillRect(64,64,38,7);ctx.fillStyle='#111';ctx.font='600 21px sans-serif';ctx.fillText('__BRAND__',118,78);
 const identity=f.identity&&handle?'@'+handle:'Builder',project=projectName(run),when=dateLabel(run);
 ctx.fillStyle='#666';clipped=lines([identity,project,run.harness,when].filter(Boolean).join(' · '),64,126,952,'18px sans-serif',23,1)||clipped;
 const outcome=shareLead?.outcome||f.title||'Outcome not added';ctx.fillStyle='#111';clipped=lines(outcome,64,194,952,'600 44px sans-serif',52,4)||clipped;
 const note=shareLead?.outcome?(f.title&&f.title!==shareLead.outcome?f.title:''):f.result;
 if(note){ctx.fillStyle='#555';clipped=lines(note,64,414,952,'23px sans-serif',30,2)||clipped;}
 const facts=shareFacts(run),factsY=note?494:446;
 facts.forEach(([label,value],i)=>{const x=64+i*317;ctx.fillStyle='#111';clipped=lines(value,x,factsY,285,'600 31px sans-serif',36,1)||clipped;ctx.fillStyle='#666';ctx.font='15px sans-serif';ctx.fillText(label,x,factsY+29);});
 const route=run.code_route&&run.code_route.v===1?run.code_route:null;
 if(route&&!route.unavailable&&Array.isArray(route.projects)&&Array.isArray(route.stops)&&route.projects.length&&route.stops.length){
  const projects=route.projects,stops=route.stops,idx=Object.fromEntries(projects.map((p,i)=>[p.id,i]));
  const left=96,top=factsY+86,rowH=26,width=920;
  ctx.strokeStyle='#123cff';ctx.lineWidth=4;ctx.beginPath();
  stops.forEach((stop,i)=>{const row=idx[stop.project]??0;const x=left+i/Math.max(1,stops.length-1)*width;const y=top+row*rowH+rowH/2;i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();
  stops.forEach((stop,i)=>{const row=idx[stop.project]??0;const x=left+i/Math.max(1,stops.length-1)*width;const y=top+row*rowH+rowH/2;const finish=route.finish&&route.finish.stop===stop.id;ctx.fillStyle=finish?'#111':'#123cff';ctx.beginPath();ctx.arc(x,y,finish?7:4.5,0,Math.PI*2);ctx.fill();});
  ctx.fillStyle='#666';ctx.font='15px sans-serif';projects.forEach((p,i)=>ctx.fillText(String(i+1),64,top+i*rowH+14));
  const projectLine=projects.map((p,i)=>`${i+1} · ${p.label}`).join('   ');clipped=lines(projectLine,64,top+projects.length*rowH+18,952,'16px sans-serif',20,2)||clipped;
  ctx.fillStyle='#111';clipped=lines(routeInsight(route)||'Code Route',64,top+projects.length*rowH+56,952,'600 20px sans-serif',26,2)||clipped;
 }else{
  const trace=traceSeries(run),values=trace?.values,base=factsY+220;ctx.strokeStyle='#123cff';ctx.lineWidth=4;
  if(trace){const max=Math.max(...values)||1;ctx.beginPath();values.forEach((v,i)=>{const x=64+i/(values.length-1)*952,y=base-v/max*120;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();ctx.fillStyle='#666';ctx.font='17px sans-serif';ctx.fillText(trace.label,64,base+34);}
  else{ctx.fillStyle='#666';ctx.font='20px sans-serif';ctx.fillText('No measured visual for this run',64,factsY+130);}
 }
 const work=workLabel(run);if(work){ctx.fillStyle='#123cff';ctx.font='600 18px sans-serif';ctx.fillText(work.label.toUpperCase()+' · '+work.host,64,canvas.height-112);}
 ctx.strokeStyle='#ddd';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(64,canvas.height-65);ctx.lineTo(1016,canvas.height-65);ctx.stroke();ctx.fillStyle='#666';ctx.font='18px sans-serif';ctx.fillText(review?'My observation · this does not prove the practice caused the result':'Builder’s account · measured facts describe this run',64,canvas.height-30);
 slot.querySelector('#post-caption').value=[outcome,f.result&&f.result!==outcome?f.result:null,work&&run.output_url,review?'My observation, not proof the practice caused the result.':(publicShare||run.visibility==='link')?url:''].filter(Boolean).join('\n\n');
 slot.querySelector('#post-message').textContent=clipped?'Some text is shortened in the image. Shorten your text or choose portrait. Moment and review exports require the complete text to fit; the caption keeps the full text.':'';
 const ready=form.elements.review.checked&&!!f.title&&(!(moment||review)||!clipped)&&(!review||!!f.result);slot.querySelector('#post-download').disabled=!ready;slot.querySelector('#post-copy').disabled=!ready;
 }
 form.addEventListener('input',e=>{if(e.target.name!=='review')form.elements.review.checked=false;draw()});form.addEventListener('submit',e=>e.preventDefault());
 slot.querySelector('#post-copy').onclick=async()=>{try{await navigator.clipboard.writeText(slot.querySelector('#post-caption').value);try{if(typeof window.va==='function')window.va('event',{name:'strive_share_copy',data:{kind:'caption'}});}catch(_){ }status('Caption copied.')}catch(_){status('Select and copy the caption below the image.')}};
 slot.querySelector('#post-download').onclick=()=>canvas.toBlob(blob=>{if(!blob){status('Image export failed. Try again.');return}const link=document.createElement('a'),object=URL.createObjectURL(blob);link.href=object;link.download='run-card-'+run.id+'-'+form.elements.format.value+'.png';link.click();setTimeout(()=>URL.revokeObjectURL(object),1000)},'image/png');
 if(moment){
  form.elements.title.value=moment.title;
  form.elements.result.value=moment.claim+' Limit: '+moment.limitation;
  contributionText='Builder-authored observation'+(moment.measurement_revision!==run.measurement_revision?' · earlier measurement, current run changed':'')+'. Not independently verified.';
  nextText=moment.next_action||'';
  const context=document.createElement('p');context.className='hint';context.textContent='Moment selected. The full excerpt stays on the run; the card includes your claim and its limit. Review all text before exporting.';form.prepend(context);
 }
 if(review){
  contributionText='My decision: '+review.decision+'. Tried the practice: '+(review.tried===true?'yes':review.tried===false?'no':'unknown')+'.';
  form.elements.result.required=true;
  const context=document.createElement('p');context.className='hint';context.textContent='Only your frozen outcome counts are included. Missing measurements stay unknown. Write the result you choose to share; your saved reflection, practice text, original author and source links are not copied. This export does not change access to your private attempt.';form.prepend(context);
 }
 draw();return{draw};
}
// Construct an export from an owned, completed attempt using a strict field allowlist.
// Never forward the practice, source moment, saved reflection, or arbitrary snapshot fields.
function reviewExport(attempt,viewerId){
 if(!viewerId||attempt.owner_id!==viewerId||!attempt.reviewed_at||!['keep','change','drop','incomparable'].includes(attempt.decision))return null;
 const outcome=attempt.outcome||{},run={id:'review-'+attempt.id,title:'My practice return',visibility:'private'};
 for(const key of ['harness','turns_typed','artifacts_produced','rhythm','trace_basis'])run[key]=outcome[key]??null;
 return {run,review:{decision:attempt.decision,tried:attempt.tried}};
}
function mountReview({attempt,viewerId,slot,status}){
 const value=reviewExport(attempt,viewerId);
 if(!value){slot.textContent='Only your own saved review can be exported.';return;}
 return mount({...value,slot,status});
}
root.GrinderSharing={mount,reviewExport,mountReview,metricStrip,shareFacts,dateLabel,workLabel,storyFacts,traceSeries};
})(window);
