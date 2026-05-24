-- Tenant branding columns — latent since 1ea4c3c, formalized here.
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS brand_logo_url TEXT,
  ADD COLUMN IF NOT EXISTS brand_primary_color TEXT,
  ADD COLUMN IF NOT EXISTS brand_secondary_color TEXT,
  ADD COLUMN IF NOT EXISTS brand_footer_text TEXT;
