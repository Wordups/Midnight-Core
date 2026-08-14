# Blacktop Legend — Game Design Document

**Working title:** Blacktop Legend
**Genre:** Adventure RPG / turn-based 1v1 basketball
**Platforms:** iOS first, then Android
**Elevator pitch:** Pokemon Yellow, but instead of catching monsters you collect basketball skills. Explore a city of neighborhood courts, challenge ballers to 1v1, take down each neighborhood's Court King, and earn your shot at The Big Stage.

---

## 1. Core fantasy

You're a nobody from the block with a ball and a dream. Every court in the city has its own culture, its own players, and its own King. You rise by playing everyone, learning moves from mentors and rivals, and building a game that's uniquely yours.

The Pokemon Yellow mapping, explicitly:

| Pokemon Yellow | Blacktop Legend |
|---|---|
| Pikachu companion | **Bounce**, your dog — follows you everywhere, hypes you up courtside |
| Wild Pokemon encounters | Pickup players who call "next" when you step on their court |
| Trainers | Named ballers who challenge you on sight |
| Gym Leaders (8) | **Court Kings** (8) — the best player of each neighborhood |
| Gym Badges | **Chains** — earn all 8 to qualify for The Big Stage |
| Elite Four + Champion | **The Big Stage** — city tournament bracket + the reigning Legend |
| Moves (4-move loadout) | **Skills** — offensive/defensive basketball moves, equip 4 |
| TMs/HMs & move tutors | **Skill capsules** found in the world + **mentors** who teach you |
| PP | **Stamina** — every move costs stamina |
| Pokemon Center | Your crib / water fountains — full stamina restore |
| Type effectiveness | **Matchup triangle** — shot selection vs. defensive scheme |
| Bag / Potions / X-items | **Backpack → Dufflebag**, Water Bottle, Special Sauce |
| Leveling / stats | Player level: Handles, Shooting, Finishing, Defense, Stamina |

## 2. Design pillars

1. **Every possession is a decision.** Battles are turn-based mind games, not reflex tests. Read the defender, pick the right move.
2. **Your game is your build.** Only 4 equipped skills. A post bully, a three-point sniper, and an ankle-breaker guard all play differently.
3. **The city is the content.** Progress = geography. New neighborhoods mean new play styles, new mentors, new skills.
4. **Short sessions, long arc.** A 1v1 game takes 2–4 minutes (mobile-friendly), the journey to The Big Stage takes 8–12 hours.

## 3. The world

Eight neighborhoods, each with a distinct court culture and a Court King whose style teaches you something:

| # | Neighborhood | Court culture | Court King style (the "gym type") |
|---|---|---|---|
| 1 | **Your Block** | Beat-up rim, chain net | Fundamentals — punishes low-percentage shots |
| 2 | **Riverside Park** | Runs at sunrise | Hustle/defense — steals and blocks |
| 3 | **School Gym** | Indoor, squeaky floors | Mid-range purist |
| 4 | **The Cages** | Fenced, physical | Post play and bully ball |
| 5 | **Uptown** | Flashy crowd | Handles — ankle-breaker offense |
| 6 | **The Docks** | Windy, deep shooters | Three-point volume |
| 7 | **Rec Center** | Old heads | IQ — counters your tendencies |
| 8 | **Downtown Main** | Lights, cameras | Complete player |

Overworld is grid-based, top-down, tile-by-tile movement — deliberately retro. Ballers challenge you when you cross their line of sight. Skill capsules sit in visible but gated spots (need a mentor-taught traversal skill — the "HM" analog, e.g. *Wall Hop* to cut through alleys).

## 4. Battle system — turn-based 1v1

**Format:** First to 11. Inside shots = 2 pts, beyond the arc = 3 pts (streetball "2s and 3s" scaled up for punchier numbers).

