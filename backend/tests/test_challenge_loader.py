"""Unit tests for the challenge loader service."""

import tempfile
from pathlib import Path

import pytest
import yaml

from app.services.challenge_loader import (
    _validate_challenge,
    get_all_challenges,
    get_challenge_by_id,
    load_challenges,
)

VALID_CHALLENGE = {
    "id": "test-001",
    "title": "Test Challenge",
    "description": "A test challenge.",
    "domain": "langchain",
    "difficulty": "intermediate",
    "mode": "socratic",
    "category": "training",
    "tags": ["test"],
    "rubric": {"arch": {"weight": 0.5}},
    "test_cases": [{"name": "basic", "code": "assert True"}],
    "reference_solution": "print('hello')",
}


class TestLoadChallenges:
    def test_load_from_project_dir(self):
        """Load challenges from the actual challenges directory."""
        result = load_challenges()
        assert len(result) > 0

    def test_load_from_custom_dir(self):
        """Load challenges from a temp directory with a valid YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.yaml"
            with open(filepath, "w") as f:
                yaml.dump(VALID_CHALLENGE, f)

            result = load_challenges(Path(tmpdir))
            assert len(result) == 1
            assert "test-001" in result

    def test_load_empty_dir(self):
        """Loading from an empty directory returns empty dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_challenges(Path(tmpdir))
            assert len(result) == 0

    def test_load_nonexistent_dir(self):
        """Loading from a missing directory returns empty dict."""
        result = load_challenges(Path("/tmp/nonexistent_dir_abc123"))
        assert len(result) == 0

    def test_duplicate_ids_skipped(self):
        """When two files have the same id, only the first is loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("a.yaml", "b.yaml"):
                filepath = Path(tmpdir) / name
                with open(filepath, "w") as f:
                    yaml.dump(VALID_CHALLENGE, f)

            result = load_challenges(Path(tmpdir))
            assert len(result) == 1


class TestValidateChallenge:
    def test_valid_challenge(self):
        """A challenge with all required fields passes validation."""
        assert _validate_challenge(VALID_CHALLENGE, Path("test.yaml")) is True

    def test_missing_fields(self):
        """A challenge missing required fields fails validation."""
        incomplete = {"id": "test-002", "title": "Incomplete"}
        assert _validate_challenge(incomplete, Path("test.yaml")) is False

    def test_empty_id(self):
        """A challenge with an empty id fails validation."""
        bad = {**VALID_CHALLENGE, "id": ""}
        assert _validate_challenge(bad, Path("test.yaml")) is False

    def test_non_string_id(self):
        """A challenge with a non-string id fails validation."""
        bad = {**VALID_CHALLENGE, "id": 123}
        assert _validate_challenge(bad, Path("test.yaml")) is False


class TestGetChallengeById:
    def test_returns_correct_challenge(self):
        """get_challenge_by_id returns the correct challenge after loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.yaml"
            with open(filepath, "w") as f:
                yaml.dump(VALID_CHALLENGE, f)
            load_challenges(Path(tmpdir))

        challenge = get_challenge_by_id("test-001")
        assert challenge is not None
        assert challenge["title"] == "Test Challenge"

    def test_returns_none_for_missing(self):
        """get_challenge_by_id returns None for a nonexistent id."""
        result = get_challenge_by_id("nonexistent-id-xyz")
        assert result is None
