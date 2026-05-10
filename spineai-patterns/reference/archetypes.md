# Archetype catalog

The 10 archetypes from `docs/SPINE_OBSERVATIONS.raw.md`, with the
specific structural decisions each one demonstrates. Use this when
you're not sure what scope to target — find the closest archetype to
your task and start from its bone/slot/animation budget.

---

## Archetype index

| # | Archetype | Reference example | Bones | Slots | Animations | Use spineAI for? |
|---|---|---|---|---|---|---|
| 1 | Humanoid biped | `spineboy-pro` | 67 | 52 | 11 | M2.b |
| 2 | Quadruped (IK + mesh) | `raptor-pro` | 76 | 36 | 5 | M2.b |
| 3 | **Simple FX (single anim)** | `coin-pro` | 7 | 6 | 1 | **M2.a (primary niche)** |
| 4 | **Pickup FX** | `powerup-pro` | 21 | 13 | 1 | **M2.a (primary niche)** |
| 5 | Winged creature | `owl-pro` | 20 | 27 | 6 | M2.b |
| 6 | Mix-and-match (skins) | `mix-and-match-pro` | 143 | 80 | 6 | M2.b |
| 7 | Mesh deformation | `vine-pro` | 18 | 2 | 1 | M2.b |
| 8 | Mechanical | `tank-pro` | 115 | 200 | 2 | M2.b |
| 9 | Multi-character scene | `celestial-circus-pro` | 60 | 70 | 7 | M2.b |
| 10 | **Simple mechanical (flat)** | `windmill-ess` | 93 | 96 | 1 | **M2.a (multi-root variant)** |

**M2.a** = covered by the current spineAI build tools (M2.a primitives
in `JOURNAL.md`). **M2.b** = needs mesh / IK / transform / path /
physics / events / multi-skin support, not yet shipped.

---

## In scope for spineAI's primary niche

The three archetypes spineAI is designed for. If your task is in this
list, M2.a is enough.

### #3 Simple FX (`coin-pro`)

- **7 bones** in 2-level hierarchy
- **6 slots**, region-only, single skin
- **Single animation** named literally `animation`
- Hyphen-cased bone/slot names (`coin-front`, `coin-sides`, `shine`)
- Use for: coin spins, idle FX, simple looping symbols

### #4 Pickup FX (`powerup-pro`)

- **21 bones** in depth-5 hierarchy (still shallow)
- **13 slots**, mix region + mesh (M2.a region-only is fine for most uses)
- **Single animation** named `bounce`
- Use for: pickup bounces, token-collected animations, reward bursts

### #10 Simple mechanical, flat (`windmill-ess`)

- **93 bones** but **30 of them are root children** — flat layout, not deep tree
- **96 slots**, region-only
- **Single animation** named literally `animation`
- Use for: scenery / reel-background / particle gardens where each
  visual element is independent

---

## Out of scope for M2.a (deferred to M2.b)

The other archetypes need features the build tools don't expose yet.
Listed for reference; if your task matches one of these, talk to the
spineAI maintainer about M2.b prioritisation.

### #1 Humanoid biped (`spineboy-pro`)

Needs IK constraints (7 of them: feet, arms), transform constraints
(8). Plus 11 named animations covering `idle` / `walk` / `run` /
`jump` / `aim` / `shoot` / `hoverboard` / `idle-turn` / `run-to-idle` /
`death` / `portal`. M2.a's keyframe primitives can theoretically build
this without IK, but the result won't deform correctly.

### #2 Quadruped IK + mesh (`raptor-pro`)

11-deep hierarchy, 9 IK constraints, 15 mesh attachments. Same M2.b
gating as #1.

### #5 Winged creature (`owl-pro`)

Mesh-heavy (15 meshes for wing deformation), 1 transform constraint.
The 6 animations (`blink`, `down`, `idle`, `left`, `right`, `up`) split
the eye and head motion into separate tracks. Conceptually inside M2.a
budget, but the meshes need M2.b.

### #6 Mix-and-match (`mix-and-match-pro`)

The skin variant pattern. 34 skins with **path-style names**
(`accessories/cape-blue`, `accessories/hat-red-yellow`). 4 path
constraints. 17 transform constraints. The richness comes from skins;
M2.a's single-skin model can't reproduce.

### #7 Mesh deformation (`vine-pro`)

Almost entirely mesh + path constraint. 1 region attachment, 1 path
attachment, 1 mesh attachment, 1 path constraint. Pure M2.b.

### #8 Mechanical (`tank-pro`)

200 slots vs 115 bones — heavy z-order layering. 2 IK + 6 transform +
1 path constraint. Primary lesson: when slots > bones, you're stacking
many decorative parts on few load-bearing bones. M2.a can do the
slot/bone math; the constraints are M2.b.

### #9 Multi-character scene (`celestial-circus-pro`)

The only example using **physics constraints** (30 of them — cloth-like
dangling). 7 named animations including `eyeblink`, `eyeblink-long`,
`stars`, `swing`, `wind-idle`, `wing-flap`, `wings-and-feet` — all
ambient. Physics is brand-new in Spine 4.2, almost nobody else uses it.

---

## Cross-cutting observations

Worth knowing even when the archetype doesn't directly apply.

### Most common animation names

`idle` (×3), `walk` (×3), `jump` (×2), `shoot` (×2), `animation` (×2),
`blink` (×2). When in doubt about animation naming, pick from this list
or compose with hyphens (`idle-turn`, `wind-idle`, `eyeblink-long`).

### Attachment composition by archetype size

- Simple mechanical (coin / windmill): **100% region**
- Heavy mesh: **vine 1:1 mesh-only**, mix-and-match heavy mesh
- Mixed: most characters **60–70% region, 30–40% mesh**

If you're doing FX in spineAI's niche, you should be at 100% region
unless you have a specific deformation need.

### Constraint usage by archetype

| Constraint type | Used by | Notes |
|---|---|---|
| IK | humanoid_biped, quadruped, mix-and-match, mechanical | Feet / hands / treads |
| Transform | 5 of 10 archetypes (humanoid, winged, variants, mechanical, scene) | Secondary motion / follow-through |
| Path | mix-and-match, vine, mechanical | Tracks, ropes, treads |
| Physics | celestial-circus only | Brand new in Spine 4.2 |

For slot machine FX in M2.a, you don't need any constraints. If you do,
that's a sign you're either in M2.b territory or over-engineering.