**Turn structure:** Ball alternates on makes and misses (loser's ball / "make it take it" is a late-game court rule variant). Each possession:

- **Offense** picks one of their 4 equipped skills (each has: shot type, points, base %, governing stat, stamina cost).
- **Defense** simultaneously picks a scheme: **Tight D / Sag Off / Reach / Jump**.
- Resolution = base% + (attacker stat − defender stat) + matchup modifier + situational modifiers (stamina, hype, streaks).

**The matchup triangle (type effectiveness):**

| | Tight D | Sag Off | Reach | Jump |
|---|---|---|---|---|
| **Drive** skills | ✅ blow-by (+) | ❌ wall (−) | ➖ risky | ❌ meets rim protector (−) |
| **Jumper** skills | ❌ contested (−) | ➖ | ✅ open look (+) | ➖ |
| **Three** skills | ❌ contested (−) | ✅ open look (+) | ✅ (+) | ✅ shooter unbothered (+) |
| **Post** skills | ➖ | ➖ | ✅ seals (+) | ❌ blocked (−) |

- **Reach** has a steal chance (scales with defender Handles vs. ball-handler Handles). Failed reach = open look.
- **Jump** has a block chance vs. drives/post. Floater-class skills ignore Jump.

**Stamina (the PP system):** Every skill costs stamina. Under 30% stamina, all percentages drop hard and animations get "tired." Small regen each possession; full restore at home/fountains. Forces varied movesets and real resource decisions in long games.

**Flow State — the ultimate power.** The Flow meter fills with makes and defensive stops (crowd + Bounce barking). At full meter you enter **Flow State** for 3 possessions on each end:

- **No misses** — every shot you take drops. Steals and blocks can't touch you.
- **Killer crossover** — drive skills break ankles automatically; the defender is on the floor.
- **Lockdown defense** — opponent shot chances crater while you're in it.

Flow is the comeback mechanic and the highlight reel. It's earned in-game, never bought. Elite opponents (Court Kings, The Legend) have their own Flow, so late-game battles become races to the meter.

**AI tells:** Opponents have tendencies (readable, like Pokemon trainers' rosters). The Rec Center King adapts to *your* tendencies — the mirror-match lesson.

## 5. Skills

~40 skills at launch across five families: **Drive, Jumper, Three, Post, Utility** (utility = e.g. *Take a Breather* (restore stamina, give up nothing but tempo), *Pump Fake* (bait Jump, next shot +), *Call Glass* (bank shot, consistent %)).

Acquisition:
- **Level-up:** your archetype (chosen at start: Guard / Wing / Big) learns a default track.
- **Skill capsules:** found in the world (the TM analog). One-time teach.
- **Mentors:** legendary old heads in each neighborhood teach signature-adjacent skills after side quests (move tutor analog).
- **Rival:** beats you with a move → later you can learn it. The rivalry teaches you your counters.

Only 4 equipped + 1 signature. Respec anytime at your crib — build experimentation is free and encouraged.

## 5b. Items & the bag

The Pokemon bag, streetball edition. Using an item takes your possession (you walk it up top and reset — the turn-based cost that keeps items honest).

| Item | Analog | Effect |
|---|---|---|
| **Backpack** | starting Bag | Your inventory. Holds 3 items. |
| **Dufflebag** | Bag upgrade | Earned from a Court King. Holds 6 items + gear (sneakers/jerseys with passive stats). |
| **Water Bottle** | Potion | Restores a big chunk of Stamina mid-game. Refillable at fountains. |
| **Special Sauce** | X Attack / rare buff | Your next 3 shots get a big boost. Rare — found, gifted by mentors, never sold cheap. |

More items later (Fresh Kicks: stamina costs down for a game; Headband: Flow meter builds faster; Chalk Toss: taunt, opponent's next pick is telegraphed).

## 5c. Freestyle mode

No defender, no score to 11 — just you, a court, and style. Interact with any hoop to start a freestyle session: chain skills to build a **combo multiplier** (repeat a move and the combo drops — variety is style), land tricks to bank **Style Points**. High scores are tracked per court.

- Earns cosmetic currency and occasional item drops (this is where Special Sauce lives).
- It's also the practice room: try a new loadout with zero stakes before taking it into a King battle.
- Post-launch: async freestyle score battles with friends (share a replay ghost).

## 6. Progression

- **Player level 1–30.** Stats: Handles, Shooting, Finishing, Defense, Stamina. Level-ups grant points; Court King wins grant bonus stats matched to their style (beat the shooter king → +Shooting).
- **Chains (badges):** 8 total. Gate neighborhoods and unlock rule variants (win-by-2, make-it-take-it, first-to-21).
- **The Big Stage:** requires all 8 Chains. Bracket of 4 elite ballers + the reigning **Legend**. No stamina restores between games — the endurance test.
- **Post-game:** rematches at higher difficulty, daily "king of the court" runs, New Game+ with your rival as the final boss.

## 7. Story beats (light, Yellow-style)

Your older sibling was "supposed to make it" and didn't — their old mentor gives you Bounce and your first skill. Your rival is the entitled kid with pro-camp training who takes the easy path while you take the long one. Each Court King has one scene of humanity. The Legend at the end is who your sibling lost to.

## 8. Art & audio direction

- **Look:** GBC-inspired pixel art, modern palette. 16px tiles, chunky characters, oversized ball. Battles: side-view court diorama with big readable animations per skill family.
- **Audio:** lo-fi boom-bap overworld; battle tracks build layers as hype rises. Sneaker squeaks, chain nets, Bounce's bark as UI feedback.

## 9. Monetization

Premium ($4.99–6.99), no ads, no IAP stat boosts. Optional cosmetic packs later (jerseys, sneakers, court skins, Bounce accessories). Never sell power — build identity is the whole game.

## 10. Scope guardrails (v1)

- 8 neighborhoods, ~35 named ballers, 8 Kings, ~40 skills, 3 archetypes.
- No online PvP in v1 (design battle system so async PvP — ghost tendencies — can come in v1.5).
- Single save slot + iCloud sync.
