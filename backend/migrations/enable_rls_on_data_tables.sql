-- Migration: enable Row Level Security on data tables flagged by Supabase's
-- security advisor (rls_disabled_in_public).
--
-- WHY THIS IS SAFE:
--   - The FastAPI backend connects as the `postgres` user (see postgres.py),
--     which is a superuser and BYPASSES RLS. So enabling RLS without
--     permissive policies blocks anon/authenticated direct access via
--     PostgREST but does NOT affect the backend's writes/reads.
--   - The frontend never calls `supabase.from('energy_readings')` or
--     `supabase.from('ml_prediction_log')` directly — confirmed by grep.
--     All data flows through FastAPI, which keeps working.
--
-- POSTGRES PARTITIONING NUANCE:
--   ALTER TABLE ... ENABLE ROW LEVEL SECURITY on the parent does NOT
--   propagate to existing partitions. Each partition must be enabled
--   individually. The parent (energy_readings) is already enabled.
--
-- IF YOU LATER WANT SUPABASE-JS DIRECT ACCESS:
--   Add a permissive policy like the commented template below to whichever
--   table(s) you want to expose. The current state is "deny all to non-superuser".
--
-- HOW TO ROLL BACK:
--   ALTER TABLE public.<table> DISABLE ROW LEVEL SECURITY;

BEGIN;

-- 1. The new ML prediction log table from Level 3.
ALTER TABLE public.ml_prediction_log ENABLE ROW LEVEL SECURITY;

-- 2. All energy_readings partitions (parent already has RLS on).
ALTER TABLE public.energy_readings_default     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20260301   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20260401   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20260501   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20260601   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20260701   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20260801   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20260901   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20261001   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20261101   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_readings_p20261201   ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------
-- Optional: example permissive policies — keep COMMENTED OUT unless
-- you want the supabase-js client to query these tables directly.
-- ------------------------------------------------------------------
-- CREATE POLICY "auth_can_read_predictions"
--   ON public.ml_prediction_log FOR SELECT
--   TO authenticated USING (true);
--
-- CREATE POLICY "auth_can_read_energy_readings"
--   ON public.energy_readings FOR SELECT
--   TO authenticated USING (true);

COMMIT;
