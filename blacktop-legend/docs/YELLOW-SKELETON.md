# The Yellow Skeleton — pulling structure without the code

**The question:** how do we take inspiration from Pokemon Yellow without reading (or being allowed to use) its code?

**The answer:** a game's *structure* doesn't live in its code. The ROM is compiled Z80 machine code — even Game Freak's own designers didn't design in it. The structure lives in the **design decisions**, and those are fully observable from playing the game and from 25 years of public documentation (strategy guides, speedrun routing, design retrospectives, fan wikis). Game mechanics and structure are not copyrightable — only the *expression* is (art, names, story text, music, code). So we extract the skeleton as explicit design rules, then build our own flesh on it.

This doc IS that extraction. Every rule below is a structural observation about Yellow, paired with the Blacktop Legend translation. When we make a design decision, we check it against this table — that's what "inspired by Yellow" means in practice, and it never requires touching Nintendo's property.

## 1. The progression graph

| Yellow's rule | Why it works | Blacktop Legend |
|---|---|---|
| One linear critical path (8 gyms in near-fixed order), with small optional pockets off it | Player always knows the next goal; freedom lives in the side pockets, not the spine | 8 Court Kings in near-fixed order; optional courts, mentors, freestyle spots off the spine |
| Progress gates are *abilities*, not keys (Cut, Surf) | The unlock is also a toy — gates feel like growth, not doors | Traversal skills from mentors (Wall Hop, Fence Vault) gate map pockets |
| Each area is beatable slightly under-leveled with good play, comfortably at-level | Skill can substitute for grind — grind is optional, never mandatory | Battle math tuned so matchup-reading beats stat advantage of ±1 "level" |
| The map loops back on itself (late-game shortcuts to early towns) | The world feels like a place, not a corridor | Late neighborhoods open shortcuts back to Your Block (bus line, bridge) |

## 2. Pacing beats (Yellow's actual rhythm)

| Beat | Yellow | Blacktop Legend |
|---|---|---|
| Tutorial fight | ~5 min in, unlosable stakes | Bounce hypes you into a 3-point warmup vs your sibling's ghost routine |
| First real wall | Brock (~45 min) — punishes your starter, forces a second tool | King #1 punishes spamming your best move (fundamentals) |
| Rival cadence | ~Every 90 min, scaled to your progress, appears at transitions | Rival ambushes at neighborhood borders, roster mirrors your recent loadout |
| Mid-game breather | Non-combat setpiece (Lavender, S.S. Anne) | Chapter 4-5: a night tournament cutscene chapter, freestyle showcase |
| Difficulty spike | Gym 7-8 demand type-chart fluency | Kings 7-8 require reading AI tendencies + stamina economy |
| Victory lap | Elite Four = 5 fights, no shops between | The Big Stage: bracket with no stamina restores between games |

## 3. The encounter economy

- **Yellow:** ~35–50 trainer fights on the critical path; wild encounters are optional grind/collection; trainers pay money, wilds pay XP + collection. **Fights average 1–3 minutes.**
- **BL:** ~35 named baller fights on the path; pickup games (wild analog) are optional stamina/XP farming; ballers pay skill unlocks + rep, pickups pay XP + item drops. First-to-11 tuned to 2–4 minutes.

## 4. The battle system's real skeleton

What makes Pokemon battles work is not turns — it's these five rules:

1. **Simultaneous commitment** — both sides lock choices, then resolution reveals who read whom. → Offense picks a move while defense picks a scheme.
2. **A small public counter-chart** — type effectiveness is learnable in an evening and printed on every fan's brain. → The 4×4 matchup triangle (drive/jumper/three/post × tight/sag/reach/jump).
3. **A depletable resource that outlives one fight** — PP/HP persist between battles, making the *route* the challenge. → Stamina persists; fountains are Pokemon Centers.
4. **A 4-slot expression cap** — you can't bring everything; loadout IS identity. → 4 equipped skills + 1 signature.
5. **Readable opponents** — trainers telegraph their archetype before the fight (class name, sprite, location). → Baller intro dialog + neighborhood + visible tendency tells.

## 5. Numbers worth copying (order of magnitude, not values)

| Knob | Yellow | BL v1 |
|---|---|---|
| Collectibles | 151 species | ~40 skills (each must feel distinct — quality bar is higher per unit) |
| Party/loadout | 6 mons ÷ 4 moves | 4 skills + 1 signature |
| Critical path | ~25 hours | 8–12 hours (mobile sessions) |
| Towns | 10 | 8 neighborhoods + finale venue |
| Save points | anywhere | anywhere (mobile: aggressive autosave) |
| Companion | 1, follows, has moods | Bounce, follows, hypes (flow meter bonus at high bond) |

## 6. What we deliberately do NOT copy

- **Random encounters** — 1999's friction; replaced by visible on-court challengers (modern QoL, like Let's Go/PLA did).
- **Binary loss punishment** (blackout, lose money) — an L teaches: post-game dialog tells you what beat you.
- **Grid-locked movement** — structure stays, presentation is free-roam smooth scroll (per 8/15 art direction).
- **Silent protagonist walls of menu text** — battle log is 1-2 punchy lines max.

## 7. Legal bright lines

Use freely: mechanics, pacing curves, progression patterns, UI *patterns* (4-slot menus, meter placement), genre conventions.
Never use: ROM contents, sprites, tilesets, music, names (Pikachu, Poke-anything), story text, trade dress that implies Nintendo affiliation. The ROM in the project uploads stays out of the repo and out of the build — it's reference for *playing*, on a cart you own, not an asset source.
