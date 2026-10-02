(function(root){
  "use strict";
  const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  async function token(client){
    const result=await client?.auth?.getSession?.();
    return result?.data?.session?.access_token||null;
  }
  async function headers(client,json=false){
    const t=await token(client), h={};
    if(t) h.Authorization=`Bearer ${t}`;
    if(json) h["Content-Type"]="application/json";
    return h;
  }
  async function responseMessage(res){
    try{const body=await res.json();return body?.error||body?.message||`Request failed (${res.status})`;}catch(_){return `Request failed (${res.status})`;}
  }
  function photoPath(photo){
    if(typeof photo?.url!=="string")return null;
    try{
      const parsed=new URL(photo.url,location.origin);
      if(parsed.origin!==location.origin||parsed.pathname!=="/api/run-photos"||!parsed.searchParams.get("id")||!parsed.searchParams.get("run_id"))return null;
      return parsed.pathname+parsed.search;
    }catch(_){return null;}
  }
  function cropper(file,host,onReady){
    const url=URL.createObjectURL(file), image=new Image(), state={mode:'original',zoom:1,x:.5,y:.5,ready:false};
    host.innerHTML='<div class="photo-crop"><label>Shape<select data-photo-shape><option value="original">Original</option><option value="square">Square</option><option value="wide">Wide</option></select></label><p class="hint">Original keeps the full photo. Choose Square or Wide to crop it.</p><canvas width="1" height="1" aria-label="Photo preview"></canvas><label>Zoom<input data-photo-zoom type="range" min="1" max="3" value="1" step="0.05"></label><div class="photo-position"><label>Left / right<input data-photo-x type="range" min="0" max="1" value="0.5" step="0.01"></label><label>Up / down<input data-photo-y type="range" min="0" max="1" value="0.5" step="0.01"></label></div><button type="button" data-photo-upload disabled>Add photo</button><button type="button" class="ghost" data-photo-cancel>Cancel</button></div>';
    const canvas=host.querySelector('canvas'), ctx=canvas.getContext('2d');
    const size=()=>{if(state.mode==='square')return [1200,1200];if(state.mode==='wide')return [1600,900];const scale=Math.min(1,1600/Math.max(image.naturalWidth,image.naturalHeight));return [Math.max(1,Math.round(image.naturalWidth*scale)),Math.max(1,Math.round(image.naturalHeight*scale))]};
    const paint=()=>{if(!image.naturalWidth)return;const base=Math.max(canvas.width/image.naturalWidth,canvas.height/image.naturalHeight),scale=base*state.zoom,w=image.naturalWidth*scale,h=image.naturalHeight*scale,maxX=Math.max(0,w-canvas.width),maxY=Math.max(0,h-canvas.height);ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,-maxX*state.x,-maxY*state.y,w,h)};
    const resize=()=>{const [width,height]=size();canvas.width=width;canvas.height=height;paint()};
    image.onload=()=>{state.ready=true;resize();host.querySelector('[data-photo-upload]').disabled=false;URL.revokeObjectURL(url)};image.onerror=()=>{URL.revokeObjectURL(url);host.textContent='This image could not be opened.'};image.src=url;
    host.querySelector('[data-photo-shape]').onchange=e=>{state.mode=e.target.value;state.zoom=1;host.querySelector('[data-photo-zoom]').value='1';resize()};
    for(const [name,key] of [['zoom','zoom'],['x','x'],['y','y']])host.querySelector(`[data-photo-${name}]`).oninput=e=>{state[key]=Number(e.target.value);paint()};
    host.querySelector('[data-photo-cancel]').onclick=()=>{URL.revokeObjectURL(url);host.innerHTML=''};
    host.querySelector('[data-photo-upload]').onclick=async()=>{
      const button=host.querySelector('[data-photo-upload]');
      button.disabled=true;
      try{
        if(!state.ready)return;
        const blob=await new Promise(resolve=>canvas.toBlob(resolve,'image/jpeg',.84));
        if(blob)await onReady(blob);
      }finally{if(button.isConnected)button.disabled=false;}
    };
  }
  async function mount({client,run,slot,owner,status}){
    if(!slot||!run?.id)return;
    const objectUrls=[];
    const clearUrls=()=>{while(objectUrls.length)URL.revokeObjectURL(objectUrls.pop())};
    async function load(){
      clearUrls();slot.innerHTML='<p class="hint">Loading photos…</p>';
      let res;
      try{res=await fetch(`/api/run-photos?run_id=${encodeURIComponent(run.id)}`,{headers:await headers(client)});}catch(_){slot.innerHTML='<p class="hint">Photos could not load.</p>';return;}
      if(!res.ok){slot.innerHTML=`<p class="hint">${esc(await responseMessage(res))}</p>`;return;}
      const body=await res.json(), photos=Array.isArray(body)?body:(body.photos||[]);
      const canAdd=owner&&photos.length<6;
      slot.innerHTML=`<section class="run-photos" aria-labelledby="run-photos-title"><div class="head"><h2 id="run-photos-title">Photos</h2><span class="meta">${photos.length} of 6</span></div><div class="run-photo-grid"></div>${canAdd?'<label class="photo-add">Add a photo<input data-photo-file type="file" accept="image/jpeg,image/png,image/webp"></label><p class="hint">Choose a JPEG, PNG or WebP.</p><div data-photo-editor></div>':owner?'<p class="hint">Six photos added. Remove one before adding another.</p>':''}</section>`;
      const grid=slot.querySelector('.run-photo-grid');
      for(const photo of photos){
        try{const path=photoPath(photo);if(!path)continue;const imageRes=await fetch(path,{headers:await headers(client)});if(!imageRes.ok)continue;const url=URL.createObjectURL(await imageRes.blob());objectUrls.push(url);const item=document.createElement('figure');item.innerHTML=`<img src="${url}" alt="Run photo" loading="lazy">${owner?`<button type="button" class="ghost" data-photo-delete="${esc(path)}">Remove</button>`:''}`;grid.append(item);}catch(_){}
      }
      if(canAdd){
        slot.querySelector('[data-photo-file]').onchange=e=>{const file=e.target.files?.[0];if(!file)return;if(file.size>12*1024*1024){status('Choose an image smaller than 12 MB.',true);return;}cropper(file,slot.querySelector('[data-photo-editor]'),async blob=>{try{if(blob.size>3*1024*1024){status('The cropped image is still larger than 3 MB.',true);return;}const base64=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=reject;reader.readAsDataURL(blob)});const upload=await fetch('/api/run-photos',{method:'POST',headers:await headers(client,true),body:JSON.stringify({run_id:run.id,image_base64:base64})});if(!upload.ok){status(await responseMessage(upload),true);return;}status('Photo added.');await load();}catch(_){status('Photo upload could not reach STRIVE. Try again.',true);}});};
      }
      if(owner)slot.querySelectorAll('[data-photo-delete]').forEach(button=>button.onclick=async()=>{button.disabled=true;try{const res=await fetch(button.dataset.photoDelete,{method:'DELETE',headers:await headers(client)});if(!res.ok){status(await responseMessage(res),true);return;}status('Photo removed.');await load();}catch(_){status('Photo removal could not reach STRIVE. Try again.',true);}finally{if(button.isConnected)button.disabled=false;}});
    }
    await load();
  }
  async function mountCovers({client,root:host=document}){
    const cards=[...host.querySelectorAll('.fc[data-run-id]:not([data-photo-checked])')];
    await Promise.all(cards.map(async card=>{
      card.dataset.photoChecked='true';
      try{
        const runId=card.dataset.runId;
        const list=await fetch(`/api/run-photos?run_id=${encodeURIComponent(runId)}`,{headers:await headers(client)});
        if(!list.ok)return;
        const payload=await list.json(), photo=payload?.photos?.[0];
        const path=photoPath(photo);if(!path)return;
        const imageRes=await fetch(path,{headers:await headers(client)});
        if(!imageRes.ok)return;
        const url=URL.createObjectURL(await imageRes.blob());
        const image=document.createElement('img');
        image.className='run-photo-cover';image.src=url;image.alt='';image.loading='lazy';
        image.onload=()=>URL.revokeObjectURL(url);
        image.onerror=()=>URL.revokeObjectURL(url);
        card.querySelector('.fc-body')?.prepend(image);
      }catch(_){}
    }));
  }
  root.StriveRunPhotos={mount,mountCovers};
})(typeof window!=="undefined"?window:globalThis);
