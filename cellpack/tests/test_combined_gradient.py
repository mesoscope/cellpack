# -*- coding: utf-8 -*-
"""
Tests for the combined-gradient (multi-gradient) mixing path:
`Gradient.get_combined_gradient_weight` and the `len(ingr.gradient) > 1`
branch of `Gradient.pick_point_for_ingredient`.

Fixture: cellpack/tests/recipes/v2/test_combined_gradient.json. The two
gradients added for this test ("asym_sharp_near_origin",
"asym_sharp_far_end") have asymmetric support relative to a restricted
candidate set -- see `test_realized_pick_fractions_match_intended_weights`
below for the mass-fraction arithmetic. The original two gradients
("X_gradient", "Y_gradient") and their consuming ingredient/composition
entries are untouched.

See NOTES_combined_gradient_adjacent_defects.md (repo root) for three
adjacent issues on this same code path that are filed, not fixed, here.
"""
import itertools
import json
from pathlib import Path
from types import SimpleNamespace

import numpy
import pytest

from cellpack.autopack.Gradient import Gradient
from cellpack.autopack.interface_objects import GradientData

TEST_RECIPE_PATH = (
    Path(__file__).parent / "recipes" / "v2" / "test_combined_gradient.json"
)


def _load_gradient_from_recipe(name):
    """
    Build a real Gradient object from the named entry in the shared test
    recipe's "gradients" dict, via GradientData -- the same sanitization
    the recipe loader applies to raw JSON gradient dicts (defaults
    mode_settings/weight_mode_settings, computes direction vectors,
    validates mode/weight_mode/pick_mode/invert).
    """
    with open(TEST_RECIPE_PATH) as f:
        recipe = json.load(f)
    options = recipe["gradients"][name]
    return Gradient(GradientData(options, name).data)


def _build_synthetic_grid():
    """
    A small synthetic master grid over the recipe's bounding box
    ([[0, 0, 0], [1000, 1000, 1]]). Both asym_* gradients are mode "X", so
    weight only varies along X; Y/Z resolution is kept minimal while X is
    resolved finely (5-unit steps, 201 points) to give the exponential
    decay a clean shape.
    """
    xs = numpy.arange(0, 1001, 5)  # 201 points, 0..1000 step 5
    ys = numpy.array([0.0, 500.0, 1000.0])  # 3 points
    zs = numpy.array([0.0])  # 1 point
    positions = numpy.array(list(itertools.product(xs, ys, zs)), dtype=float)
    bb = [[0, 0, 0], [1000, 1000, 1]]
    return bb, positions


def test_asym_gradients_peak_at_opposite_ends_of_x():
    """
    Sanity check that "invert: distance" (not "reversed", which only feeds
    mode_settings["direction"] for mode:"vector" and is never read by
    build_axis_weight_map) actually moves the peak of an axis-mode gradient
    to the opposite end of the box. build_axis_weight_map always measures
    distance from the axis minimum (Gradient.py, build_axis_weight_map),
    so two axis gradients differing only by "reversed" would build
    identical weight maps -- this is what makes "invert: distance" the
    correct choice for constructing an asymmetric-support pair.
    """
    bb, positions = _build_synthetic_grid()
    near = _load_gradient_from_recipe("asym_sharp_near_origin")
    far = _load_gradient_from_recipe("asym_sharp_far_end")
    near.build_weight_map(bb, positions)
    far.build_weight_map(bb, positions)

    assert positions[numpy.argmax(near.weight), 0] == pytest.approx(0.0)
    assert positions[numpy.argmax(far.weight), 0] == pytest.approx(1000.0)


