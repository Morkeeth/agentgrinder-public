import {cp,mkdir,readdir,readFile,writeFile} from 'node:fs/promises';
import {runtimeConfig} from '../server/runtime-config.mjs';
import {BRAND,TAGLINE} from '../server/brand.mjs';
const config=runtimeConfig();
await mkdir('dist',{recursive:true});
await cp('site','dist',{recursive:true});
let html=await readFile('dist/index.html','utf8');
for(const name of ['SB_URL','SB_KEY']) {
 const pattern=new RegExp(`const ${name}="[^"]*";`);
 if(!pattern.test(html)) throw new Error(`Missing ${name} deployment marker`);
 html=html.replace(pattern,()=>`const ${name}=${JSON.stringify(config[name])};`);
}
await writeFile('dist/index.html',html);

// The brand tokens carry the product name into every built text file. The source
// tree keeps the tokens so one edit in server/brand.mjs renames the product.
const TEXT=/\.(html|js|css|json|txt|webmanifest)$/;
async function files(dir) {
 const out=[];
 for(const entry of await readdir(dir,{withFileTypes:true})) {
  const path=`${dir}/${entry.name}`;
  if(entry.isDirectory()) out.push(...await files(path));
  else if(TEXT.test(entry.name)) out.push(path);
 }
 return out;
}
let replaced=0;
for(const path of await files('dist')) {
 const before=await readFile(path,'utf8');
 const after=before.replaceAll('__BRAND__',BRAND).replaceAll('__TAGLINE__',TAGLINE);
 if(after===before) continue;
 if(/__BRAND__|__TAGLINE__/.test(after)) throw new Error(`Brand token survived substitution in ${path}`);
 replaced++;
 await writeFile(path,after);
}
if(!replaced) throw new Error('Missing __BRAND__ deployment marker in the built site');
console.log(`Built ${BRAND} website with explicit strava schema; no privileged keys. Brand applied to ${replaced} file(s).`);
