# Midnight Core — Architecture

## Pipeline

upload → extract → transform → classify → map → validate → render → store

## Layers

- **api/** — FastAPI routes (pipeline + dashboard)
- **core/** — pure engine logic, no template or API concerns
- **renderers/** — docx + pdf output
- **templates/** — modular template packs
- **storage/** — file handling + Supabase client

## Rules

1. No template logic inside core engine files
2. No company-specific content ever enters this repo
3. Every output is a draft — nothing is "compliant"
4. Validate in 2.0, productize in Core
