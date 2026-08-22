# Adjacent defects on the combined-gradient path — filed, not fixed

Written as part of the F-A fix (candidate-restricted normalization in
`Gradient.get_combined_gradient_weight`, branch
`fix/combined-gradient-candidate-normalization`). Per the dispatching brief, these three
issues are documented here and deliberately **not** fixed in this branch: fixing them would
widen the diff past the "changes confined to the combined-gradient functions" gate, and each
one risks changing single-gradient or non-manuscript behavior. Line numbers below are current
as of this branch (post F-A fix) in `cellpack/autopack/Gradient.py`.

All three were checked against `cellpack-analysis/cellpack_analysis/packing/rule_repository.py`
(the manuscript's canonical `GRADIENTS` dict, read-only) via `grep -n "pick_mode\|invert"`,
which returned no matches — none of the manuscript's rules (`random`, `nucleus_gradient`,
`membrane_gradient`, `apical_gradient`, or their `combine_prob` mixes) set a non-default
`pick_mode` or any `invert` value. **The grep is accurate; the dormancy inference drawn from it
for defect #1 is not.** The default `pick_mode` is `"linear"`
(`interface_objects/default_values.py:9`), applied to every gradient via
`GradientData.__init__`'s `deep_merge(gradient_data, gradient_options)` (`gradient_data.py:111`)
regardless of whether the recipe's own JSON sets `pick_mode` at all — so an absent `pick_mode` key
does not mean there is nothing for defect #1 to override. Generated recipes carry no `pick_mode`
key, so every manuscript gradient resolves to `pick_mode: "linear"`, and the combined path's
unconditional `numpy.random.choice` overrides it on **every** combined-gradient mix that has ever
been run, including the Fig 5b/5c packings. Defect #1 is not dormant — see #1 below for why this
is nevertheless benign. Defects #2 and #3 are unaffected by this correction: defect #3's dormancy
follows directly from this same grep (no `invert` value is set anywhere, and that reasoning does
not depend on a default-value assumption the way defect #1's did), and defect #2's liveness
depends on packing-invocation configuration (serial vs. parallel `doloop`), not on this grep at
all.

---

## 1. Per-gradient `pick_mode` is silently ignored on the combined path

**What the code does now.** `Gradient.pickPoint` (`Gradient.py:314-318`) dispatches point
selection through `self.pick_functions[self.pick_mode]`, a dict built per-gradient-instance at
`Gradient.py:84-92` covering `max`, `min`, `rnd`, `linear`, `binary`, `sub`, `reg`. Both
single-gradient branches of `pick_point_for_ingredient` call this: the single-item-list branch
(`ptInd = all_gradients[ingr.gradient[0]].pickPoint(allIngrPts)`) and the bare-string branch
(`ptInd = all_gradients[ingr.gradient].pickPoint(allIngrPts)`), both around
`Gradient.py:286-289`. So a single gradient's declared `pick_mode` is honored.

The combined path (`len(ingr.gradient) > 1`, `Gradient.py:246-283`) never calls `pickPoint` on
any component gradient. It always finishes with
`Gradient.pick_point_from_weight(ingr.combined_weight, allIngrPts)`
(`Gradient.py:197-221` for the callee, call site at `Gradient.py:281-283`), and that function's
body unconditionally does `numpy.random.choice(points, p=point_probabilities)` — i.e. it always
behaves like `pick_mode: "rnd"`, regardless of what `pick_mode` any of the mixed component
gradients declares in its JSON (`"max"`, `"min"`, `"linear"`, `"binary"`, `"sub"`, `"reg"`).
There is no code path by which a combined gradient's per-component `pick_mode` reaches point
selection.

**Why it is wrong/risky.** Neither the recipe validators
(`autopack/validation/recipe_models.py`, `interface_objects/gradient_data.py`, per the repo's
own `CLAUDE.md`) nor anything in `Gradient.py` raises, warns, or logs when a gradient with a
non-`"rnd"` `pick_mode` is used inside a multi-gradient mix. A recipe author who sets
`pick_mode: "max"` on a gradient later reused in a mix will have that setting accepted and then
silently overridden — the recipe reads as "always pick the single highest-weight point" but
actually does weighted-random sampling. This is a silent semantic downgrade, not a crash.

**Who it could affect.** Every recipe that mixes a gradient into a `packing_mode: gradient` list
of length > 1 — not only ones that explicitly set a non-default `pick_mode`. Generated recipes
carry no `pick_mode` key, so every manuscript gradient resolves to the default
`pick_mode: "linear"` (`interface_objects/default_values.py:9`, via `GradientData.__init__`'s
`deep_merge`), and the combined path's unconditional `numpy.random.choice` overrides that default
on every mix ever run, including the Fig 5b/5c packings — **the override fires universally, not
only on some hypothetical future non-default recipe.** It is benign only because
`getLinearWeighted` and `numpy.random.choice(p=w/Σw)` are both weight-proportional samplers, so
the substituted selection is distributionally equivalent to what `pick_mode: "linear"` would have
done (verified: total variation 0.0072 at N = 200,000 draws). A future recipe that sets a
genuinely different `pick_mode` (`"max"`, `"min"`, `"binary"`, `"sub"`, `"reg"` — anything not
weight-proportional) on a gradient later mixed would still see a real, silent behavior change,
since the linear/`"rnd"` equivalence does not extend to those modes.

**Suggested fix sketch.** Decide the intended semantics first (this is a design choice, not a
mechanical patch): e.g. (a) require/validate that all gradients in a mix share one `pick_mode`
and generalize `pick_point_from_weight` to dispatch through `self.pick_functions`-equivalent
logic on the *combined* weight array, or (b) explicitly document that mixing always implies
`"rnd"` and make the validator reject/warn on a mismatched `pick_mode` inside a mix instead of
ignoring it silently. Either changes the combined path's selection function, which is
out of scope for F-A (candidate-set normalization only).

---

## 2. `combined_weight` is cached via `hasattr` and never invalidated

**What the code does now.** `pick_point_for_ingredient` guards the mixture computation with
`if not hasattr(ingr, "combined_weight")` (`Gradient.py:247`): computed once, cached directly as
an attribute on the `ingr` object, and never cleared anywhere in `Gradient.py` afterward. This
is unchanged by the F-A fix — F-A only changes *what* gets computed and cached (candidate-mass
normalized instead of global-mass normalized), not the caching mechanism itself. A comment
documenting this was added at the call site (`Gradient.py:~251-266`, immediately before the
`get_combined_gradient_weight` call) as required by the brief's "document the t=0 caching
semantics" instruction.

Checked (read-only) whether this cache is cleared by the normal per-seed reset path:
`Environment.reset()` (`Environment.py:1479`) calls `resetIngrRecip()` (`Environment.py:1499`),
which resets `firstTimeUpdate`, `counter`, `rejectionCounter`, `completion`, `prev_alt`,
`start_positions`, `allIngrPts` (cleared to `[]`), and conditionally `isph`/`icyl` — it does
**not** touch `combined_weight`.

**Why it is wrong/risky.** Two distinct consequences:

- *Within one seed*: deliberate and now documented — the mixture stays stationary over the run
  using the candidate set as it stood at the ingredient's first pick, rather than being
  recomputed as `allIngrPts` shrinks. This matches "one blended weight map per ingredient," which
  is what the analysis assumes, but it is still an approximation: a component's realized share
  can drift from its intended `gradient_weights` coefficient over a long run as
  differently-shaped components empty out their support at different rates.
- *Across seeds in a serial run*: `Analysis.py`'s `doloop()` (`Analysis.py:1143`), when
  `number_of_processes <= 1` (the serial branch, ~`Analysis.py:1271-1295`, the default/common
  case), calls `self.pack_one_seed(...)` for every `seed_index` **in the same process**.
  `pack_one_seed` (`Analysis.py:966`) calls `self.env.reset()` near its top (~`Analysis.py:987`)
  before `build_grid()`/`pack()` — but, per the `resetIngrRecip()` finding above, that reset does
  not clear any ingredient's `combined_weight`. If the same `Ingredient` Python object is reused
  across seeds on this serial path (env.reset() does not reconstruct ingredient objects from
  scratch), the mixture computed at seed 0's first pick is silently reused for every later seed,
  even though each seed nominally gets a fresh grid/candidate set. This is a **live**, not
  merely theoretical, cross-seed staleness path for any multi-gradient ingredient packed via
  multiple serial `doloop` seeds. (The `ProcessPoolExecutor` branch for
  `number_of_processes > 1` does not share this risk — each worker process gets its own object
  graph.)

**Who it could affect.** Any multi-gradient (combined) ingredient packed with
`number_of_processes <= 1` and more than one seed in one `doloop` call.
`replicate_99_v2` uses only the four canonical single-gradient rules (`random`,
`nucleus_gradient`, `membrane_gradient`, `apical_gradient`; confirmed no combined gradient
lists) so it is **not** affected by this specific cross-seed path regardless of process count.
The at-risk condition is the mixed/interpolated rule (`combine_prob`, Fig 5b/5c). Whether that
packing invocation actually uses `number_of_processes <= 1` for multi-seed runs is a
cellpack-analysis-side packing-configuration question, outside this engine-only branch's scope
to verify — flagging it here as an open question for whoever repacks the mixed rule next.

**Suggested fix sketch.** Needs a design decision, not a mechanical patch: (i) invalidate
`combined_weight` inside `Environment.reset()`/`resetIngrRecip()` — correct but touches
`Environment.py`, a large shared file, well past this fix's diff gate; (ii) key the cache by
something that changes per seed/reset (e.g. a seed counter or `id(env)` threaded into
`pick_point_for_ingredient`) instead of a bare `hasattr`-guarded instance attribute; or (iii)
confirm/ensure ingredient objects are already reconstructed fresh per seed elsewhere in the
packing setup (in which case this is a non-issue in practice and the risk is theoretical) —
this needs to be checked against how `Environment`/`RecipeLoader` actually instantiate
ingredients per seed before picking (i) or (ii).

---

## 3. `invert: "weight"` gives out-of-support points weight 1.0

**What the code does now.** `set_weights_by_mode` (`Gradient.py:405`) computes `self.weight`,
then at `Gradient.py:459` zeroes NaNs: `self.weight[numpy.isnan(self.weight)] = 0`. Only
afterward, at `Gradient.py:461-462`, does it apply the invert:
`if self.invert == "weight": self.weight = 1.0 - self.weight`. Because NaN-zeroing runs first,
any point that was NaN — i.e. outside this gradient's/ingredient's valid support (outside a
compartment, a masked or otherwise-invalid distance) — is first turned into `0.0`, and then
`invert: "weight"` turns that `0.0` into `1.0`: an out-of-support point ends up with the
*maximum* possible weight after inversion, instead of remaining excluded. (`invert: "distance"`
does not have this problem — it flips `scaled_distances` before `weight_mode` is applied,
upstream of this NaN-zeroing step.)

**Why it is wrong/risky.** `invert: "weight"` presumably is meant to mean "prefer the points
this gradient normally disfavors" (`weight -> 1 - weight`), not "prefer points that have no
defined weight at all." Making unpackable/masked points maximally attractive is the opposite of
the recipe author's likely intent, and it would compound badly with the F-A fix's
candidate-restricted normalization in a combined mix: a component that is "supposed to be
near-zero in this region" could instead dominate a mix if the region is technically out of that
gradient's raw support but inside the packing candidate set.

**Who it could affect.** Only gradients that set `invert: "weight"` specifically (not
`invert: "distance"`, which is unaffected) and that also have NaN-valued points within the
region being packed. Confirmed dormant for all current manuscript rules and `combine_prob`
mixes (no gradient in `rule_repository.py` sets any `invert` value at all). Would only bite a
future recipe combining `invert: "weight"` with a gradient that has genuine out-of-support
(NaN) points in the packable region.

**Suggested fix sketch.** Swap the order of the two existing statements so NaN-zeroing always
runs last, regardless of invert (inverting a NaN leaves it NaN: `1.0 - nan == nan`, so a
trailing zero-out still correctly excludes it):

```python
if self.invert == "weight":
    self.weight = 1.0 - self.weight
self.weight[numpy.isnan(self.weight)] = 0
```

i.e. simply reorder `Gradient.py:459` to run after the (currently) `461-462` block instead of
before it.
