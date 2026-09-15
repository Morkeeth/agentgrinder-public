import local from './public-config.json' with {type:'json'};

function origin(value, label) {
 const parsed=new URL(value);
 const loopback=['localhost','127.0.0.1','[::1]'].includes(parsed.hostname);
 if((parsed.protocol!=='https:' && !(loopback&&parsed.protocol==='http:')) || parsed.username || parsed.password || parsed.search || parsed.hash || parsed.pathname!=='/') throw new Error(`${label} must be an HTTPS origin (localhost HTTP is allowed)`);
 return parsed.origin;
}
export function runtimeConfig(env=process.env) {
 const url=env.AGENTGRINDER_SUPABASE_URL||local.SB_URL;
 const key=env.AGENTGRINDER_SUPABASE_ANON_KEY||local.SB_KEY;
 if(env.VERCEL && (!env.AGENTGRINDER_SUPABASE_URL||!env.AGENTGRINDER_SUPABASE_ANON_KEY||!env.STRAVA_ORIGIN)) throw new Error('Production requires the Pacecard origin and public Supabase configuration');
 if(typeof key!=='string'||key.startsWith('sb_secret_')) throw new Error('Only a public Supabase key is allowed');
 if(key.split('.').length===3) {
  let payload;try{payload=JSON.parse(Buffer.from(key.split('.')[1],'base64url').toString())}catch{throw new Error('Invalid public key')}
  if(payload.role!=='anon') throw new Error('Only an anonymous public key is allowed');
 } else if(key!=='local-development-only'&&!key.startsWith('sb_publishable_')) throw new Error('Unsupported public key format');
 return {SB_URL:origin(url,'Supabase URL'),SB_KEY:key,SB_SCHEMA:'strava',ORIGIN:origin(env.STRAVA_ORIGIN||'http://localhost:8000','Pacecard URL')};
}
