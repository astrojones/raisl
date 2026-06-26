"""Stable paths for harness persistent state (~/.harness by default)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def repo_id(root: str) -> str:
    """Short stable identifier for the repo (SHA-256 of realpath, first 12 hex chars)."""
    return hashlib.sha256(os.path.realpath(root).encode()).hexdigest()[:12]


def harness_home() -> Path:
    """Root of harness persistent state; override via REPO_AGENT_HARNESS_HOME."""
    env = os.environ.get("REPO_AGENT_HARNESS_HOME")
    return Path(env) if env else Path.home() / ".harness"


def repo_state_dir(root: str) -> Path:
    """Per-repo state dir under harness_home(); created lazily with mode 0700."""
    d = harness_home() / "repos" / repo_id(root)
    d.mkdir(parents=True, exist_ok=True)
    d.chmod(0o700)
    return d


# Perception-layer state files under repo_state_dir(). Named here (in this light module,
# no heavy imports) so the daemon (perception.py) and the delivery hooks (agent_hooks.py)
# agree on locations without the hook hot-path importing the daemon.
PERCEPTION_FILE = "perception.json"
PERCEPTION_LAST_SEEN_FILE = "perception_last_seen.json"
PERCEPTION_TOUCHED_FILE = "perception_touched.json"


def perception_file(root: str) -> Path:
    """Path to the current perception snapshot written by the daemon."""
    return repo_state_dir(root) / PERCEPTION_FILE


def perception_last_seen_file(root: str) -> Path:
    """Path to the marker recording the snapshot last surfaced to the agent (UserPromptSubmit)."""
    return repo_state_dir(root) / PERCEPTION_LAST_SEEN_FILE


def perception_touched_file(root: str) -> Path:
    """Path to the set of files the agent has edited this session (PostToolUse attribution)."""
    return repo_state_dir(root) / PERCEPTION_TOUCHED_FILE
