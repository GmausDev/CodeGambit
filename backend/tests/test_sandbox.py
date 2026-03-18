"""Tests for the sandbox execution service."""

import pytest

from app.services.sandbox import ExecutionResult, _parse_memory_limit, execute_code


class TestParseMemoryLimit:
    def test_megabytes(self):
        assert _parse_memory_limit("256m") == 256 * 1024 * 1024

    def test_gigabytes(self):
        assert _parse_memory_limit("1g") == 1024 * 1024 * 1024

    def test_kilobytes(self):
        assert _parse_memory_limit("512k") == 512 * 1024

    def test_raw_bytes(self):
        assert _parse_memory_limit("1048576") == 1048576

    def test_uppercase_suffix(self):
        assert _parse_memory_limit("256M") == 256 * 1024 * 1024

    def test_whitespace_stripped(self):
        assert _parse_memory_limit("  256m  ") == 256 * 1024 * 1024


class TestExecuteCode:
    def test_hello_world(self):
        result = execute_code("print('hello')", timeout=10)
        assert isinstance(result, ExecutionResult)
        assert "hello" in result.stdout
        assert result.exit_code == 0
        assert result.timed_out is False

    def test_nonzero_exit(self):
        result = execute_code("import sys; sys.exit(1)", timeout=10)
        assert result.exit_code != 0
        assert result.timed_out is False

    def test_timeout(self):
        result = execute_code("while True: pass", timeout=2)
        assert result.timed_out is True

    def test_syntax_error(self):
        result = execute_code("syntax error!!!", timeout=10)
        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr

    def test_multiline_output(self):
        code = "for i in range(3): print(i)"
        result = execute_code(code, timeout=10)
        assert result.exit_code == 0
        assert "0" in result.stdout
        assert "2" in result.stdout

    def test_execution_time_populated(self):
        result = execute_code("print(1)", timeout=10)
        assert result.execution_time_ms >= 0
