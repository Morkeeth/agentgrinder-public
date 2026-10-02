// Server maintenance only. Drains at most 100 queued objects; no paths/keys/bytes logged.
// Run after account/run deletions or on a scheduled maintenance worker.
import {runtimeConfig} from '../server/runtime-config.mjs';
export async function cleanupPhotos(config,fetchImpl=fetch) {
 if(!config.STORAGE_KEY) throw new Error('STRIVE_STORAGE_SERVICE_ROLE_KEY is required.');
 const headers={apikey:config.STORAGE_KEY,Authorization:`Bearer ${config.STORAGE_KEY}`,
  'Accept-Profile':'strava','Content-Profile':'strava','Content-Type':'application/json'};
 const request=(path,opts={})=>fetchImpl(config.SB_URL+path,{...opts,headers,cache:'no-store',signal:AbortSignal.timeout(15000)});
 const response=await request('/rest/v1/photo_deletion_queue?select=object_name&order=requested_at.asc&limit=100');
 if(!response.ok) throw new Error('Could not read the deletion queue.');
 const queued=await response.json();let removed=0;
 for(const row of queued) {
  if(!/^[0-9a-f-]{36}\/[0-9a-f-]{36}\.jpg$/.test(row.object_name)) throw new Error('Unexpected photo object path in queue.');
  const deleted=await request('/storage/v1/object/strive-run-photos',{method:'DELETE',body:JSON.stringify({prefixes:[row.object_name]})});
  if(!deleted.ok) throw new Error('Photo deletion failed; queue entry retained.');
  const acknowledged=await request('/rest/v1/photo_deletion_queue?object_name=eq.'+encodeURIComponent(row.object_name),{method:'DELETE'});
  if(!acknowledged.ok) throw new Error('Deletion queue acknowledgement failed; retry is safe.');
  removed++;
 }
 return {removed,remaining_unknown:queued.length===100};
}
if(import.meta.url===new URL(process.argv[1],'file:').href) {
 try {console.log(JSON.stringify(await cleanupPhotos({...runtimeConfig(),STORAGE_KEY:process.env.STRIVE_STORAGE_SERVICE_ROLE_KEY})));}
 catch(error) {console.error(error.message);process.exitCode=1;}
}
