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

**What the code does now.** `Gradient.pickPoint` (`Gradient.py:344-348`) dispatches point
selection through `self.pick_functions[self.pick_mode]`, a dict built per-gradient-instance at
`Gradient.py:84-92` covering `max`, `min`, `rnd`, `linear`, `binary`, `sub`, `reg`. Both
single-gradient branches of `pick_point_for_ingredient` call this: the single-item-list branch
(`ptInd = all_gradients[ingr.gradient[0]].pickPoint(allIngrPts)`) and the bare-string branch
(`ptInd = all_gradients[ingr.gradient].pickPoint(allIngrPts)`), both around
`Gradient.py:315-318`. So a single gradient's declared `pick_mode` is honored.

The combined path (`len(ingr.gradient) > 1`, `Gradient.py:269-314`) never calls `pickPoint` on
any component gradient. It always finishes with
`Gradient.pick_point_from_weight(ingr.combined_weight, allIngrPts)`
(`Gradient.py:220-245` for the callee, call site at `Gradient.py:312-314`), and that function's
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
`if not hasattr(ingr, "combined_weight")` (`Gradient.py:270`): computed once, cached directly as
an attribute on the `ingr` object, and never cleared anywhere in `Gradient.py` afterward. This
is unchanged by the F-A fix — F-A only changes *what* gets computed and cached (candidate-mass
normalized instead of global-mass normalized), not the caching mechanism itself. A comment
documenting this was added at the call site (`Gradient.py:279-304`, immediately before the
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
  can drift from its intended `gradient_weights` coefficient over a long run, by an amount and
  in a direction that depend on geometry rather than on the components' shapes. See #4 below
  for the mechanism, why "differently-shaped components empty out their support at different
  rates" is the wrong driver, and what is and is not established about the direction.
- *Across seeds in a serial run*: `Analysis.py`'s `doloop()` (`Analysis.py:1143`), when
  `number_of_processes <= 1` (the serial branch, ~`Analysis.py:1271-1295`, the default/common
  case), calls `self.pack_one_seed(...)` for every `seed_index` **in the same process**.
  `pack_one_seed` (`Analysis.py:966`) calls `self.env.reset()` near its top (~`Analysis.py:987`)
  before `build_grid()`/`pack()` — but, per the `resetIngrRecip()` finding above, that reset does
  not clear any ingredient's `combined_weight`. If the same `Ingredient` Python object is reused
  across seeds on this serial path (env.reset() does not reconstruct ingredient objects from
  scratch), the mixture computed at seed 0's first pick is silently reused for every later seed,
  even though each seed nominally gets a fresh grid/candidate set. Whether that reuse is a
  *defect* or merely correct memoization depends on something this section originally did not
  ask: **would a recompute have produced a different map?** The cached map is the mixture
  normalized over the candidate set as it stood at the ingredient's first pick. Because
  `pack_one_seed` calls `env.reset()` and then `build_grid()`, every seed starts from an
  identical t=0 candidate set — so when the multi-gradient ingredient is the *only* thing
  consuming free points, seed 0's cached map is exactly what seeds 1..N would have computed,
  and reusing it is correct.

  The reuse becomes a **real staleness bug** in the case that breaks that premise: when
  another ingredient is packed into the same region *before* the multi-gradient one. Then the
  candidate set at the multi-gradient ingredient's first pick depends on the earlier
  ingredient's placements, which *do* differ per seed — so the map cached at seed 0 is wrong
  for every later seed. That is the multi-structure configuration (ER/golgi packed alongside
  peroxisome/endosome), not the single-structure mixed rule. (The `ProcessPoolExecutor` branch for
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
scope the fix to the configurations where a recompute would actually differ. Note that
"are ingredient objects reconstructed fresh per seed?" is the *wrong* diagnostic — object
freshness is neither necessary nor sufficient. A reused object holding a map that equals what
a recompute would produce is correct memoization; a freshly constructed object would recompute
the same map and change nothing. The load-bearing question is whether the candidate set at the
ingredient's first pick varies across seeds, which happens only when another ingredient
consumes free points in the same region first (see the analysis above). Pick (i) or (ii) if
the multi-structure trees are to be repacked; otherwise this is dormant for the
single-structure mixed rule and can be filed rather than fixed.

---

## 3. `invert: "weight"` gives out-of-support points weight 1.0

**What the code does now.** `set_weights_by_mode` (`Gradient.py:435`) computes `self.weight`,
then at `Gradient.py:489` zeroes NaNs: `self.weight[numpy.isnan(self.weight)] = 0`. Only
afterward, at `Gradient.py:491-492`, does it apply the invert:
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

i.e. simply reorder `Gradient.py:489` to run after the (currently) `491-492` block instead of
before it.

---

## 4. Realized-share drift from the intended blend: mechanism, direction, and what is measured

`get_combined_gradient_weight` normalizes each component over the candidate set as it stands at the
ingredient's *first* pick, and `ingr.combined_weight` is cached from that moment onward (see #2).
Every later draw renormalizes those frozen weights over the *current* candidate list, so the
realized density departs from the intended blend as candidates deplete.

This section states what is and is not known about that departure. It is written at length because
earlier drafts of it — in the inline comment, in this file, and in the analysis-side HANDOFF — each
stated it more strongly than the code supports.

### The candidate set is not the free-point set

There are two distinct ways a point leaves contention, and only one of them is a pick:

- **Removed.** `BaseGrid.updateDistances` (`autopack/BaseGrid.py:104`) walks `insidePoints` and
  `reorder_free_points` hard-removes them. `get_new_distances_and_inside_points` (`:968`) classifies
  a point as inside when its `signed_distance <= 0`.
- **Blocked, but still in `free_points`.** `newDistPoints` keep their slot and get `distance[pt]`
  reduced. `get_list_of_free_indices` (`autopack/ingredient/Ingredient.py:789`) then filters on
  `comp_ids[pt] == current_comp_id and d >= cuttoff`, where `cuttoff = radius - jitter`
  (`get_cuttoff_value`, `:749`). Such a point can never be picked again, yet it was never consumed.

`pack_at_grid_pt_location` (`:1405`) blocks a ball of `encapsulating_radius + dpad`, and `dpad` is the
maximum radius over all *active* ingredients — not this ingredient's own.

Three further precisions, each of which an earlier draft got wrong:

- **`allIngrPts` is not "the free points."** It is the compartment- and cutoff-filtered subset. In one
  branch `get_list_of_free_indices` starts from the cached `self.allIngrPts` when that array is
  shorter than `nbFreePoints`.
- **The recompute is conditional, not unconditional.** `checkIfUpdate` (`:765`) returns the **stale
  cached** `allIngrPts` on its non-update branch. It behaves as if per-iteration only because
  `freePtsUpdateThreshold = 0.0` (`autopack/Environment.py:210`) and `nbPts > 0` after the first
  placement. Change that threshold and the behaviour changes with it.
- **"Weighted sampling without replacement" is an idealization.** `numpy.random.choice` in
  `pick_point_from_weight` defaults to `replace=True`. Removal is a side effect of successful
  placement *geometry*, not of the draw. `reject()` only sets `haveBeenRejected` and increments
  `rejectionCounter`, so a rejected point is not consumed and remains drawable.

### Direction: flattening is a limit result, not a general one

For a single ingredient in the **point-like limit** — one grid point consumed per placement — the
departure is a flattening that relaxes toward uniform over the *initial* candidate set. Outside that
limit the sign is geometry-dependent and unmeasured. Two mechanisms readable off this code can invert
it:

- **Interleaved co-packed ingredients.** `free_points` and `distance` are global state, and `dpad` is
  the max radius over all active ingredients. A co-ingredient whose consumption anti-correlates with
  this ingredient's `w` therefore *enriches* the high-weight survivors — sharpening, not flattening.
- **Boundary-truncated exclusion footprints.** A placement near a compartment surface consumes fewer
  candidates than one in the interior, so saturated capacity is boundary-elevated. All three
  non-uniform canonical gradients peak *at* a boundary, since `exp(-d / (lambda * nanmax(d)))` is
  maximal at `d = 0`. For a weakly peaked gradient the drift then runs *toward* the peak.

Both are conditional mechanisms, not measured effects. Stated the other way round: nothing in this
codebase currently measures the sign, so a document asserting one unconditionally is over-claiming.

### This code defines no per-component realized share

The blend is a single array and a pick carries no component label, so any per-component accounting
needs an **external attribution rule**. Disjoint supports make one unambiguous — but disjointness is
*sufficient, not necessary*. With overlapping supports the natural rule is the mixture responsibility
`c_i * p_i(x) / sum_j (c_j * p_j(x))`, which is exactly what an NNLS refit of realized occupancy
estimates. An earlier draft claimed a per-component share is defined *only* for disjoint supports;
that would have invalidated the refit this very document recommends as the diagnostic.

Under either rule the baseline is the **sum-normalized** coefficient `c_i / sum_j c_j`, not the raw
`gradient_weights` value: `numpy.average(prob_list, axis=0, weights=w)` normalizes its weights
internally, and the dict branch pre-divides by their sum before that.

The consequence is that the blend is **exactly scale-invariant in `sum(c)`**: multiplying every
weight by a constant leaves the blended array unchanged to float precision (checked at factors 1.07,
1.46 and 17.3 -- maximum absolute change 9e-19). A caller cannot influence the mixture through the
magnitude of the weights it passes, only through their ratios, so `{..: 30, ..: 70}` -- as this
repo's own mixer test fixture passes -- yields exactly the blend of `{..: 0.3, ..: 0.7}`.
