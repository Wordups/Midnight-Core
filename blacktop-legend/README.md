# 🏀 Blacktop Legend

**Pokemon Yellow, but basketball.** Explore a city of neighborhood courts, collect skills instead of monsters, battle ballers in turn-based 1v1, chase **Flow State**, take down all 8 Court Kings, and earn your shot at **The Big Stage**.

iOS first, Android after.

## What's here

| Path | What it is |
|---|---|
| [`docs/GDD.md`](docs/GDD.md) | Full game design document — world, battle system, Flow State, items, Freestyle mode, progression, story, monetization |
| [`docs/TECH-ROADMAP.md`](docs/TECH-ROADMAP.md) | Engine decision (Godot 4), architecture, milestones M0→M5, costs, risks |
| [`prototype/index.html`](prototype/index.html) | **Playable M0 prototype** — open it in any browser (phone works great). No build step, no dependencies. |

## The prototype (Chapter 1: Your Block)

Proves the core loop end-to-end:

- **Overworld** — grid-movement neighborhood with your crib, the park court, a chained gym, and your dog Bounce trailing you
- **Turn-based 1v1** — first to 11 (2s & 3s). Pick your move; the defense picks a scheme; the matchup triangle + stats decide. Read tendencies, manage stamina.
- **Flow State (the ultimate)** — fill the meter with buckets and stops: **no misses, killer crossover ankle-breakers, lockdown defense** for 3 possessions. King Reign has his own Flow — race him to it.
- **Skill collection** — start with 2 moves; find capsules (💿 Stepback Three, Floater) and learn moves from every baller you beat (Killer Crossover, Deep Three, Post Fade). Equip max 4.
- **The bag** — Backpack (3 slots) → **Dufflebag** (6, from the King). **Water Bottle** restores stamina; **Special Sauce** boosts your next 3 shots.
- **Freestyle mode** — interact with any hoop: no defender, chain varied moves for combo-multiplied style points. Break 200 for a rare reward.
- 3 park ballers gate the gym; beat them, then take the crown from **King Reign** for Chain 1/8.

Saves locally (localStorage). ~3 minutes per 1v1 game, ~20–30 minutes to take the crown.

## Moving this to its own repo

This folder is temporarily parked on a branch of Midnight-Core because the Claude session couldn't create repositories. To give it its own home:

1. Create the empty repo on GitHub (e.g. `Wordups/blacktop-legend`), no README.
2. From a clone of Midnight-Core on this branch:

```bash
git checkout claude/mobile-basketball-game-ie0ezj
cp -r blacktop-legend ~/blacktop-legend && cd ~/blacktop-legend
git init -b main && git add -A && git commit -m "Blacktop Legend — GDD, roadmap, playable M0 prototype"
git remote add origin https://github.com/Wordups/blacktop-legend.git && git push -u origin main
```

3. Delete the `blacktop-legend/` folder from the Midnight-Core branch afterward (or just delete the branch once migrated).

## Next up (see TECH-ROADMAP.md)

M1 vertical slice in **Godot 4**: real pixel art, animations, haptics, one full neighborhood — exit criteria is a stranger playing 15 minutes on a phone and asking to keep the build.
