# Slot machine FX cookbook

Recipes for the four most common slot machine FX archetypes. Adapt;
don't copy verbatim. All use kebab-case, the `animation` (single) or
short-verb (multi) animation naming convention, and the standard render
order stack.

---

## 1. Spinning symbol (coin / gem / number)

**Use when**: a reel symbol needs to spin in place during win
animations or as an idle attractor.

**Bones (5–8, depth 2–3)**: `root` → `coin-root` → `coin-spin`. Optional
sibling `glint-track` parented to root for screen-space highlights.
Optional `shadow-bone` parented to root for non-spinning shadow.

**Slots in render order**:
```
shadow → coin-back → coin-front → glint (additive) → coin-rim
```

**Animation `animation` (1.0–1.5s loop)**:

| Track | Keyframes | Why |
|---|---|---|
| `coin-spin.rotate` | `(0, 0) → (1.0, 360)` linear | Cyclic value, no easing for steady spin |
| `glint-track.translate.x` | `-50 → 50 → -50` (sweep + reset) | Reset under alpha=0 cover |
| `glint.alpha` | `0 → 1 → 1 → 0 → 0` bookend | Glint visible only during sweep |
| `shadow.alpha` (optional) | subtle `0.6 → 0.7 → 0.6` pulse | Adds life without distracting |

**See**: `examples/coin-spin-glint.md` for the full MCP call sequence.

---

## 2. Pickup bounce (token-collected, big-win burst)

**Use when**: a symbol is awarded to the player and needs a "claim me"
animation — used after the reels stop, or when a multiplier is granted.

**Bones (5–10, depth 2–3)**: `root` → `token-root` → `token-body`. Plus
N sibling bones `star-1`...`star-N` for radial particles, parented to
`token-root`.

**Slots in render order**:
```
glow (additive) → token-body → star-1 → star-2 → star-3 (all additive)
```

**Animation `bounce` (0.5–0.8s, may be one-shot, NOT default)**:

| Track | Keyframes | Why |
|---|---|---|
| `token-root.translate.y` | `(0, 0) → (0.2, 60) → (0.5, 0)` with ease-out then ease-in | Bounce arc; ease-out feels "pulled up", ease-in "settles" |
| `token-root.scale` | `(0, 1) → (0.05, 1.1) → (0.2, 1) → (0.5, 1)` | Anticipation squash on launch |
| Each `star-N.translate` | radial outward with ease-out | Stars feel ejected by impact |
| Each `star-N.alpha` | bookend `0 → 1 → 0` | Stars appear from nothing, fade out |

**Don't set as default** — set the symbol's `idle` (or none) as default,
trigger `bounce` programmatically.

---

## 3. Reel symbol idle (subtle life)

**Use when**: symbols should breathe slightly while waiting for the
spin to start — separates "active" symbols from inert artwork.

**Bones (3–5, depth 2)**: `root` → `symbol-root` → `breathing-control`.
That's it.

**Slots**: just the symbol parts in their natural z-order (no special
FX layer).

**Animation `idle` (2.0–3.0s loop, set as default)**:

| Track | Keyframes | Why |
|---|---|---|
| `breathing-control.scale` | `(0, 1, 1) → (1.0, 1.02, 0.98) → (2.0, 1, 1)` mirrored | 2% squash, mirrored midpoint = cleanly seamless |
| Optional micro-rotate | `(0, 0) → (1.0, 1.5) → (2.0, 0)` on a feature bone | Adds asymmetric life |

**Avoid the temptation to over-animate idle.** It must read as
"subtle background motion", not "primary effect".

---

## 4. Win celebration (radial burst + spin)

**Use when**: a winning combination triggers a one-shot celebration
overlay on top of the symbol or reel.

**Bones (8–12, depth 2–3)**: `root` → `burst-root` → `center-glow` +
`ray-1` ... `ray-8` (all parented to `burst-root`).

**Slots in render order**:
```
center-glow (additive) → ray-1 ... ray-8 (additive) → optional foreground icon
```

**Animation `win` (1.0s, ONE-SHOT, NOT default)**:

| Track | Keyframes | Why |
|---|---|---|
| `burst-root.rotate` | `(0, 0) → (1.0, 30)` slow drift | Subtle rotation gives life without distracting from rays |
| Each `ray-N.scale` | `(0, 0) → (0.2, 1) → (0.8, 1) → (1.0, 0.9)` | Quick punch-in, hold, gentle settle |
| Each `ray-N.alpha` | `(0, 0) → (0.1, 1) → (0.9, 1) → (1.0, 0)` | Bookend for clean entry/exit |
| `center-glow.alpha` | `(0, 0) → (0.05, 1) → (0.7, 1) → (1.0, 0)` | Pre-empt rays slightly |

**Stagger the rays** by giving each a slightly different start time
(`ray-1` starts at t=0, `ray-2` at t=0.05, etc.). This is what
separates "designed" from "made by a script".

**Don't set as default**. Default is the symbol's idle; `win` is
triggered.

---

## When to depart from these recipes

| Symptom | Departure |
|---|---|
| Symbol needs to react to player input (e.g. hover) | Add a second animation `hover` with subtle scale up; use animator-runtime trigger |
| Win celebration needs sound sync | Add `events` track at key beats (M2.b — not in M2.a) |
| Reel needs blur during spin | Add `coin-blur` slot with motion-blur PNG, alpha bookend during high-speed phase |
| Multiple symbol variants (gold / silver / bronze) | Use skins, path-style names like `value/gold` (M2.b) |

For mesh deformation, IK constraints, transform constraints, path
constraints, multi-skin variants, and events — see `M2.b` scope in
`JOURNAL.md`. None of these are needed for the four recipes above.
