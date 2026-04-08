# Template Pack Guide

Each template pack lives in `backend/templates/{name}/` and contains:

| File | Purpose |
|------|---------|
| manifest.json | name, version, doc_type, outputs |
| schema.json | required + optional fields |
| mapping.json | source field → target field |
| layout.json | fonts, tables, section order |
| assets/ | logo placeholder, banner |

## Adding a customer template

1. Create `backend/templates/{customer_name}_{type}/`
2. Copy a generic pack as a starting point
3. Update mapping.json to match their field names
4. Update layout.json for their formatting rules
5. Register in `backend/templates/registry.py`
