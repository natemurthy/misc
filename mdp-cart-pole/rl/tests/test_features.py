"""Unit tests for the state representations in common/features.py."""

import math

import numpy as np

from common import GridDiscretizer, boxes_index, normalize_obs, N_BOXES


def test_grid_index_bounds_and_shape():
    g = GridDiscretizer((1, 1, 8, 16))
    assert g.n_states == 128
    idx = g.index(np.array([0.0, 0.0, 0.0, 0.0]))
    assert len(idx) == 4 and idx[0] == 0 and idx[1] == 0
    # extremes clip into the outermost bins rather than indexing out of range
    lo = g.index(np.array([-9, -9, -9, -9]))
    hi = g.index(np.array([9, 9, 9, 9]))
    assert lo == (0, 0, 0, 0)
    assert hi == (0, 0, 7, 15)


def test_grid_flat_is_consistent_with_index():
    g = GridDiscretizer((3, 3, 8, 16))
    obs = np.array([1.0, -0.5, 0.05, 1.0])
    assert g.flat(obs) == int(np.ravel_multi_index(g.index(obs), g.bins))
    assert 0 <= g.flat(obs) < g.n_states


def test_boxes_covers_all_162_regions():
    xs = [-2.0, 0.0, 2.0]
    xds = [-1.0, 0.0, 1.0]
    ths = [math.radians(d) for d in (-9, -3, -0.5, 0.5, 3, 9)]
    thds = [math.radians(d) for d in (-80, 0, 80)]
    seen = {boxes_index([x, xd, th, thd]) for x in xs for xd in xds for th in ths for thd in thds}
    assert seen == set(range(N_BOXES))


def test_boxes_returns_minus_one_outside_failure_thresholds():
    assert boxes_index([2.5, 0, 0, 0]) == -1
    assert boxes_index([0, 0, math.radians(13), 0]) == -1
    assert boxes_index([0, 0, 0, 0]) >= 0


def test_boxes_angle_boundaries_match_paper():
    """Neighbouring angles on either side of the 1 and 6 degree boundaries land in different boxes."""
    def box_theta(deg):
        return boxes_index([0, 0, math.radians(deg), 0])
    assert box_theta(-0.5) != box_theta(0.5)  # 0 boundary
    assert box_theta(0.9) != box_theta(1.1)  # 1 degree boundary
    assert box_theta(5.9) != box_theta(6.1)  # 6 degree boundary
    assert box_theta(2) == box_theta(5)  # same region inside [1, 6)


def test_normalize_obs_scales_to_unit_range():
    obs = np.array([2.4, 3.0, 0.21, 3.5])
    assert np.allclose(normalize_obs(obs), [1, 1, 1, 1])
    assert np.allclose(normalize_obs(-obs), [-1, -1, -1, -1])
