---
name: spineai-patterns
description: Use when designing or building a Spine 4.2 skeletal animation, when calling spineAI MCP build tools (create_project, add_bone, add_slot, add_region_attachment, add_animation, add_bone_keyframes, add_slot_keyframes, set_default_animation, export_project), or when authoring slot machine FX, reel symbols, UI panels, pickup or win celebration animations. Triggers on kebab-case bone/slot/animation naming questions, T03/T07/T08 gotchas, render order decisions, or attachment composition. Does NOT cover Spine Editor GUI usage, mesh deformation rigging, or IK constraint setup (M2.b).
---

# spineai-patterns

Authoring conventions distilled from 22 official Spine 4.2 examples.
Apply **before** issuing spineAI MCP build calls. Comprehensive catalog
in `docs/SPINE_PATTERNS.md`; this skill carries only the rules that
are most often violated.

## The five rules

1. **Use kebab-case** for bones, slots, attachments, animations, and
   skins. Never `coin_front`, never `coinFront`. Unanimous across the 22
   official examples.
2. **Animation naming**: single-animation FX projects use literal
   `animation` (the Spine Editor default). Multi-animation projects use
   short verbs (`idle`, `walk`, `jump`, `bounce`). **Never** descriptive
   names like `coin_spin_loop`.
3. **Attachment names mirror the slot name** by default. Slot
   `coin-front` → attachment `coin-front`. No `_img`, `_attach` suffixes.
4. **Initial attachment goes via timeline at t=0** (T07), not via
   `Slot.attachment` (setup-pose explosion).
5. **Always call `set_default_animation`** before export (T08 — runtimes
   auto-play the first dict key).

## Semantic bone suffixes

| Suffix | Meaning |
|---|---|
| `-target` | IK target bone, placed at root level |
| `-control` / `-controller` | Animator-facing handle; other bones follow via constraints |
| `-root` | Anchor for a logical sub-skeleton |
| `-bb` | Bounding box attachment carrier |

If you name a bone with one of these, the surrounding structure must match.

## Slot render order (universal stack)

Earlier slot = background; later slot = foreground.

```
shadow → background body → main body → mid details → additive FX → highlights
```

Glints / sparkles use `blend="additive"`. With `blend="normal"` they
read as flat stickers, not light.

## Scope budget for slot machine FX

5–15 bones, depth 2–5. If you're at 50 bones for a coin, scope is wrong.

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| Underscore / camelCase | Naming inconsistent with all 22 examples | Use kebab-case |
| `coin_spin_animation` | Long animation name | `animation` (single) or `spin` (multi) |
| Glint child of spinning bone | Glint orbits the coin, looks pinned | Parent glint to root or sibling, account for transform composition |
| Glint sibling but rotated to match the spinner | Same orbit problem, just laundered through a sibling bone | Don't keyframe the glint bone's rotation at all — the whole point is screen-space motion, not "coin-relative motion via a sibling" |
| `blend="normal"` for sparkles | Looks like opaque sticker | `blend="additive"` |
| Snap-reset frame for loops | Visible flicker | Use cyclic rotation (`0 → 360`) or alpha bookend |
| Skipping `set_default_animation` | Runtimes auto-play `death` if alphabetically first | Always set explicitly |

## Where to dig deeper

- `examples/coin-spin-glint.md` — full worked example: 16 MCP calls
  building a coin spin with a screen-space glint, with curve choices
  explained.
- `reference/cookbook.md` — recipes for spinning symbol, pickup bounce,
  reel idle, and win celebration.
- `reference/archetypes.md` — bone / slot / animation breakdowns of the
  10 archetypes from the official examples.
- `docs/SPINE_PATTERNS.md` (spineAI repo) — comprehensive catalog,
  hierarchy patterns by complexity, constraint guidance (M2.b),
  full anti-pattern table.