def test_realized_pick_fractions_match_intended_weights():
    """
    Monte Carlo check that realized pick fractions match the intended
    `gradient_weights` coefficients when the packable candidate set is a
    strict, asymmetric-relative-to-support subset of the master grid --
    the scenario the F-A fix (candidate-restricted normalization) targets.

    Setup: "asym_sharp_near_origin" peaks at X=0, "asym_sharp_far_end"
    peaks at X=1000 (both decay_length=0.03, exponential). Candidate set
    is restricted to X>=500 (101 of 201 X-values). gradient_weights are
    [30, 70] (intended c_near=0.30, c_far=0.70) -- deliberately unequal so
    that an implementation which ignored gradient_weights entirely could
    not accidentally pass.

    Because the two gradients are sharp (decay_length=0.03) and peak at
    opposite ends of the *candidate* range [500, 1000], each one's
    candidate-restricted probability mass concentrates overwhelmingly on
    its own half of that range: "near" mostly in [500, 750), "far" mostly
    in [750, 1000]. That lets us attribute picks to a component by which
    half of the candidate range they land in, and compare directly to the
    intended c_i.

    This test calls the same `pick_point_for_ingredient` entry point used
    in production packing (via a minimal SimpleNamespace standing in for
    an Ingredient) -- its signature is unchanged by the fix, so this test
    also runs (and fails, see below) against the pre-fix code.
    """
    bb, positions = _build_synthetic_grid()
    near = _load_gradient_from_recipe("asym_sharp_near_origin")
    far = _load_gradient_from_recipe("asym_sharp_far_end")
    near.build_weight_map(bb, positions)
    far.build_weight_map(bb, positions)

    candidate_points = numpy.where(positions[:, 0] >= 500)[0]
    all_gradients = {
        "asym_sharp_near_origin": near,
        "asym_sharp_far_end": far,
    }
    ingr = SimpleNamespace(
        gradient=["asym_sharp_near_origin", "asym_sharp_far_end"],
        gradient_weights=[30, 70],  # intended c_near=0.30, c_far=0.70
    )

    numpy.random.seed(42)  # seeded for a deterministic, non-flaky assertion
    n_picks = 10000
    picks = numpy.array(
        [
            Gradient.pick_point_for_ingredient(ingr, candidate_points, all_gradients)
            for _ in range(n_picks)
        ]
    )
    # combined_weight is computed once and cached on `ingr` at the first
    # pick (see pick_point_for_ingredient and
    # NOTES_combined_gradient_adjacent_defects.md #2) -- so all n_picks
    # draws use the same fixed distribution, which is what makes this a
    # clean, fixed-p binomial comparison rather than a moving target.
    assert hasattr(ingr, "combined_weight")

    picked_x = positions[picks, 0]
    realized_near = numpy.mean(picked_x < 750)
    realized_far = numpy.mean(picked_x >= 750)

    # --- tolerance arithmetic (binomial standard error), shown explicitly ---
    # Grid step in X is 5 units over a 1000-unit span, so each step changes
    # scaled_distance by 5/1000 = 0.005. With decay_length=0.03 for both
    # components, the per-step decay ratio is
    #   r = exp(-0.005 / 0.03) = exp(-1/6) ~= 0.8465.
    # The candidate range [500, 1000] splits at X=750 into two halves of
    # 50 grid-steps each. "near" peaks at the candidate's near edge
    # (X=500) and decays across it; "far" is the mirror image. The
    # fraction of one gradient's *own* candidate-restricted mass that
    # leaks across the X=750 split onto the other gradient's half is a
    # geometric tail bounded by
    #   r**50 = exp(-50/6) = exp(-8.333) ~= 2.4e-4,
    # which biases the expected realized fractions by less than 2e-4 away
    # from the idealized intended values (0.30 / 0.70) -- negligible next
    # to sampling noise.
    # Binomial standard error at p~=0.30, N=10000:
    #   SE = sqrt(p*(1-p)/N) = sqrt(0.30*0.70/10000) = sqrt(2.1e-5) ~= 0.0046.
    # tolerance=0.02 is ~4.3 SE (two-sided P(|Z|>4.3) ~= 1.7e-5), so this
    # assertion is not expected to flake, while still being >10x tighter
    # than the ~0.30 discrepancy the pre-fix code actually produces
    # (observed empirically, see below).
    tolerance = 0.02
    assert realized_near == pytest.approx(0.30, abs=tolerance)
    assert realized_far == pytest.approx(0.70, abs=tolerance)

    # --- empirically-verified pre-fix failure (required by plan step B3) ---
    # Before the fix, get_combined_gradient_weight normalized each
    # component over the WHOLE master grid, not the candidate set. "near"
    # peaks at X=0 (mostly outside the X>=500 candidate set), so its
    # candidate-restricted probability mass is ~r**100 = exp(-100/6)
    # ~= 5.8e-8 of its *global* mass; "far" peaks at X=1000 (almost
    # entirely inside the candidate set), so its candidate mass fraction
    # is ~1.0. Verified empirically (2026-08-21) by running this exact
    # test against the unmodified, pre-fix Gradient.py (before the
    # candidate_points parameter existed at all): this assertion block
    # failed with realized_near = 0.0004, realized_far = 0.9996 (4/10000
    # and 9996/10000 picks respectively) against intended 0.30/0.70 -- a
    # ~300x violation of the 0.02 tolerance. The fix was then implemented
    # and this test re-run to confirm it passes (see
    # NOTES_combined_gradient_adjacent_defects.md and the engine report
    # for the full before/after record).


