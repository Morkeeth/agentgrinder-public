begin;

-- Extend ridge_basis to turn-order for Grok Bot burst ridges.
--
-- Migration 003 allowed wall-time and call-index. Call-index with fewer than 50
-- calls spreads evenly and draws a flat 1 and 0 comb. That comb is not a measured
-- shape. Turn-order places each typed turn's tool-call count into one bin, so the
-- card can show a burst sequence such as 1, 2, 5, 13, 0, 7.
--
-- PostgreSQL cannot widen a CHECK in place. This transaction replaces
-- runs_ridge_basis_check with the wider set. The constraint is never left absent.

alter table strava.runs drop constraint if exists runs_ridge_basis_check;
alter table strava.runs
  add constraint runs_ridge_basis_check
  check (
    ridge_basis is null
    or ridge_basis in ('wall-time', 'call-index', 'turn-order')
  );

comment on column strava.runs.ridge_basis is
  'wall-time when every call had a timestamp; call-index for untimed call order; turn-order for tool counts per typed turn.';

commit;
