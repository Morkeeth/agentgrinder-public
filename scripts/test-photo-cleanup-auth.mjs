import assert from 'node:assert/strict';
import handler from '../api/photo-cleanup.js';
let status,body;
const res={setHeader(){},status(s){status=s;return this},json(b){body=b;}};
delete process.env.CRON_SECRET;
await handler({method:'GET',headers:{}},res);assert.equal(status,401);
process.env.CRON_SECRET='test-secret';
for(const authorization of ['', 'Bearer bad', 'Bearer test-secret-extra']){
 await handler({method:'GET',headers:{authorization}},res);assert.equal(status,401);
}
await handler({method:'POST',headers:{authorization:'Bearer test-secret'}},res);assert.equal(status,405);
delete process.env.STRIVE_STORAGE_SERVICE_ROLE_KEY;
await handler({method:'GET',headers:{authorization:'Bearer test-secret'}},res);assert.equal(status,503);
assert.ok(!JSON.stringify(body).includes('test-secret'));
console.log('Cleanup rejects unauthenticated and wrong-method requests; missing storage fails safely.');
