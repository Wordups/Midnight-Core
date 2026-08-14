# Blacktop Legend — Technical Roadmap (iOS first)

## Engine decision

**Recommendation: Godot 4** (GDScript, free, no revenue share).

| Option | iOS | Android later | Fit for this game | Notes |
|---|---|---|---|---|
| **Godot 4** ✅ | Excellent (official iOS export, TestFlight-ready) | One-click export | Ideal — 2D tilemap + UI-heavy turn-based combat is Godot's sweet spot | No licensing cost; huge 2D community; GDScript is fast to iterate |
| Unity | Excellent | Excellent | Fine, but heavier than needed | Runtime-fee drama resolved but licensing still a consideration; better if you later want heavy 3D |
| Swift + SpriteKit | Native, lightest binary | ❌ full rewrite | Good iOS-only fit | Kills the "Android later" requirement — rules it out |
| React Native / Capacitor + canvas | OK | OK | Workable for this genre (turn-based, 2D) | Viable if you want a web-tech stack; worse feel for the overworld |

Godot gives you: TileMap + autotiling for the overworld, AnimationPlayer for battle sequences, a real UI system for the battle menus, and `.tres` resources for skills/ballers data (designer-editable without code).

## Architecture sketch

```
res://
  scenes/
    overworld/      # TileMap scenes per neighborhood, NPC scenes, encounter triggers
    battle/         # Battle scene: state machine (ChooseOffense→ChooseDefense→Resolve→...)
    ui/             # Menus, loadout editor, dialog system
  data/
    skills/*.tres   # Skill resources: family, pts, base%, stat, stamina cost, fx
    ballers/*.tres  # Opponent resources: stats, loadout, tendencies, dialog
    map/            # Neighborhood graph, gating (chains required)
  systems/
    battle_resolver.gd   # Pure logic: (offense skill, defense scheme, stats, state) -> outcome
    save_service.gd      # Local save + iCloud key-value sync
    progression.gd       # XP, levels, stat points, chains
```

**Key rule:** `battle_resolver.gd` is pure and deterministic given an injected RNG — unit-testable (GUT framework), and reusable server-side later for async PvP anti-cheat.

## Milestones

### M0 — Prototype (done, in this repo)
Playable HTML5 prototype of the core loop: overworld → encounter → turn-based 1v1 → skill collection → Court King. Validates the battle system math and the fun. See `prototype/index.html`.

### M1 — Vertical slice (4–6 weeks)
- Godot project, one neighborhood (Your Block), 3 ballers + 1 Court King
- Full battle system: matchup triangle, stamina, hype, signatures
- Loadout editor, save/load, touch controls, haptics
- Placeholder art → commission pixel artist for 1 tileset + 4 characters
- **Exit criteria:** a stranger plays 15 minutes on a phone and wants to keep the build

### M2 — Content engine (6–8 weeks)
- Data-driven neighborhoods/ballers/skills (all 8 neighborhoods stubbed)
- Dialog/quest flags, mentors, rival encounters 1–2
- Balance harness: simulate 10k battles per matchup in CI, flag win-rate outliers

### M3 — iOS beta (4 weeks)
- App Store assets, TestFlight external beta
- iCloud save sync, Game Center achievements
- Performance pass (thermals, battery — target 60fps, cap at 30 in overworld if needed)

### M4 — Launch iOS (4 weeks)
- Full content: 8 Kings, Big Stage, post-game
- Soft launch (CA/AU/NZ) → global

### M5 — Android
- Godot export, Play Store, controller support pass

## Costs & accounts (rough)

- Apple Developer Program: $99/yr (needed at M3)
- Pixel artist: ~$3–8k for full tileset + character set (biggest line item)
- Audio: licensed lo-fi pack ~$200 or composer ~$1–3k
- Everything else: $0 (Godot, GUT, GitHub Actions for CI builds via `godot-ci`)

## Risks

1. **Battle depth vs. readability** — the matchup triangle must be learnable in 3 games. Mitigate: telegraphed AI tells early, tooltip on every pick. (Prototype tests this.)
2. **Content cost** — 8 neighborhoods of pixel art is the schedule. Mitigate: shared tile library + palette swaps per neighborhood.
3. **Solo-dev scope creep** — v1 guardrails in GDD §10 are the contract. No online PvP in v1.