def test_realized_pick_fractions_match_intended_weights_dict_form():
    """
    Dict-form companion to test_realized_pick_fractions_match_intended_weights
    above -- same fixture, same seed, same tolerance, only the
    `gradient_weights` form changes (name-keyed dict instead of a positional
    list). This is the form every production mixed recipe actually uses
    (`combine_prob` recipes key coefficients by gradient name), so it is the
    only test in this file that exercises the `isinstance(gradient_weights,
    dict)` branch in Gradient.get_combined_gradient_weight with a realistic,
    non-degenerate input -- every other test above passes a list. See the
    test above for the full mass-fraction arithmetic and tolerance
    derivation; this test only re-checks that the dict and list forms
    produce the same realized fractions.
    """
    bb, positions = _build_synthetic_grid()
    near = _load_gradient_from_recipe("asym_sharp_near_origin")
    far = _load_gradient_from_recipe("asym_sharp_far_end")
    near.build_weight_map(bb, positions)
    far.build_weight_map(bb, positions)

    candidate_points = numpy.where(positions[:, 0] >= 500)[0]
    all_gradients = {
        "asym_sharp_near_origin": near,
        "asym_sharp_far_end": far,
    }
    ingr = SimpleNamespace(
        gradient=["asym_sharp_near_origin", "asym_sharp_far_end"],
        gradient_weights={"asym_sharp_far_end": 70, "asym_sharp_near_origin": 30},
    )

    numpy.random.seed(42)  # same seed as the list-form test above
    n_picks = 10000
    picks = numpy.array(
        [
            Gradient.pick_point_for_ingredient(ingr, candidate_points, all_gradients)
            for _ in range(n_picks)
        ]
    )
    assert hasattr(ingr, "combined_weight")

    picked_x = positions[picks, 0]
    realized_near = numpy.mean(picked_x < 750)
    realized_far = numpy.mean(picked_x >= 750)

    # Same tolerance derivation as
    # test_realized_pick_fractions_match_intended_weights above.
    tolerance = 0.02
    assert realized_near == pytest.approx(0.30, abs=tolerance)
    assert realized_far == pytest.approx(0.70, abs=tolerance)


def test_combined_gradient_weight_without_candidate_points_matches_legacy_behavior():
    """
    candidate_points=None (the default) must reproduce the pre-fix,
    whole-grid-normalized behavior exactly -- the brief requires the
    existing signature stay call-compatible, since there may be other
    callers/tests that never pass a candidate set.
    """
    fake_a = SimpleNamespace(name="fake_a", weight=numpy.array([1.0, 2.0, 3.0, 4.0]))
    fake_b = SimpleNamespace(name="fake_b", weight=numpy.array([4.0, 3.0, 2.0, 1.0]))

    combined = Gradient.get_combined_gradient_weight([fake_a, fake_b], [50, 50])

    prob_a = fake_a.weight / fake_a.weight.sum()
    prob_b = fake_b.weight / fake_b.weight.sum()
    expected_combined_prob = numpy.average([prob_a, prob_b], axis=0, weights=[50, 50])
    expected_combined_prob /= expected_combined_prob.sum()
    expected = Gradient.normalize_by_max_value(expected_combined_prob)

    numpy.testing.assert_allclose(combined, expected)


