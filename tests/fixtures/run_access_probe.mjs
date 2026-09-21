import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const access = require('../../site/run-access.js');

const author = 'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
const viewer = 'bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
const link = {id: 'cccccccc-cccc-cccc-cccc-cccccccccccc', visibility: 'link', profile_id: author, title: 'SECRET LINK'};
const pub = {...link, visibility: 'public', title: 'Public run'};
const priv = {...link, visibility: 'private', title: 'SECRET PRIVATE'};
const crewShared = {
  id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
  visibility: 'private',
  crew_shared: true,
  crew_id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
  profile_id: author,
  title: 'Crew shared run',
};
const closeFriendsCrew = {...crewShared, visibility: 'close_friends', title: 'Close friends not via crew flag'};

function client({followCount = 0, closeFriend = false} = {}) {
  return {
    from(table) {
      const q = {
        select() { return q; },
        eq() { return q; },
        then(onFulfilled) {
          const count = table === 'grinder_follows' ? followCount : 0;
          return Promise.resolve({count, error: null}).then(onFulfilled);
        },
      };
      return q;
    },
    async rpc(name, args) {
      assert.equal(name, 'grinder_is_close_friend_of');
      assert.equal(args.owner, author);
      return {data: closeFriend, error: null};
    },
  };
}

assert.equal(await access.viewerMayOpenRun(pub, {me: null, client: null}), true);
assert.equal(await access.viewerMayOpenRun(link, {me: null, client: null}), false, 'stranger must not open Link');
assert.equal(await access.viewerMayOpenRun(priv, {me: {id: viewer}, client: null}), false, 'private stays owner-only');
assert.equal(await access.viewerMayOpenRun(link, {me: {id: author}, client: null}), true, 'owner may open Link');
assert.equal(await access.viewerMayOpenRun(link, {me: {id: viewer}, client: client({followCount: 1})}), true, 'follower may open Link');
assert.equal(await access.viewerMayOpenRun(link, {me: {id: viewer}, client: client({followCount: 0, closeFriend: false})}), false, 'signed-in stranger stays gated');
assert.equal(await access.viewerMayOpenRun(link, {me: {id: viewer}, client: client({followCount: 0, closeFriend: true})}), true, 'close friend may open Link');
// N1: crew_shared private rows are what grinder_share_with_crew stores. A crew member who
// already received the row through RLS must open it on ?run= (matches grinder_can_read_run).
assert.equal(await access.viewerMayOpenRun(crewShared, {me: null, client: null}), false, 'signed-out cannot open crew_shared');
assert.equal(await access.viewerMayOpenRun(crewShared, {me: {id: viewer}, client: null}), true, 'crew member may open crew_shared private run');
assert.equal(await access.viewerMayOpenRun(crewShared, {me: {id: author}, client: null}), true, 'owner may open crew_shared');
assert.equal(await access.viewerMayOpenRun(priv, {me: {id: viewer}, client: null}), false, 'plain private still owner-only');
assert.equal(await access.viewerMayOpenRun(closeFriendsCrew, {me: {id: viewer}, client: client({closeFriend: true})}), true, 'close_friends still uses its own path');
console.log('PASS run access: public open, link relationship-gated, private owner-only, crew_shared open to members');
