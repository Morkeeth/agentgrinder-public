# Feedback panel: secure next slice

Do not show the persistent Feedback button until this path exists end to end.

## User path

1. A signed-in beta user opens Feedback from the fixed edge trigger.
2. The right panel (mobile sheet) carries a 1–5 rating, one sentence, the current route and an optional screenshot.
3. The user sees the exact payload and presses **Send feedback**.
4. The panel shows a stored receipt ID. It never claims success from a local draft or clipboard copy.

## Storage

Create `strava.product_feedback` with:

- `id uuid primary key default gen_random_uuid()`
- `profile_id uuid not null references strava.profiles(id) on delete cascade`
- `rating smallint not null check (rating between 1 and 5)`
- `body text not null check (char_length(body) between 1 and 500)`
- `route text not null check (char_length(route) <= 500)`
- `screenshot_path text null`
- `created_at timestamptz not null default now()`

Enable RLS. A signed-in user may insert a row only when `profile_id = strava.grinder_profile_id()` and read only their own rows. No public read policy. Put screenshots in a private `strive-feedback` bucket under `<profile_id>/<feedback_id>.<ext>` with matching owner policies, a 5 MB limit, and PNG/JPEG/WebP content types. Store the object only after the feedback row exists; delete it if the final row update fails.

## Release proof

- An anonymous insert is denied.
- One signed-in beta user stores feedback and receives its ID.
- Another user cannot read the row or screenshot.
- The owner can open the private screenshot by a short-lived signed URL.
- `/r/<id>` and exported run images contain no Feedback trigger or beta chrome.
