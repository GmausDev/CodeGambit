"""Sandbox execution service for running user code safely.

Tries Docker first, falls back to subprocess with resource limits.
"""

import logging
import os
import resource
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int
    timed_out: bool
    memory_exceeded: bool


def _parse_memory_limit(limit_str: str) -> int:
    """Parse memory limit string (e.g. '256m') to bytes."""
    limit_str = limit_str.strip().lower()
    if limit_str.endswith("g"):
        return int(limit_str[:-1]) * 1024 * 1024 * 1024
    if limit_str.endswith("m"):
        return int(limit_str[:-1]) * 1024 * 1024
    if limit_str.endswith("k"):
        return int(limit_str[:-1]) * 1024
    return int(limit_str)


def _docker_available() -> bool:
    """Check if Docker is available and running."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def _run_docker(code: str, timeout: int, memory_limit: str) -> ExecutionResult:
    """Execute code in a Docker container."""
    import docker

    client = docker.from_env()
    start = time.monotonic()
    timed_out = False
    memory_exceeded = False

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name
    os.chmod(tmp_path, 0o600)

    try:
        container = client.containers.run(
            settings.SANDBOX_IMAGE,
            command=["python3", "/sandbox/solution.py"],
            volumes={tmp_path: {"bind": "/sandbox/solution.py", "mode": "ro"}},
            mem_limit=memory_limit,
            cpu_period=100000,
            cpu_quota=int(settings.SANDBOX_CPU_LIMIT * 100000),
            network_disabled=True,
            user="sandbox",
            working_dir="/sandbox",
            detach=True,
        )

        try:
            result = container.wait(timeout=timeout)
        except Exception:
            container.kill()
            timed_out = True
            result = {"StatusCode": -1}

        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        exit_code = result.get("StatusCode", -1)

        # OOM killed
        container.reload()
        inspect = container.attrs
        if inspect.get("State", {}).get("OOMKilled", False):
            memory_exceeded = True

        container.remove(force=True)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    elapsed_ms = int((time.monotonic() - start) * 1000)

    return ExecutionResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        execution_time_ms=elapsed_ms,
        timed_out=timed_out,
        memory_exceeded=memory_exceeded,
    )


def _make_preexec_fn(memory_bytes: int):
    """Create a preexec_fn that sets resource limits for the subprocess."""
    def preexec():
        # Limit virtual memory
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        # Disable core dumps
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        # Limit number of processes
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    return preexec


def _run_subprocess(code: str, timeout: int, memory_limit: str) -> ExecutionResult:
    """Execute code in a subprocess with resource limits (reduced isolation)."""
    memory_bytes = _parse_memory_limit(memory_limit)
    start = time.monotonic()
    timed_out = False
    memory_exceeded = False

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp_path = f.name
    os.chmod(tmp_path, 0o600)

    try:
        result = subprocess.run(
            ["python3", tmp_path],
            capture_output=True,
            timeout=timeout,
            preexec_fn=_make_preexec_fn(memory_bytes),
            env={},
        )
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        timed_out = True
        stdout = ""
        stderr = "Execution timed out"
        exit_code = -1
    except Exception as exc:
        stdout = ""
        stderr = str(exc)
        exit_code = -1
        if "MemoryError" in str(exc) or "Cannot allocate memory" in str(exc):
            memory_exceeded = True
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Check stderr for memory-related errors
    if "MemoryError" in stderr or "Cannot allocate memory" in stderr:
        memory_exceeded = True

    return ExecutionResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        execution_time_ms=elapsed_ms,
        timed_out=timed_out,
        memory_exceeded=memory_exceeded,
    )


def execute_code(
    code: str,
    timeout: int | None = None,
    memory_limit: str | None = None,
) -> ExecutionResult:
    """Execute code in a sandbox.

    Tries Docker first. Falls back to subprocess with resource limits
    if Docker is not available.
    """
    timeout = timeout or settings.SANDBOX_TIMEOUT
    memory_limit = memory_limit or settings.SANDBOX_MEMORY_LIMIT

    if _docker_available():
        logger.debug("Executing code in Docker sandbox")
        return _run_docker(code, timeout, memory_limit)

    logger.warning(
        "Docker not available, using subprocess sandbox — reduced isolation"
    )
    return _run_subprocess(code, timeout, memory_limit)
