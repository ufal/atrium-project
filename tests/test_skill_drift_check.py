"""Tests for tools/skill_drift_check.py's client check: the 502 rule of the skill clients (#77 C)."""

from __future__ import annotations

import sys
from pathlib import Path

_HUB_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HUB_ROOT / "tools"))

import skill_drift_check as sdc  # noqa: E402

SKELETON = _HUB_ROOT / "docs" / "templates" / "skill" / "atrium_client.skeleton.py"

OLD_CLIENT = """
RETRY_STATUS = {502, 503, 504}
RETRY_ATTEMPTS = 3

def http_json(url):
    if e.code in RETRY_STATUS and attempt < RETRY_ATTEMPTS:
        pass
"""


def test_the_skeleton_follows_its_own_rule():
    assert sdc.client_retry_rule("scripts/atrium_x.py", SKELETON.read_text(encoding="utf-8")) is None


def test_a_client_that_retries_every_502_is_a_finding():
    finding = sdc.client_retry_rule("scripts/atrium_old.py", OLD_CLIENT)
    assert finding is not None and "scripts/atrium_old.py" in finding and "RETRY_502_REASONS" in finding


def test_naming_the_set_without_the_function_is_not_enough():
    text = OLD_CLIENT + '\nRETRY_502_REASONS = {"upstream_unavailable"}\n'
    assert sdc.client_retry_rule("scripts/atrium_old.py", text) is not None


def test_a_client_that_does_not_retry_502_needs_no_rule():
    assert sdc.client_retry_rule("scripts/atrium_y.py", "RETRY_STATUS = {503, 504}\n") is None
    assert sdc.client_retry_rule("scripts/atrium_y.py", "print('no retries')\n") is None


def test_only_the_skill_clients_are_checked():
    assert sdc.CLIENT_PATH.match("scripts/atrium_convert.py")
    assert sdc.CLIENT_PATH.match("scripts/atrium_keywords.py")
    assert not sdc.CLIENT_PATH.match("scripts/server.sh")
    assert not sdc.CLIENT_PATH.match("tools/atrium_helper.py")
