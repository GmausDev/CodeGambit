"""Tests for the evaluator service."""

import pytest

from app.config import Settings
from app.services.evaluator import (
    ClaudeEvaluator,
    EvaluationResult,
    _mock_evaluation,
    _parse_json_response,
    _result_from_parsed,
)


class TestParseJsonResponse:
    def test_plain_json(self):
        result = _parse_json_response('{"overall_score": 80}')
        assert result == {"overall_score": 80}

    def test_markdown_wrapped_json(self):
        raw = '```json\n{"overall_score": 80}\n```'
        result = _parse_json_response(raw)
        assert result == {"overall_score": 80}

    def test_markdown_no_language_tag(self):
        raw = '```\n{"overall_score": 80}\n```'
        result = _parse_json_response(raw)
        assert result == {"overall_score": 80}

    def test_invalid_json_returns_empty(self):
        result = _parse_json_response("invalid")
        assert result == {}

    def test_empty_string_returns_empty(self):
        result = _parse_json_response("")
        assert result == {}

    def test_nested_json(self):
        raw = '{"scores": {"a": 1, "b": 2}, "overall_score": 75}'
        result = _parse_json_response(raw)
        assert result["overall_score"] == 75
        assert result["scores"]["a"] == 1


class TestMockEvaluation:
    def test_socratic_mode(self):
        result = _mock_evaluation("socratic")
        assert isinstance(result, EvaluationResult)
        assert 0 <= result.overall_score <= 100
        assert 0 <= result.architecture_score <= 100
        assert 0 <= result.framework_depth_score <= 100
        assert 0 <= result.complexity_mgmt_score <= 100
        assert "socratic" in result.feedback_summary
        assert result.model_used == "mock"

    def test_adversarial_mode(self):
        result = _mock_evaluation("adversarial")
        assert isinstance(result, EvaluationResult)
        assert 0 <= result.overall_score <= 100
        assert 0 <= result.architecture_score <= 100
        assert 0 <= result.framework_depth_score <= 100
        assert 0 <= result.complexity_mgmt_score <= 100
        assert "adversarial" in result.feedback_summary

    def test_collaborative_mode(self):
        result = _mock_evaluation("collaborative")
        assert isinstance(result, EvaluationResult)
        assert "collaborative" in result.feedback_summary

    def test_strengths_and_improvements_populated(self):
        result = _mock_evaluation("socratic")
        assert isinstance(result.strengths, list)
        assert len(result.strengths) > 0
        assert isinstance(result.improvements, list)
        assert len(result.improvements) > 0


class TestResultFromParsed:
    def test_full_parsed_data(self):
        parsed = {
            "overall_score": 85,
            "architecture_score": 90,
            "framework_depth_score": 80,
            "complexity_mgmt_score": 75,
            "feedback_summary": "Great work!",
            "strengths": ["Clean code"],
            "improvements": ["More tests"],
        }
        result = _result_from_parsed(parsed, '{"raw": true}', "socratic")
        assert result.overall_score == 85
        assert result.architecture_score == 90
        assert result.framework_depth_score == 80
        assert result.complexity_mgmt_score == 75
        assert result.feedback_summary == "Great work!"
        assert result.strengths == ["Clean code"]
        assert result.improvements == ["More tests"]

    def test_missing_fields_use_defaults(self):
        parsed = {}
        result = _result_from_parsed(parsed, "{}", "adversarial")
        assert result.overall_score == 60
        assert result.architecture_score == 60
        assert result.framework_depth_score == 60
        assert result.complexity_mgmt_score == 60
        assert "adversarial" in result.feedback_summary

    def test_mode_feedback_override(self):
        parsed = {"mode_specific_feedback": "from parsed"}
        result = _result_from_parsed(parsed, "{}", "socratic", "from argument")
        assert result.mode_specific_feedback == "from argument"

    def test_mode_feedback_from_parsed_when_no_override(self):
        parsed = {"mode_specific_feedback": "from parsed"}
        result = _result_from_parsed(parsed, "{}", "socratic")
        assert result.mode_specific_feedback == "from parsed"


class TestClaudeEvaluator:
    def test_empty_api_key_uses_mock(self):
        s = Settings(ANTHROPIC_API_KEY="")
        evaluator = ClaudeEvaluator(settings=s)
        assert evaluator.client is None

    def test_invalid_api_key_still_creates_client(self):
        s = Settings(ANTHROPIC_API_KEY="sk-test-fake-key")
        evaluator = ClaudeEvaluator(settings=s)
        # Client is created (validation happens at call time, not init)
        assert evaluator.client is not None
