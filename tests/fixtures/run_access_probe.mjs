import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const access = require('../../site/run-access.js');

const author = 'aaaaaaa1-aaaa-aaaa-aaaa-aaaaaaaaaaaa';
const viewer = 'bbbbbbb1-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
const link = {id: 'cccccccc-cccc-cccc-cccc-cccccccccccc', visibility: 'link', profile_id: author, title: 'SECRET LINK'};
const pub = {...link, visibility: 'public', title: 'Public run'};
const priv = {...link, visibility: 'private', title: 'SECRET PRIVATE'};

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
console.log('PASS run access: public open, link relationship-gated, private owner-only');
