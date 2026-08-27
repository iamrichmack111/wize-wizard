from wize_wizard.models import communications_report, pert_three_point


def test_group_has_manager_product_lead_and_stable_pair():
    r = communications_report(4)
    assert r["local_managers"] == 1
    assert r["product_leaders"] == 1
    assert r["workers"] == 2
    assert r["stable_pair_channels"] == 1
    assert r["structured"] < r["channels"]


def test_remainder_becomes_coordination_management():
    r = communications_report(10)
    assert r["remainder"] == 2
    assert r["managers"] == 2
    assert r["local_managers"] == 2
    assert r["product_leaders"] == 2
    assert r["structured"] < r["channels"]


def test_pert_probability_deadlines_increase_with_confidence():
    r = pert_three_point(20, 27.5, 35)
    p68 = r.finish_by(.68)
    p80 = r.finish_by(.80)
    p95 = r.finish_by(.95)
    assert r.expected == 27.5
    assert p68 < p80 < p95
    assert 0.67 <= r.probability_by(p68) <= 0.69
