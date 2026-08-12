"""Tier restructure (The Angle §4): FREE / STARTER / PRO fences, with
legacy trial/growth rows resolving through aliases. A Starter customer
must NOT get Pro-level access, and Free is preview-only."""

from backend.billing_plans import PLAN_LIMITS, limits_for, plan_features, resolve_plan


def test_free_is_preview_only():
    l = limits_for("free")
    assert l["max_generations_total"] == 1
    assert l["docx_export"] is False
    assert l["full_gap_list"] is False
    assert l["haiku_only"] is True
    assert l["watermark"] is True
    assert l["max_users"] == 1
    assert l["max_frameworks"] == 1


def test_starter_exports_but_stays_fenced():
    l = limits_for("starter")
    assert l["docx_export"] is True
    assert l["max_docs_per_month"] == 10
    assert l["max_generations_total"] is None
    assert l["full_gap_list"] is False
    assert l["haiku_only"] is False
    assert l["watermark"] is False
    assert l["max_frameworks"] == 1
    assert l["max_users"] == 1


def test_pro_unlocks_everything_mapped():
    l = limits_for("pro")
    assert l["docx_export"] is True
    assert l["full_gap_list"] is True
    assert l["max_docs_per_month"] is None
    assert l["max_frameworks"] is None
    assert l["max_users"] == 3


def test_enterprise_is_unlimited():
    l = limits_for("enterprise")
    assert l["max_uploads"] is None
    assert l["max_frameworks"] is None
    assert l["max_users"] is None


def test_legacy_aliases_resolve():
    assert resolve_plan("trial") == "free"
    assert resolve_plan("growth") == "pro"
    assert limits_for("trial") == PLAN_LIMITS["free"]
    assert limits_for("growth") == PLAN_LIMITS["pro"]
    assert resolve_plan("  PRO ") == "pro"


def test_unknown_plan_defaults_to_free():
    assert limits_for("bogus") == PLAN_LIMITS["free"]
    assert limits_for(None) == PLAN_LIMITS["free"]
    assert limits_for("") == PLAN_LIMITS["free"]


def test_plan_features_shape():
    feats = plan_features("free")
    assert feats == {
        "docx_export": False,
        "full_gap_list": False,
        "haiku_only": True,
        "watermark": True,
    }
    assert plan_features("pro")["full_gap_list"] is True
