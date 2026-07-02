"""Wave B H7: plan limits scale per tier instead of binary trial/not-trial
(a Starter customer must NOT get Enterprise-level access)."""

from backend.billing_plans import limits_for, PLAN_LIMITS


def test_trial_limits_unchanged():
    l = limits_for("trial")
    assert l["max_uploads"] == 3
    assert l["max_frameworks"] == 1
    assert l["max_users"] == 3


def test_tiers_scale_up():
    assert limits_for("starter")["max_uploads"] > limits_for("trial")["max_uploads"]
    assert limits_for("growth")["max_frameworks"] > limits_for("starter")["max_frameworks"]
    assert limits_for("growth")["max_users"] > limits_for("starter")["max_users"]


def test_enterprise_is_unlimited():
    l = limits_for("enterprise")
    assert l["max_uploads"] is None
    assert l["max_frameworks"] is None
    assert l["max_users"] is None


def test_unknown_plan_defaults_to_trial():
    assert limits_for("bogus") == PLAN_LIMITS["trial"]
    assert limits_for(None) == PLAN_LIMITS["trial"]
    assert limits_for("") == PLAN_LIMITS["trial"]
