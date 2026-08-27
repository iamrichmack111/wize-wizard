from __future__ import annotations
from dataclasses import dataclass
from math import ceil, sqrt, floor
from statistics import NormalDist

LAFLEY = [
    "What is Winning?",
    "Where Will I Play?",
    "What Tools Do I Need?",
    "What Management System Do I Need?",
    "What Skills Do I Need?",
]
# Original Wize ladder, clarified around the user's desired escalation.
# A concrete Need is the goal; repeated strategic Why passes expand it into
# increasingly aspirational Wish, Dream, and Fantasy statements.
LEVELS = ["Need", "Wish", "Dream", "Fantasy"]

@dataclass
class PertResult:
    expected: float
    sigma: float
    low_stress: float
    high_stress: float
    mode: str
    confidence_sentence: str
    optimistic: float = 0.0
    pessimistic: float = 0.0

    @property
    def range_68(self) -> tuple[float, float]:
        return (max(0.0, self.expected - self.sigma), self.expected + self.sigma)

    @property
    def range_95(self) -> tuple[float, float]:
        return (max(0.0, self.expected - 2*self.sigma), self.expected + 2*self.sigma)

    @property
    def range_997(self) -> tuple[float, float]:
        return (max(0.0, self.expected - 3*self.sigma), self.expected + 3*self.sigma)

    def finish_by(self, probability: float) -> float:
        """Normal-approximation completion time for a requested cumulative probability."""
        if self.sigma <= 0:
            return self.expected
        probability = min(max(probability, 0.0001), 0.9999)
        return max(0.0, self.expected + NormalDist().inv_cdf(probability) * self.sigma)

    def probability_by(self, duration: float) -> float:
        """Approximate probability of finishing by duration under a normal approximation."""
        if self.sigma <= 0:
            return 1.0 if duration >= self.expected else 0.0
        return NormalDist(mu=self.expected, sigma=self.sigma).cdf(duration)

    @property
    def chance_rows(self) -> list[tuple[int, float]]:
        return [(68, self.expected + self.sigma), (95, self.expected + 2*self.sigma), (99.7, self.expected + 3*self.sigma)]

    @property
    def aggressive_16(self) -> float:
        return max(0.0, self.expected - self.sigma)

    @property
    def very_aggressive_2(self) -> float:
        return max(0.0, self.expected - 2*self.sigma)

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
    """Build a deliberately simple managed communication structure.

    Wize keeps some *pairwise stability* instead of turning every group into a
    pure hub-and-spoke network. A normal group has a Manager and Product Lead,
    contributors report through the Product Lead, and contributors are paired
    into stable working pairs where possible. If the grouping leaves a
    remainder, the remainder becomes a coordination-management layer as the
    original Wize rule requires.

    This is a planning heuristic, not a universal organization-design law.
    """
    if n < 1:
        raise ValueError("People must be at least 1")
    raw = channels(n)
    g = suggest_group_size(n)
    full_groups, remainder = divmod(n, g) if g else (0, 0)

    if full_groups == 0:
        group_sizes = [n]
        coordinators = 0
        remainder = 0
    else:
        group_sizes = [g] * full_groups
        coordinators = remainder

    groups = len(group_sizes)
    local_managers = sum(1 for size in group_sizes if size >= 1)
    product_leaders = sum(1 for size in group_sizes if size >= 2)
    workers_by_group = [max(size - 2, 0) if size >= 2 else 0 for size in group_sizes]
    workers = sum(workers_by_group)

    # A manager/product-lead pair anchors every multi-person group.
    management_spine = product_leaders
    # Contributors coordinate through the Product Lead.
    delivery_channels = workers
    # Preserve a small amount of peer-to-peer stability with fixed buddy pairs.
    stable_pair_channels = sum(floor(w / 2) for w in workers_by_group)

    if coordinators:
        manager_pairwise = 0
        coordinator_oversight = local_managers
        coordinator_channels = channels(coordinators)
        role_note = (
            f"The {coordinators}-person remainder becomes a coordination-management layer above "
            f"the {local_managers} group manager(s)."
        )
    else:
        # Group managers retain pairwise coordination with one another.
        manager_pairwise = channels(local_managers)
        coordinator_oversight = 0
        coordinator_channels = 0
        role_note = (
            f"There is no remainder layer, so the {local_managers} group manager(s) coordinate "
            "pairwise with one another when more than one group exists."
        )

    structured = (management_spine + delivery_channels + stable_pair_channels +
                  manager_pairwise + coordinator_oversight + coordinator_channels)
    reduction = max(0, raw - structured)
    reduction_pct = (reduction / raw * 100.0) if raw else 0.0
    management_total = local_managers + product_leaders + coordinators
    management_ratio = (management_total / n * 100.0) if n else 0.0
    avg_span = (workers / product_leaders) if product_leaders else 0.0

    sentence = (
        f"With {n} people, an all-to-all network has {raw} possible communication lines. "
        f"Wize creates {groups} working group(s) with {local_managers} Manager role(s) and "
        f"{product_leaders} Product Lead role(s). The Product Lead coordinates {workers} contributor role(s), "
        f"with an average delivery span of {avg_span:.2f}. To keep the group from becoming a fragile hub-and-spoke system, "
        f"Wize preserves {stable_pair_channels} stable contributor-pair line(s). {role_note} "
        f"The managed structure uses {structured} communication lines instead of {raw}, a reduction of "
        f"{reduction} lines ({reduction_pct:.1f}%)."
    )
    return {
        "people": n, "channels": raw, "group_size": g, "groups": groups,
        "remainder": remainder, "managers": coordinators,
        "local_supervisors": local_managers, "local_managers": local_managers,
        "product_leaders": product_leaders, "workers": workers,
        "local_management_channels": management_spine + delivery_channels,
        "management_spine": management_spine, "delivery_channels": delivery_channels,
        "stable_pair_channels": stable_pair_channels,
        "supervisor_coordination": manager_pairwise,
        "oversight": coordinator_oversight, "manager_channels": coordinator_channels,
        "structured": structured, "reduction": reduction, "reduction_pct": reduction_pct,
        "management_total": management_total, "management_ratio": management_ratio,
        "avg_span": avg_span, "sentence": sentence,
    }

