import {cp,mkdir,readFile,writeFile} from 'node:fs/promises';
import {runtimeConfig} from '../server/runtime-config.mjs';
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
console.log('Built Strava website with explicit strava schema; no privileged keys.');