def test_candidate_restricted_mixing_is_exact_for_disjoint_supports():
    """
    Deterministic (non-random) check of the core fix's arithmetic: build
    two fake gradient-like objects whose weight is EXACTLY zero outside a
    disjoint region (unlike real exponential decay, which only gets very
    small), so each component's candidate-restricted contribution to the
    combined probability can be checked exactly rather than via noisy
    Monte Carlo sampling.
    """
    fake_a = SimpleNamespace(
        name="fake_a", weight=numpy.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    )
    fake_b = SimpleNamespace(
        name="fake_b", weight=numpy.array([0.0, 0.0, 0.0, 1.0, 1.0, 1.0])
    )
    candidate_points = numpy.arange(6)

    combined = Gradient.get_combined_gradient_weight(
        [fake_a, fake_b], [30, 70], candidate_points=candidate_points
    )
    candidate_weight = combined[candidate_points]
    candidate_prob = candidate_weight / candidate_weight.sum()

    assert candidate_prob[:2].sum() == pytest.approx(0.3, abs=1e-9)
    assert candidate_prob[3:].sum() == pytest.approx(0.7, abs=1e-9)
    # point 2 is outside both components' support -> zero contribution
    assert candidate_prob[2] == pytest.approx(0.0, abs=1e-12)


def test_zero_candidate_mass_raises():
    """
    A component whose weight is exactly zero everywhere in the candidate
    set means the recipe asks to mix in a gradient with no packable
    support in this context -- the fix must raise a clear exception
    rather than silently dividing by zero and letting a NaN propagate
    into numpy.random.choice downstream.
    """
    fake_a = SimpleNamespace(name="fake_a", weight=numpy.array([1.0, 1.0, 0.0, 0.0]))
    fake_b = SimpleNamespace(name="fake_b", weight=numpy.array([0.0, 0.0, 1.0, 1.0]))
    candidate_points = numpy.array([2, 3])  # fake_a's weight is exactly 0 here

    with pytest.raises(ValueError, match="zero"):
        Gradient.get_combined_gradient_weight(
            [fake_a, fake_b], [50, 50], candidate_points=candidate_points
        )


def test_zero_coefficient_vector_raises():
    """
    A `gradient_weights` coefficient vector that sums to exactly zero (every
    component's mixing coefficient is 0) is a distinct degenerate input from
    test_zero_candidate_mass_raises above: there, one component's own weight
    map has zero mass over the candidate set; here, both components have
    perfectly good candidate mass, but the *mixing coefficients themselves*
    carry no information about how to combine them. numpy.average raises an
    opaque ZeroDivisionError for this today ("Weights sum to zero, can't be
    normalized"); the fix must raise the same clear, named ValueError as the
    other degenerate-input guards instead, so callers can catch one
    exception type at this boundary rather than a mix of ValueError and
    numpy/Python internals.
    """
    fake_a = SimpleNamespace(name="fake_a", weight=numpy.array([1.0, 1.0, 1.0, 1.0]))
    fake_b = SimpleNamespace(name="fake_b", weight=numpy.array([1.0, 1.0, 1.0, 1.0]))
    candidate_points = numpy.arange(4)  # both components have full candidate mass

    with pytest.raises(ValueError, match="zero"):
        Gradient.get_combined_gradient_weight(
            [fake_a, fake_b], [0, 0], candidate_points=candidate_points
        )


