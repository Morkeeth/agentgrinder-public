import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {decisionHtml} from '../server/decision-story.mjs';

const fixture=JSON.parse(readFileSync(new URL('../tests/fixtures/full-night-run-code-route.json',import.meta.url),'utf8'));
const port=Number(process.env.PORT||process.argv[2]||8002);
const path=`/d/${fixture.id}`;
const origin=`http://127.0.0.1:${port}`;

createServer((req,res)=>{
 const pathname=new URL(req.url,origin).pathname;
 if(pathname!==path){
  res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'});
  res.end(`Open ${path}\n`);
  return;
 }
 res.writeHead(200,{
  'Content-Type':'text/html; charset=utf-8',
  'Cache-Control':'no-store',
  'X-Content-Type-Options':'nosniff',
 });
 res.end(decisionHtml(fixture,{preview:true,origin}));
}).listen(port,'127.0.0.1',()=>{
 console.log(`Decision story preview: ${origin}${path}`);
 console.log('Fixture bb5bb2e0 is local only; this does not read or change the production run.');
});
