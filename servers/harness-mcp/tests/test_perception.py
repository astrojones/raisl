"""Tests for the perception daemon (perception.py): scheduling, snapshotting, baseline."""

from __future__ import annotations

import anyio
from repo_agent_harness import perception
from repo_agent_harness.models import (
    CheckVerdict,
    GitState,
    HealthCheckConfig,
    HealthConfig,
    PerceptionSnapshot,
)


def test_due_first_run_is_always_true():
    p = perception.Perception("/tmp/repo")
    assert p._due("lint", 30.0, 8.0, now=1000.0) is True


def test_due_respects_min_interval():
    p = perception.Perception("/tmp/repo")
    p._last_run["lint"] = 1000.0
    p._last_runtime_s["lint"] = 0.0
    assert p._due("lint", 30.0, 0.0, now=1020.0) is False  # 20s < 30s floor
    assert p._due("lint", 30.0, 0.0, now=1031.0) is True  # 31s >= 30s floor


def test_due_adaptive_factor_scales_with_runtime():
    p = perception.Perception("/tmp/repo")
    p._last_run["slow"] = 1000.0
    p._last_runtime_s["slow"] = 5.0  # last run took 5s -> 8x => 40s interval
    assert p._due("slow", 0.0, 8.0, now=1030.0) is False
    assert p._due("slow", 0.0, 8.0, now=1041.0) is True


def test_write_read_roundtrip(repo):
    p = perception.Perception(str(repo))
    snap = PerceptionSnapshot(
        verdicts=[CheckVerdict(id="lint", kind="lint", ok=False, summary="E501")],
        git=GitState(branch="main", head="abc1234"),
    )
    p._write(snap)
    loaded = perception.read_snapshot(str(repo))
    assert loaded is not None
    assert loaded.verdicts[0].ok is False
    assert loaded.verdicts[0].summary == "E501"
    assert loaded.git.branch == "main"


def test_read_snapshot_absent_is_none(repo):
    assert perception.read_snapshot(str(repo)) is None


def test_current_state_baseline_without_snapshot(repo):
    state = perception.current_state(str(repo))
    assert state["verdicts"] == []
    assert state["git"]["branch"]  # a real branch from the git repo
    assert state["generated_at"]


def test_refresh_runs_only_auto_runnable_checks_and_writes(repo, monkeypatch):
    cfg = HealthConfig(
        checks=[
            HealthCheckConfig(id="lint", kind="lint", auto=True),
            HealthCheckConfig(id="tests", kind="test", auto=False),  # not auto -> skipped
            HealthCheckConfig(id="worktree", kind="git", auto=True),  # auto but not runnable -> skipped
        ]
    )
    monkeypatch.setattr(perception.health, "load_config", lambda root: cfg)
    ran: list[str] = []

    def fake_run_kind(root, kind):
        ran.append(kind)
        return {"ok": False, "skipped": False, "command": "ruff check", "output": "E501 line too long\nmore"}

    monkeypatch.setattr(perception.verify, "run_kind", fake_run_kind)
    anyio.run(perception.Perception(str(repo))._refresh)

    assert ran == ["lint"]  # only the auto + runnable check ran
    snap = perception.read_snapshot(str(repo))
    assert snap is not None
    verdicts = {v.id: v for v in snap.verdicts}
    assert verdicts["lint"].ok is False
    assert "E501" in verdicts["lint"].summary
    assert snap.git.branch  # git state always captured


def test_refresh_marks_skipped_check_ok_none(repo, monkeypatch):
    cfg = HealthConfig(checks=[HealthCheckConfig(id="lint", kind="lint", auto=True)])
    monkeypatch.setattr(perception.health, "load_config", lambda root: cfg)
    monkeypatch.setattr(
        perception.verify,
        "run_kind",
        lambda root, kind: {"ok": True, "skipped": True, "command": None, "output": "no lintable files"},
    )
    anyio.run(perception.Perception(str(repo))._refresh)
    snap = perception.read_snapshot(str(repo))
    assert snap is not None
    assert snap.verdicts[0].ok is None  # skipped -> unknown, not a failure
