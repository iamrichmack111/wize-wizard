from __future__ import annotations
from dataclasses import dataclass
from math import ceil, sqrt

LAFLEY = [
    "What is Winning?",
    "Where Will I Play?",
    "What Tools Do I Need?",
    "What Skills Do I Need?",
    "What Management Systems Do I Need?",
]
LEVELS = ["Initial Need", "Want", "Wish", "Dream"]

@dataclass
class PertResult:
    expected: float
    sigma: float
    low_stress: float
    high_stress: float
    mode: str
    confidence_sentence: str

    # These ranges are Wize Wizard planning envelopes, not mean-centered
    # confidence intervals. They expand outward from the entered Best/Worst
    # boundaries, with the lower bound clamped at zero.
    optimistic: float = 0.0
    pessimistic: float = 0.0

    @property
    def range_68(self) -> tuple[float, float]:
        return (max(0.0, self.optimistic - self.sigma), self.pessimistic + self.sigma)

    @property
    def range_95(self) -> tuple[float, float]:
        return (max(0.0, self.optimistic - 2*self.sigma), self.pessimistic + 2*self.sigma)

    @property
    def range_997(self) -> tuple[float, float]:
        return (max(0.0, self.optimistic - 3*self.sigma), self.pessimistic + 3*self.sigma)


def confidence_summary(o: float, m: float, p: float, expected: float, sigma: float) -> str:
    base = max(expected, 1e-9)
    spread_ratio = (p - o) / base
    best_ratio = o / base
    likely_ratio = m / base
    worst_ratio = p / base
    if spread_ratio <= 0.25:
        band = "tight"
        confidence = "high"
    elif spread_ratio <= 0.75:
        band = "moderate"
        confidence = "moderate"
    else:
        band = "wide"
        confidence = "low"
    return (
        f"Estimate confidence is {confidence}: the best case is {best_ratio:.0%} of the PERT mean, "
        f"the most-likely estimate is {likely_ratio:.0%}, and the worst case is {worst_ratio:.0%}; "
        f"the total best-to-worst spread is {spread_ratio:.0%} of the expected duration, which is a {band} uncertainty band, "
        f"with σ={sigma:.2f}."
    )


def pert_three_point(o: float, m: float, p: float, severity: int = 3) -> PertResult:
    expected = (o + 4*m + p) / 6
    sigma = max((p - o) / 6, 0.0)
    # Wize Wizard stress convention, distinct from standard statistical terminology.
    # Wize stress convention: expand outward from the entered range.
    # 2σ below Best is the aggressive/high-stress lower boundary; never < 0.
    # 3σ above Worst is the maximum low-stress planning allowance.
    high_stress = max(0.0, o - 2*sigma)
    low_stress = p + 3*sigma
    spread = (p-o)/max(m, 1e-9)
    mode = "6-point" if severity >= 4 or spread >= 1.0 else "3-point"
    return PertResult(expected, sigma, low_stress, high_stress, mode, confidence_summary(o,m,p,expected,sigma), o, p)


def derive_estimates(best: float, pessimistic: float | None = None, severity: int = 3) -> tuple[float, float, float, PertResult, bool]:
    """Return a coherent three-point estimate.

    If pessimistic is omitted, Wize Wizard derives it as 2×best.
    Most-likely is always the midpoint between best and pessimistic.
    The final boolean indicates whether pessimistic was derived.
    """
    o = best
    derived = pessimistic is None
    p = best * 2.0 if derived else pessimistic
    if p is None or p < o:
        raise ValueError("Pessimistic estimate must be at least the best-case estimate")
    m = (o + p) / 2.0
    return o, m, p, pert_three_point(o, m, p, severity), derived


def derive_from_best(best: float, severity: int = 3) -> tuple[float, float, float, PertResult]:
    """Backward-compatible sparse-input helper."""
    o, m, p, result, _ = derive_estimates(best, None, severity)
    return o, m, p, result


def channels(n: int) -> int:
    return n * (n - 1) // 2


def suggest_group_size(n: int, max_group: int = 6) -> int:
    if n <= max_group:
        return n
    return min(max_group, max(2, ceil(sqrt(n))))


def communications_report(n: int) -> dict[str, float | int | str]:
    raw = channels(n)
    g = suggest_group_size(n)
    groups = max(1, ceil(n / g))
    sizes = [min(g, n - i*g) for i in range(groups)]
    internal = sum(channels(s) for s in sizes)
    lead_channels = channels(groups) if groups > 1 else 0
    structured = internal + lead_channels
    reduction = max(0, raw - structured)
    reduction_pct = (reduction / raw * 100.0) if raw else 0.0
    sentence = (
        f"With {n} people, an unstructured all-to-all network creates {raw} possible communication lines. "
        f"Splitting the team into {groups} group(s) of about {g} people yields approximately {internal} internal lines plus "
        f"{lead_channels} lead-to-lead lines, or {structured} structured lines total, reducing potential communication load by "
        f"{reduction} lines ({reduction_pct:.1f}%)."
    )
    return {"people": n, "channels": raw, "group_size": g, "groups": groups, "internal": internal,
            "lead_channels": lead_channels, "structured": structured, "reduction": reduction,
            "reduction_pct": reduction_pct, "sentence": sentence}