def test_zero_coefficient_dict_raises():
    """
    Dict-form companion to test_zero_coefficient_vector_raises. Every
    production mixed recipe passes `gradient_weights` as a name-keyed dict
    (see test_realized_pick_fractions_match_intended_weights_dict_form), and
    the dict branch resolves coefficients via a `.../total` division before
    `numpy.average` ever runs -- a zero-sum dict hits a plain Python
    ZeroDivisionError ("division by zero") one step earlier than the list
    form does. The fix must catch this case too, with the same ValueError.
    """
    fake_a = SimpleNamespace(name="fake_a", weight=numpy.array([1.0, 1.0, 1.0, 1.0]))
    fake_b = SimpleNamespace(name="fake_b", weight=numpy.array([1.0, 1.0, 1.0, 1.0]))
    candidate_points = numpy.arange(4)

    with pytest.raises(ValueError, match="zero"):
        Gradient.get_combined_gradient_weight(
            [fake_a, fake_b],
            {"fake_a": 0, "fake_b": 0},
            candidate_points=candidate_points,
        )


def test_legacy_global_normalization_reproduces_pre_fix_mass_leak():
    """
    Executable, permanent companion to
    test_realized_pick_fractions_match_intended_weights (plan step B3: "add
    a companion assertion that this test fails on the pre-fix code").
    Rather than relying only on a one-time stash/run/restore (already done
    manually -- see the recorded numbers above and the engine report), this
    reproduces the pre-fix *arithmetic* permanently and automatically: the
    fix kept get_combined_gradient_weight's default (candidate_points=None)
    call-compatible with the old, unconditional whole-grid normalization
    (see test_combined_gradient_weight_without_candidate_points_matches_legacy_behavior
    for the direct, non-Monte-Carlo proof of that equivalence on toy
    arrays). Pre-fix, pick_point_for_ingredient's combined branch was
    exactly:
        combined_weight = get_combined_gradient_weight(gradient_list, weights)
        ptInd = pick_point_from_weight(combined_weight, allIngrPts)
    -- the same two real (not reimplemented) functions called below, just
    without candidate restriction on the first call, then restricted to
    the candidate set only at the final pick step exactly as
    pick_point_for_ingredient does. So this test drives production code
    through the exact call sequence the pre-fix code used, and will start
    failing (as a regression alarm) if the "no candidate_points" default
    is ever changed to something other than legacy whole-grid
    normalization -- which would silently break the call-compatibility
    guarantee the fix design requires.
    """
    bb, positions = _build_synthetic_grid()
    near = _load_gradient_from_recipe("asym_sharp_near_origin")
    far = _load_gradient_from_recipe("asym_sharp_far_end")
    near.build_weight_map(bb, positions)
    far.build_weight_map(bb, positions)

    candidate_points = numpy.where(positions[:, 0] >= 500)[0]

    # No candidate_points kwarg -> legacy whole-master-grid normalization:
    # byte-for-byte what the pre-fix code always did, since no other
    # normalization mode existed before this fix.
    legacy_combined_weight = Gradient.get_combined_gradient_weight(
        [near, far], [30, 70]
    )

    numpy.random.seed(42)
    n_picks = 10000
    picks = numpy.array(
        [
            Gradient.pick_point_from_weight(legacy_combined_weight, candidate_points)
            for _ in range(n_picks)
        ]
    )
    picked_x = positions[picks, 0]
    realized_near = numpy.mean(picked_x < 750)
    realized_far = numpy.mean(picked_x >= 750)

    # Same leak-magnitude reasoning as the comment in
    # test_realized_pick_fractions_match_intended_weights: "near"'s
    # candidate-restricted mass is ~exp(-100/6) ~= 5.8e-8 of its global
    # mass, so its realized share collapses toward 0 regardless of its
    # intended 0.30 weight. Bounds below are deliberately loose (an order
    # of magnitude from both the 0.30/0.70 intended split and the
    # ~0.0004/0.9996 observed against the real pre-fix file) so this is a
    # robust, non-flaky regression guard rather than a repeat of the tight
    # tolerance check above.
    assert realized_near < 0.02, (
        f"expected legacy whole-grid normalization to starve the "
        f"near-origin component well below its intended 0.30 share; "
        f"got {realized_near}"
    )
    assert realized_far > 0.98, (
        f"expected legacy whole-grid normalization to inflate the "
        f"far-end component well above its intended 0.70 share; "
        f"got {realized_far}"
    )
