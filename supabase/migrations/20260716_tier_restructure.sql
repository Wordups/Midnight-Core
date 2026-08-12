-- Tier restructure: trial/growth retired, FREE/STARTER/PRO per The Angle.
-- Code carries trial->free and growth->pro aliases, so this is safe to run
-- before or after the app deploy.

update tenants set plan_type = 'free' where plan_type = 'trial';
update tenants set plan_type = 'pro'  where plan_type = 'growth';

alter table tenants alter column plan_type set default 'free';
