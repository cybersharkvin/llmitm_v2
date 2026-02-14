"""Tests for target profile registry and multi-target exploit step generation."""

import pytest

from llmitm_v2.target_profiles import TARGET_PROFILES, get_active_profile
from llmitm_v2.tools.exploit_tools import (
    _auth_offset,
    _login_and_auth_steps,
    auth_strip_steps,
    idor_walk_steps,
    token_swap_steps,
)


@pytest.fixture
def juice():
    return TARGET_PROFILES["juice_shop"]


@pytest.fixture
def nodegoat():
    return TARGET_PROFILES["nodegoat"]


@pytest.fixture
def dvwa():
    return TARGET_PROFILES["dvwa"]


def test_all_profiles_have_required_fields():
    for p in TARGET_PROFILES.values():
        assert p.login_path and p.user_a.username and p.user_b.username


def test_bearer_profile_has_extraction_pattern(juice):
    assert juice.token_extraction_pattern is not None


def test_cookie_profile_has_cookie_name(nodegoat):
    assert nodegoat.session_cookie_name == "connect.sid"


def test_get_active_profile_unknown_raises():
    with pytest.raises(ValueError, match="Unknown target profile"):
        get_active_profile("nonexistent")


def test_auth_offset_bearer_is_2(juice):
    assert _auth_offset(juice) == 2


def test_auth_offset_cookie_is_1(nodegoat):
    assert _auth_offset(nodegoat) == 1


def test_auth_offset_csrf_is_3(dvwa):
    assert _auth_offset(dvwa) == 3


def test_idor_walk_bearer_produces_5_steps(juice):
    assert len(idor_walk_steps("/api/Users/1", "test", juice)) == 5


def test_idor_walk_cookie_produces_4_steps(nodegoat):
    assert len(idor_walk_steps("/allocations/1", "test", nodegoat)) == 4


def test_idor_walk_csrf_produces_6_steps(dvwa):
    assert len(idor_walk_steps("/vuln/1", "test", dvwa)) == 6


def test_cookie_steps_lack_authorization_header(nodegoat):
    steps = idor_walk_steps("/allocations/1", "test", nodegoat)
    for s in steps:
        assert "Authorization" not in s.parameters.get("headers", {})


def test_token_swap_raises_for_cookie_auth(nodegoat):
    with pytest.raises(ValueError, match="bearer_token"):
        token_swap_steps("/allocations/1", "test", nodegoat)


def test_auth_strip_cookie_has_skip_cookies_step(nodegoat):
    steps = auth_strip_steps("/allocations/1", "test", nodegoat)
    no_auth = [s for s in steps if "skip_cookies" in s.parameters]
    assert len(no_auth) == 1 and no_auth[0].parameters["skip_cookies"] is True


def test_login_steps_bearer_produces_2(juice):
    assert len(_login_and_auth_steps(juice, "a")) == 2


def test_login_steps_cookie_produces_1(nodegoat):
    assert len(_login_and_auth_steps(nodegoat, "a")) == 1


def test_login_steps_csrf_produces_3(dvwa):
    assert len(_login_and_auth_steps(dvwa, "a")) == 3
