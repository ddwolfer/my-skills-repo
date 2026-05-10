# Worked example: coin spin + screen-space glint

A 100×100 slot machine reel symbol. The coin rotates one full turn per
1-second loop, and a thin glint streak sweeps across the face during the
first half of the loop. The streak lives in **screen space** (not the
spinning bone) so it doesn't orbit with the coin.

This example demonstrates every rule in `SKILL.md`:

- kebab-case throughout
- `animation` as the single-animation name
- attachment names mirror slots (no `_img` suffix)
- T07: initial attachment via timeline at t=0
- T08: explicit `set_default_animation` call
- glint parented to root (sibling of `coin-spin`), not to `coin-spin`
- alpha-bookend loop (not snap-reset)
- additive blend on the glint slot

## The 16 MCP calls

```
# 1. Project
pid = create_project("coin-symbol")

# 2. Bones (depth budget: 5–15 bones, max depth 2–5 for FX)
add_bone(pid, "root")
add_bone(pid, "coin-root",  parent="root")
add_bone(pid, "coin-spin",  parent="coin-root")
add_bone(pid, "glint-track", parent="root")           # NB: parent=root, not coin-spin

# 3. Slots in render order (back → front)
add_slot(pid, "shadow",     bone="coin-root")
add_slot(pid, "coin-back",  bone="coin-spin")
add_slot(pid, "coin-front", bone="coin-spin")
add_slot(pid, "glint",      bone="glint-track", blend="additive")
add_slot(pid, "coin-rim",   bone="coin-spin")

# 4. Region attachments — names mirror their slot
add_region_attachment(pid, "shadow",     "shadow",     width=110, height=30,  y=-50)
add_region_attachment(pid, "coin-back",  "coin-back",  width=100, height=100)
add_region_attachment(pid, "coin-front", "coin-front", width=95,  height=95)
add_region_attachment(pid, "glint",      "glint",      width=25,  height=100)
add_region_attachment(pid, "coin-rim",   "coin-rim",   width=100, height=100)

# 5. The single animation, conventionally named "animation"
add_animation(pid, "animation")

# 6. Initial attachment for every slot via timeline (T07)
for slot in ["shadow", "coin-back", "coin-front", "glint", "coin-rim"]:
    add_slot_keyframes(pid, "animation", slot,
                       attachment=[{"time": 0, "name": slot}])

# 7. Coin rotates one full turn (cyclic value: 360 ≡ 0)
add_bone_keyframes(pid, "animation", "coin-spin",
    rotate=[{"time": 0, "value": 0}, {"time": 1.0, "value": 360}])

# 8. Glint sweeps left → right during first half, invisible second half
add_bone_keyframes(pid, "animation", "glint-track",
    translate=[
        {"time": 0,   "x": -50, "y": 0},
        {"time": 0.5, "x":  50, "y": 0},
        {"time": 1.0, "x": -50, "y": 0},   # reset under cover of alpha=0
    ])

# 9. Glint alpha bookend (loop seamless: alpha=0 at both endpoints)
add_slot_keyframes(pid, "animation", "glint",
    alpha=[
        {"time": 0,    "value": 0},
        {"time": 0.05, "value": 1},
        {"time": 0.45, "value": 1},
        {"time": 0.5,  "value": 0},
        {"time": 1.0,  "value": 0},
    ])

# 10. Default animation pin (T08)
set_default_animation(pid, "animation")

# 11. Export — runs lint internally, raises on errors
export_project(pid, "./out")
```

## Why each choice

### Bone hierarchy

```
root
├── coin-root        — anchor for the coin assembly (allows future
│   │                  positioning without touching the spinning sub-tree)
│   └── coin-spin    — carries everything that rotates with the coin
│       (face, back, rim ride here)
└── glint-track      — sibling of coin-root, NOT child of coin-spin
                      (so the glint moves in screen space, not coin space)
```

A common mistake is parenting the glint to `coin-spin`. The visual
result: the glint orbits with the coin and looks pinned to a point on
the coin face, which destroys the "passing light" illusion.

### Slot order

```
shadow → coin-back → coin-front → glint → coin-rim
```

The rim sits last so the front bevel outline always wins z-order, even
over the additive glint. Without the rim being last, the glint can
visually "eat" the rim outline at peak alpha.

### Animation timing

- **1.0s loop** is the slot machine standard for symbol idle. Faster
  feels frantic; slower feels sluggish.
- **Glint sweep takes 0.5s** (half the rotation), then invisible for
  the second half. This makes the glint feel like a periodic
  reflection, not a constant feature.
- **Linear rotation** (no curve) — the coin should spin at a constant
  rate. If you want eased acceleration, that's a different effect
  (a `win` animation, not the idle).

### Loop seamlessness check

| Track | t=0 value | t=1.0 value | Continuous? |
|---|---|---|---|
| `coin-spin.rotate` | 0 | 360 | Yes (`360 ≡ 0` cyclic) |
| `glint-track.translate.x` | -50 | -50 | Yes (literal match) |
| `glint.alpha` | 0 | 0 | Yes (literal match) |

All three loop cleanly. The glint position resets during alpha=0, so
the reset is invisible.

## Adapting this to your symbol

| Want | Change |
|---|---|
| Different symbol size (e.g. 200×200 reel symbol) | Scale all `width`/`height` proportionally; keep glint width ~25% of symbol width |
| Slower / faster spin | Adjust the rotate keyframe time; keep proportional glint timing |
| Two glint passes per loop | Add second alpha bookend pulse at 0.5–1.0; mirror the translate |
| Multi-symbol variants (gold / silver / bronze) | Add skins `gold`, `silver`, `bronze` with `add_region_attachment(skin="gold", ...)` (M2.b: not yet supported in M2.a) |
| Win celebration on top | New `win` animation; **don't** set as default — keep `animation` as default and trigger `win` on cue |
