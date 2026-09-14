-- Read-only setup evidence: no user data or credentials.
select current_database(), current_user, to_regnamespace('strava') as strava_schema;
select nspname from pg_namespace where nspname in ('public','strava','auth');
select t.tgname, pg_get_triggerdef(t.oid) as trigger_definition,
       pg_get_functiondef(t.tgfoid) as function_definition
from pg_trigger t where t.tgrelid=to_regclass('auth.users') and not t.tgisinternal;
select n.nspname,p.proname,p.proconfig,p.proacl
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where n.nspname='strava' order by p.proname;
select c.relname,c.relrowsecurity,c.relacl
from pg_class c where c.relnamespace=to_regnamespace('strava') and c.relkind='r'
order by c.relname;
