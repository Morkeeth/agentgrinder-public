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
function metricStrip(run){
 return [
  ['Session',duration(sessionSeconds(run))],
  ['Turns',run.prompts??run.turns_typed??null],
  ['Tool calls',run.tool_calls??null],
 ].map(([label,value])=>[label,value==null?'Unknown':String(value)]);
}
function projectName(run){
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
 if(!facts.length&&run.tool_calls!=null)facts.push(run.tool_calls+' tool calls');
 return facts;
}
function storyFacts(run){
 return {project:projectName(run)||'Unknown',output:outputKind(run),code:codeFacts(run).join(' · ')||'Unknown'};
}
function mount({run,slot,status,moment=null,review=null}){
 if(moment&&(moment.run_id!==run.id||moment.measurement_revision!==run.measurement_revision)){
  slot.innerHTML='<p>This moment belongs to a different measurement. Return to the grind and choose a current moment before making a card.</p>';return;
 }
 const readable=['public','link'].includes(run.visibility), handle=run.profiles?.github_handle;
 const url=moment?location.origin+'/?run='+encodeURIComponent(run.id)+'&moment='+encodeURIComponent(moment.id):location.origin+(run.visibility==='public'?'/r/':'/?run=')+encodeURIComponent(run.id);
 slot.innerHTML=`<div class="head"><h2>${review?"Share my outcome":"Share your run"}</h2>${review?"":`<a href="/?run=${encodeURIComponent(run.id)}">Back to run</a>`}</div>
 <p class="hint">${readable?(run.visibility==='public'?'Public run · anyone can read it.':'Link-only run · anyone with the link can read it.'):'Private run · exporting an image does not change who can read the run.'}</p>
 <div class="share-studio"><form id="post-editor" class="panel reply-form">
 <label>What did you build?<input name="title" maxlength="100" required value="${esc(run.title)}"></label>
 <label>Where did the agent help or struggle?<textarea name="contribution" maxlength="240" placeholder="Describe one useful contribution or difficult moment."></textarea></label>
 <label>What was the result?<textarea name="result" maxlength="240" placeholder="Describe what you checked. Keep claims specific.">${esc(run.caption||'')}</textarea></label>
 <label>What will you try next?<input name="next" maxlength="160" placeholder="One change for the next run"></label>
 <label>Image format<select name="format"><option value="square">Square · 1080 × 1080</option><option value="portrait">Portrait · 1080 × 1350</option></select></label>
 <label><input type="checkbox" name="identity" ${handle?'checked':''}> Include public handle and agent name</label>
 <p class="hint">The image uses your title and result, a safe output label, the proven project name, measured code activity, the blue trace, and effort counts. It never includes command text, paths, code, prompts, secrets, or tool output.</p>
 <label><input type="checkbox" name="review"> I have reviewed this image and caption for sharing.</label>
 <div class="cta"><button type="button" id="post-download" disabled>Download PNG</button><button type="button" class="ghost" id="post-copy" disabled>Copy caption</button></div>
 </form><div class="post-preview"><canvas aria-label="Exact share image preview" role="img"></canvas><label>Caption<textarea id="post-caption" readonly rows="8"></textarea></label><p class="hint" id="post-message" role="status"></p></div></div>`;
 const form=slot.querySelector('form'),canvas=slot.querySelector('canvas'),ctx=canvas.getContext('2d');
 const fields=()=>({title:form.elements.title.value.trim(),contribution:form.elements.contribution.value.trim(),result:form.elements.result.value.trim(),next:form.elements.next.value.trim(),identity:form.elements.identity.checked});
 function lines(text,x,y,width,font,lineHeight,maxLines){ctx.font=font;let words=String(text).split(/\s+/),line='',rows=[];for(const word of words){const candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width>width&&line){rows.push(line);line=word}else line=candidate;}if(line)rows.push(line);rows=rows.flatMap(row=>{if(ctx.measureText(row).width<=width)return[row];const parts=[];let part='';for(const c of row){if(ctx.measureText(part+c).width>width){parts.push(part);part=''}part+=c}if(part)parts.push(part);return parts});const clipped=rows.length>maxLines;rows=rows.slice(0,maxLines);if(clipped){let last=rows.at(-1);while(last&&ctx.measureText(last+'…').width>width)last=last.slice(0,-1);rows[rows.length-1]=last+'…'}rows.forEach((row,i)=>ctx.fillText(row,x,y+i*lineHeight));return clipped;}
 function draw(){const f=fields(),portrait=form.elements.format.value==='portrait';canvas.width=1080;canvas.height=portrait?1350:1080;let clipped=false;ctx.fillStyle='#f8f8f6';ctx.fillRect(0,0,1080,canvas.height);ctx.fillStyle='#123cff';ctx.fillRect(64,64,44,8);ctx.fillStyle='#111';ctx.font='600 23px sans-serif';ctx.fillText('__BRAND__',128,80);ctx.fillStyle='#666';ctx.font='20px sans-serif';ctx.fillText(review?'MY RETURN':'RUN NOTES',820,80);
 ctx.fillStyle='#123cff';ctx.font='600 16px sans-serif';ctx.fillText('ACHIEVED',64,124);
 ctx.fillStyle='#111';clipped=lines(f.title||'Your run',64,172,952,'600 46px sans-serif',54,2)||clipped;
 ctx.fillStyle='#444';clipped=lines(f.result||'Achievement caption unknown',64,275,952,'24px sans-serif',31,2)||clipped;
 ctx.fillStyle='#666';const identity=f.identity&&handle?'@'+handle:'Identity not included';clipped=lines(identity+' · '+(run.harness||'Harness unknown')+(f.identity&&run.agent_name?' · '+run.agent_name:''),64,330,952,'19px sans-serif',24,1)||clipped;
 const facts=storyFacts(run),story=[['PROJECT TOUCHED',facts.project],['CODE ACTIVITY',facts.code],['OUTPUT',facts.output]].filter(([,value])=>value);story.forEach(([label,value],i)=>{const x=64+i*317;ctx.fillStyle='#666';ctx.font='15px sans-serif';ctx.fillText(label,x,378);ctx.fillStyle=value==='Unknown'?'#666':'#111';ctx.font=value==='Unknown'?'19px sans-serif':'600 20px sans-serif';clipped=lines(value,x,408,285,'600 20px sans-serif',24,1)||clipped;});
 const values=run.rhythm;ctx.strokeStyle='#123cff';ctx.lineWidth=4;const valid=Array.isArray(values)&&values.length>1&&values.length<=10000&&values.every(v=>Number.isFinite(v)&&v>=0);if(valid){const max=Math.max(...values)||1;ctx.beginPath();values.forEach((v,i)=>{const x=64+i/(values.length-1)*952,y=560-v/max*105;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke()}else{ctx.fillStyle='#666';ctx.font='24px sans-serif';ctx.fillText('Trace unavailable',64,520)}
 ctx.fillStyle='#666';ctx.font='17px sans-serif';ctx.fillText(run.trace_basis==='elapsed-agent-tool-calls'?'Agent tool requests · elapsed time':run.trace_basis==='elapsed'?'Session activity · elapsed time':run.trace_basis==='position'?'Session activity · event order':'Session activity · time basis unknown',64,592);
 ctx.fillStyle='#123cff';ctx.font='600 16px sans-serif';ctx.fillText('EFFORT',64,632);
 metricStrip(run).forEach(([name,value],i)=>{const x=64+i*317;ctx.fillStyle='#666';ctx.font='17px sans-serif';ctx.fillText(name,x,663);ctx.fillStyle=value==='Unknown'?'#666':'#111';ctx.font=value==='Unknown'?'22px sans-serif':'600 31px sans-serif';ctx.fillText(value,x,705)});
 let y=770;const blocks=[['THE AGENT',f.contribution],['NEXT RUN',f.next]].filter(([,v])=>v);for(const [label,body] of blocks){ctx.fillStyle='#123cff';ctx.font='600 17px sans-serif';ctx.fillText(label,64,y);ctx.fillStyle='#111';clipped=lines(body,64,y+34,952,'26px sans-serif',32,portrait?3:2)||clipped;y+=portrait?160:110;}
 ctx.strokeStyle='#ddd';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(64,canvas.height-65);ctx.lineTo(1016,canvas.height-65);ctx.stroke();ctx.fillStyle='#666';ctx.font='18px sans-serif';ctx.fillText(review?'My observation · this does not prove the practice caused the result':'Builder’s account · recorded counts are not independent verification',64,canvas.height-30);
 slot.querySelector('#post-caption').value=[f.title,f.contribution&&'Agent: '+f.contribution,f.result&&'Result: '+f.result,f.next&&'Next run: '+f.next,review?'My observation, not proof the practice caused the result.':readable?url:''].filter(Boolean).join('\n\n');
 slot.querySelector('#post-message').textContent=clipped?'Some text is shortened in the image. Shorten your text or choose portrait. Moment and review exports require the complete text to fit; the caption keeps the full text.':'';
 const ready=form.elements.review.checked&&!!f.title&&(!(moment||review)||!clipped)&&(!review||!!f.result);slot.querySelector('#post-download').disabled=!ready;slot.querySelector('#post-copy').disabled=!ready;
 }
 form.addEventListener('input',e=>{if(e.target.name!=='review')form.elements.review.checked=false;draw()});form.addEventListener('submit',e=>e.preventDefault());
 slot.querySelector('#post-copy').onclick=async()=>{try{await navigator.clipboard.writeText(slot.querySelector('#post-caption').value);status('Caption copied.')}catch(_){status('Select and copy the caption below the image.')}};
 slot.querySelector('#post-download').onclick=()=>canvas.toBlob(blob=>{if(!blob){status('Image export failed. Try again.');return}const link=document.createElement('a'),object=URL.createObjectURL(blob);link.href=object;link.download='run-card-'+run.id+'-'+form.elements.format.value+'.png';link.click();setTimeout(()=>URL.revokeObjectURL(object),1000)},'image/png');
 if(moment){
  form.elements.title.value=moment.title;
  form.elements.result.value=moment.claim+' Limit: '+moment.limitation;
  form.elements.contribution.value='Builder-authored observation'+(moment.measurement_revision!==run.measurement_revision?' · earlier measurement, current run changed':'')+'. Not independently verified.';
  form.elements.next.value=moment.next_action;
  const context=document.createElement('p');context.className='hint';context.textContent='Moment selected. The full excerpt stays on the run; the card includes your claim and its limit. Review all text before exporting.';form.prepend(context);
 }
 if(review){
  form.elements.contribution.value='My decision: '+review.decision+'. Tried the practice: '+(review.tried===true?'yes':review.tried===false?'no':'unknown')+'.';
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
root.GrinderSharing={mount,reviewExport,mountReview,metricStrip,storyFacts};
})(window);
