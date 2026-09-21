// Audience gate for non-public runs. Public is world-readable. Private is owner-only.
// Link and Close friends need a signed-in reader with a follow or close-friends relation
// (or ownership). Strangers stay on the neutral private surface.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.GrinderRunAccess = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  async function followsAuthor(client, viewerId, authorId) {
    if (!client || !viewerId || !authorId) return false;
    const { count, error } = await client
      .from('grinder_follows')
      .select('follower_id', { count: 'exact', head: true })
      .eq('follower_id', viewerId)
      .eq('followed_id', authorId);
    return !error && Number(count) > 0;
  }

  async function isCloseFriendOf(client, authorId) {
    if (!client || !authorId) return false;
    try {
      const { data, error } = await client.rpc('grinder_is_close_friend_of', { owner: authorId });
      if (!error) return data === true;
    } catch (_) {}
    return false;
  }

  async function viewerMayOpenRun(run, { me, client } = {}) {
    if (!run) return false;
    if (run.visibility === 'public') return true;
    if (!me || !me.id) return false;
    if (me.id === run.profile_id) return true;
    if (run.visibility === 'private' || run.visibility === 'anonymous') return false;
    if (run.visibility === 'close_friends') {
      // RLS only returns Close friends rows to the owner or listed friends.
      return true;
    }
    if (run.visibility === 'link') {
      if (await followsAuthor(client, me.id, run.profile_id)) return true;
      return isCloseFriendOf(client, run.profile_id);
    }
    return false;
  }

  return { viewerMayOpenRun, followsAuthor, isCloseFriendOf };
});
