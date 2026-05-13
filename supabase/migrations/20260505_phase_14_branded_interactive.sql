alter table public.tenants
  add column if not exists brand_logo_url text,
  add column if not exists brand_primary_color text default '#1D9E75',
  add column if not exists brand_secondary_color text default '#111111',
  add column if not exists brand_footer_text text;

update public.tenants
set
  brand_primary_color = coalesce(brand_primary_color, '#1D9E75'),
  brand_secondary_color = coalesce(brand_secondary_color, '#111111'),
  brand_footer_text = coalesce(brand_footer_text, '© 2026 ' || coalesce(name, 'Midnight'));

alter table public.documents
  add column if not exists public_url text,
  add column if not exists public_access boolean default false,
  add column if not exists qr_code_url text;

create index if not exists documents_public_access_idx
  on public.documents (public_access);
