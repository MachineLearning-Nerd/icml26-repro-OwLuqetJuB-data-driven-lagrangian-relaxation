"""Clean-room numerical primitives for the paper's finite MILP family."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def dual_values(
    pi: np.ndarray,
    c: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    feasible_x: np.ndarray,
) -> tuple[float, int, np.ndarray]:
    """Enumerate a finite Lagrangian subproblem exactly."""
    slopes = b[None, :] - feasible_x @ a.T
    values = feasible_x @ c + slopes @ pi
    winner = int(np.argmin(values))
    return float(values[winner]), winner, slopes[winner].copy()


def hard_dual(pi: np.ndarray, c: np.ndarray) -> float:
    """Dual value for A=I, b=1/2, x in {0,1}^s."""
    pi = np.asarray(pi, dtype=float)
    c = np.asarray(c, dtype=float)
    return float(np.minimum(pi / 2.0, c - pi / 2.0).sum())


def hard_supergradient(pi: np.ndarray, c: np.ndarray) -> np.ndarray:
    """A valid supergradient using the x=0 tie-breaking rule."""
    return 0.5 - (np.asarray(pi) > np.asarray(c)).astype(float)


def expected_hard_utility(pi: np.ndarray, p_high: np.ndarray, low=1.0, high=2.0) -> float:
    pi = np.asarray(pi, dtype=float)
    p_high = np.broadcast_to(np.asarray(p_high, dtype=float), pi.shape)
    low_value = np.minimum(pi / 2.0, low - pi / 2.0)
    high_value = np.minimum(pi / 2.0, high - pi / 2.0)
    return float(((1.0 - p_high) * low_value + p_high * high_value).sum())


def population_optimum(p_high: np.ndarray, low=1.0, high=2.0) -> np.ndarray:
    p_high = np.asarray(p_high, dtype=float)
    return np.where(p_high > 0.5, high, low)


def expected_excess(pi: np.ndarray, p_high: np.ndarray, low=1.0, high=2.0) -> float:
    optimum = population_optimum(np.broadcast_to(p_high, np.asarray(pi).shape), low, high)
    return expected_hard_utility(optimum, p_high, low, high) - expected_hard_utility(
        pi, p_high, low, high
    )


def scalar_expected_excess(pi: np.ndarray, p_high: float, low=1.0, high=2.0) -> np.ndarray:
    """Vectorized one-coordinate excess risk, used for raw SGA trajectories."""
    pi = np.asarray(pi, dtype=float)
    opt = high if p_high > 0.5 else low
    def utility(x: np.ndarray) -> np.ndarray:
        return (1.0 - p_high) * np.minimum(x / 2.0, low - x / 2.0) + p_high * np.minimum(
            x / 2.0, high - x / 2.0
        )
    return utility(np.full_like(pi, opt)) - utility(pi)


def averaged_sga_scalar(
    *, n: int, p_high: float, repeats: int, seed: int, pi_max: float = 2.0, b_bound: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """Run Algorithm 1 independently for many scalar coordinates.

    Separability makes a full s-coordinate risk exactly s times this scalar risk.
    """
    rng = np.random.default_rng(seed)
    eta = pi_max / (2.0 * b_bound * math.sqrt(n))
    pi = np.zeros(repeats, dtype=np.float64)
    running = np.zeros_like(pi)
    for _ in range(n):
        running += pi
        c = np.where(rng.random(repeats) < p_high, 2.0, 1.0)
        grad = 0.5 - (pi > c).astype(np.float64)
        pi = np.clip(pi + eta * grad, 0.0, pi_max)
    averaged = running / n
    return averaged, scalar_expected_excess(averaged, p_high)


def warm_start_errors(
    *, n: int, p_high: float, repeats: int, seed: int
) -> np.ndarray:
    """Raw scalar squared errors of the empirical-mean warm start."""
    rng = np.random.default_rng(seed)
    high_counts = rng.binomial(n, p_high, size=repeats)
    estimate = 1.0 + high_counts / n
    truth = 1.0 + p_high
    return np.square(estimate - truth)


def erm_scalar_excess(
    *, n: int, p_high: float, repeats: int, seed: int, low=1.0, high=2.0
) -> tuple[np.ndarray, np.ndarray]:
    """Raw ERM decisions and population excess for the separable hard family."""
    rng = np.random.default_rng(seed)
    high_counts = rng.binomial(n, p_high, size=repeats)
    # Minimum-norm tie breaking selects the low breakpoint.
    estimates = np.where(high_counts > n / 2, high, low)
    return estimates, scalar_expected_excess(estimates, p_high, low, high)


def bernoulli_kl(epsilon: float) -> float:
    """KL(Ber((1+eps)/2) || Ber((1-eps)/2))."""
    return epsilon * math.log((1.0 + epsilon) / (1.0 - epsilon))


def greedy_hamming_packing(s: int, seed: int = 26754) -> np.ndarray:
    """Construct the Varshamov-sized packing used by the Fano certificate."""
    target = 2 ** (s // 8)
    min_distance = s // 8
    rng = np.random.default_rng(seed + s)
    selected = [np.zeros(s, dtype=np.uint8)]
    attempts = 0
    while len(selected) < target and attempts < 2_000_000:
        candidate = rng.integers(0, 2, size=s, dtype=np.uint8)
        if all(np.count_nonzero(candidate != row) >= min_distance for row in selected):
            selected.append(candidate)
        attempts += 1
    if len(selected) != target:
        raise RuntimeError(f"packing construction stopped at {len(selected)}/{target}")
    return np.stack(selected)


def pairwise_hamming(rows: np.ndarray) -> np.ndarray:
    distances = []
    for i in range(len(rows)):
        distances.extend(np.count_nonzero(rows[i + 1 :] != rows[i], axis=1).tolist())
    return np.asarray(distances, dtype=np.int64)


def fano_certificate(s: int, n: int, packing: np.ndarray, kappa: float = 0.07) -> dict:
    eps = kappa / math.sqrt(n)
    distances = pairwise_hamming(packing)
    log_m = math.log(len(packing))
    exact_kl_max = n * int(distances.max()) * bernoulli_kl(eps)
    paper_kl_envelope = 4.0 * n * s * eps**2
    fano_error = 1.0 - (paper_kl_envelope + math.log(2.0)) / log_m
    direct_lower = max(0.0, fano_error) * eps * float(distances.min()) / 4.0
    warm_lower = max(0.0, fano_error) * eps**2 * float(distances.min()) / 4.0
    return {
        "s": s,
        "n": n,
        "epsilon": eps,
        "packing_size": int(len(packing)),
        "pair_count": int(len(distances)),
        "min_hamming": int(distances.min()),
        "max_hamming": int(distances.max()),
        "log_packing_size": log_m,
        "exact_kl_max": exact_kl_max,
        "paper_kl_envelope": paper_kl_envelope,
        "exact_kl_below_envelope": exact_kl_max <= paper_kl_envelope + 1e-12,
        "fano_error_lower": fano_error,
        "direct_risk_lower": direct_lower,
        "direct_normalized": direct_lower / (s / math.sqrt(n)),
        "warm_risk_lower": warm_lower,
        "warm_normalized": warm_lower / (s / n),
    }


def dudley_integral(b_bound: float, pi_max: float, s: int, order: int = 64) -> dict:
    """Numerically integrate the paper's entropy integral with Gauss-Laguerre."""
    lipschitz = 2.0 * b_bound * math.sqrt(s)
    diameter = pi_max * math.sqrt(s)
    radius = lipschitz * diameter
    nodes, weights = np.polynomial.laguerre.laggauss(order)
    integral = radius * float(np.sum(weights * np.sqrt(math.log(3.0) + nodes)))
    paper_envelope = 3.0 * radius * math.sqrt(math.pi) / 2.0
    return {
        "s": s,
        "lipschitz": lipschitz,
        "diameter": diameter,
        "radius": radius,
        "integral": integral,
        "paper_envelope": paper_envelope,
        "below_envelope": integral <= paper_envelope,
    }


def fit_log_slope(xs: Iterable[float], ys: Iterable[float]) -> float:
    x = np.log(np.asarray(list(xs), dtype=float))
    y = np.log(np.asarray(list(ys), dtype=float))
    return float(np.polyfit(x, y, 1)[0])
