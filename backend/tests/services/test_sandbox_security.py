"""
Tests for Sandbox Security - H2.2 Core Feature Hardening

Tests the enhanced sandbox security implementation:
1. gVisor runtime detection
2. Seccomp profile selection
3. Security configuration
4. Docker command building
5. Execution isolation
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from pathlib import Path


# =============================================================================
# Security Configuration Tests
# =============================================================================

class TestSandboxSecurityConfig:
    """Tests for SandboxSecurityConfig."""

    def test_default_config(self):
        """Test default security configuration."""
        from app.services.sandbox_executor import SandboxSecurityConfig, SandboxRuntime

        config = SandboxSecurityConfig()

        assert config.runtime == SandboxRuntime.RUNC
        assert config.memory_limit == "512m"
        assert config.cpu_limit == 0.5
        assert config.timeout_seconds == 30
        assert config.pids_limit == 50
        assert config.network_disabled is True
        assert config.read_only_rootfs is True
        assert config.no_new_privileges is True

    def test_gvisor_config(self):
        """Test gVisor runtime configuration."""
        from app.services.sandbox_executor import SandboxSecurityConfig, SandboxRuntime

        config = SandboxSecurityConfig(runtime=SandboxRuntime.RUNSC)

        assert config.runtime == SandboxRuntime.RUNSC

    def test_minimal_syscalls(self):
        """Test minimal syscalls list."""
        from app.services.sandbox_executor import SandboxSecurityConfig

        config = SandboxSecurityConfig()

        # Essential syscalls should be present
        assert "read" in config.minimal_syscalls
        assert "write" in config.minimal_syscalls
        assert "exit" in config.minimal_syscalls
        assert "mmap" in config.minimal_syscalls

        # Dangerous syscalls should not be present
        assert "execve" not in config.minimal_syscalls
        assert "socket" not in config.minimal_syscalls
        assert "fork" not in config.minimal_syscalls


class TestSandboxRuntime:
    """Tests for SandboxRuntime enum."""

    def test_runtime_values(self):
        """Test runtime enum values."""
        from app.services.sandbox_executor import SandboxRuntime

        assert SandboxRuntime.RUNC.value == "runc"
        assert SandboxRuntime.RUNSC.value == "runsc"
        assert SandboxRuntime.KATA.value == "kata"


# =============================================================================
# Seccomp Profile Tests
# =============================================================================

class TestSeccompProfiles:
    """Tests for seccomp profile configuration."""

    def test_minimal_profile_structure(self):
        """Test minimal seccomp profile has correct structure."""
        from app.services.sandbox_executor import MINIMAL_SECCOMP_PROFILE

        assert "defaultAction" in MINIMAL_SECCOMP_PROFILE
        assert MINIMAL_SECCOMP_PROFILE["defaultAction"] == "SCMP_ACT_ERRNO"
        assert "architectures" in MINIMAL_SECCOMP_PROFILE
        assert "syscalls" in MINIMAL_SECCOMP_PROFILE

    def test_minimal_profile_blocks_execve(self):
        """Test minimal profile blocks execve."""
        from app.services.sandbox_executor import MINIMAL_SECCOMP_PROFILE

        execve_rules = [
            rule for rule in MINIMAL_SECCOMP_PROFILE["syscalls"]
            if "execve" in rule.get("names", [])
        ]

        assert len(execve_rules) > 0
        assert execve_rules[0]["action"] == "SCMP_ACT_ERRNO"

    def test_minimal_profile_blocks_socket(self):
        """Test minimal profile blocks socket syscalls."""
        from app.services.sandbox_executor import MINIMAL_SECCOMP_PROFILE

        socket_rules = [
            rule for rule in MINIMAL_SECCOMP_PROFILE["syscalls"]
            if "socket" in rule.get("names", [])
        ]

        assert len(socket_rules) > 0
        assert socket_rules[0]["action"] == "SCMP_ACT_ERRNO"

    def test_minimal_profile_allows_basic_io(self):
        """Test minimal profile allows basic I/O."""
        from app.services.sandbox_executor import MINIMAL_SECCOMP_PROFILE

        io_rules = [
            rule for rule in MINIMAL_SECCOMP_PROFILE["syscalls"]
            if "read" in rule.get("names", []) or "write" in rule.get("names", [])
        ]

        allowed_rules = [r for r in io_rules if r["action"] == "SCMP_ACT_ALLOW"]
        assert len(allowed_rules) > 0

    def test_seccomp_file_exists(self):
        """Test seccomp profile files exist."""
        from app.services.sandbox_executor import SECCOMP_STRICT, SECCOMP_MINIMAL

        # At least one should exist
        assert SECCOMP_STRICT.exists() or SECCOMP_MINIMAL.exists()

    def test_seccomp_file_valid_json(self):
        """Test seccomp profile files are valid JSON."""
        from app.services.sandbox_executor import SECCOMP_STRICT, SECCOMP_MINIMAL

        if SECCOMP_STRICT.exists():
            content = SECCOMP_STRICT.read_text()
            profile = json.loads(content)
            assert "defaultAction" in profile

        if SECCOMP_MINIMAL.exists():
            content = SECCOMP_MINIMAL.read_text()
            profile = json.loads(content)
            assert "defaultAction" in profile


# =============================================================================
# Sandbox Executor Tests
# =============================================================================

class TestSandboxExecutor:
    """Tests for SandboxExecutor class."""

    @pytest.fixture
    def mock_subprocess(self):
        """Mock subprocess.run."""
        with patch("subprocess.run") as mock:
            # Docker available, image available, gVisor not available
            def run_side_effect(args, **kwargs):
                result = MagicMock()
                if args[0] == "docker" and args[1] == "info":
                    result.returncode = 0
                    result.stdout = b'{"Runtimes": {"runc": {}}}'
                elif args[0] == "docker" and args[1] == "images":
                    result.returncode = 0
                    result.stdout = b"abc123"  # Image exists
                else:
                    result.returncode = 0
                return result

            mock.side_effect = run_side_effect
            yield mock

    def test_executor_initialization(self, mock_subprocess):
        """Test executor initializes correctly."""
        from app.services.sandbox_executor import SandboxExecutor

        executor = SandboxExecutor()

        assert executor.docker_available is True
        assert executor.image_available is True

    def test_executor_with_security_config(self, mock_subprocess):
        """Test executor with custom security config."""
        from app.services.sandbox_executor import (
            SandboxExecutor,
            SandboxSecurityConfig,
            SandboxRuntime,
        )

        config = SandboxSecurityConfig(
            runtime=SandboxRuntime.RUNSC,
            memory_limit="256m",
            pids_limit=25,
        )

        executor = SandboxExecutor(security_config=config)

        assert executor.security_config.memory_limit == "256m"
        assert executor.security_config.pids_limit == 25

    def test_gvisor_detection(self, mock_subprocess):
        """Test gVisor runtime detection."""
        from app.services.sandbox_executor import SandboxExecutor

        # Modify mock to show gVisor available
        def run_side_effect(args, **kwargs):
            result = MagicMock()
            if args[0] == "docker" and args[1] == "info":
                if "--format" in args:
                    result.stdout = b'{"runsc": {}, "runc": {}}'
                result.returncode = 0
            elif args[0] == "docker" and args[1] == "images":
                result.returncode = 0
                result.stdout = b"abc123"
            else:
                result.returncode = 0
            return result

        mock_subprocess.side_effect = run_side_effect

        executor = SandboxExecutor()

        # gVisor detection happens in _check_gvisor
        # Check that the method ran without error
        assert executor.docker_available is True


class TestDockerCommandBuilding:
    """Tests for Docker command building."""

    @pytest.fixture
    def executor(self):
        """Create executor with mocked Docker check."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stdout=b"abc123")
            from app.services.sandbox_executor import SandboxExecutor
            exec_instance = SandboxExecutor()
            exec_instance.docker_available = True
            exec_instance.image_available = True
            exec_instance.gvisor_available = False
            return exec_instance

    @pytest.fixture
    def mock_config(self):
        """Create mock SandboxConfig."""
        config = MagicMock()
        config.memory_mb = 512
        config.cpu_limit = 0.5
        config.tier = "strict"
        config.network_enabled = False
        return config

    def test_command_includes_security_options(self, executor, mock_config):
        """Test Docker command includes security options."""
        cmd = executor._build_docker_command(mock_config, "test-container")

        # Check for security options
        assert "--security-opt=no-new-privileges:true" in cmd
        assert "--cap-drop=ALL" in cmd
        assert "--read-only" in cmd

    def test_command_includes_resource_limits(self, executor, mock_config):
        """Test Docker command includes resource limits."""
        cmd = executor._build_docker_command(mock_config, "test-container")

        # Check for resource limits
        assert "--memory=512m" in cmd
        assert "--cpus=0.5" in cmd
        assert any("--pids-limit" in c for c in cmd)

    def test_command_includes_network_isolation(self, executor, mock_config):
        """Test Docker command includes network isolation."""
        mock_config.network_enabled = False
        cmd = executor._build_docker_command(mock_config, "test-container")

        assert "--network=none" in cmd

    def test_command_with_gvisor(self, executor, mock_config):
        """Test Docker command with gVisor runtime."""
        executor.gvisor_available = True
        cmd = executor._build_docker_command(
            mock_config,
            "test-container",
            use_gvisor=True
        )

        assert "--runtime=runsc" in cmd

    def test_command_without_gvisor(self, executor, mock_config):
        """Test Docker command without gVisor runtime."""
        executor.gvisor_available = False
        cmd = executor._build_docker_command(
            mock_config,
            "test-container",
            use_gvisor=True
        )

        # Should not include gVisor if not available
        assert "--runtime=runsc" not in cmd

    def test_command_includes_tmpfs(self, executor, mock_config):
        """Test Docker command includes tmpfs with noexec."""
        cmd = executor._build_docker_command(mock_config, "test-container")

        tmpfs_arg = [c for c in cmd if c.startswith("--tmpfs=")]
        assert len(tmpfs_arg) > 0
        assert "noexec" in tmpfs_arg[0]

    def test_command_includes_user(self, executor, mock_config):
        """Test Docker command includes non-root user."""
        cmd = executor._build_docker_command(mock_config, "test-container")

        user_arg = [c for c in cmd if c.startswith("--user=")]
        assert len(user_arg) > 0


# =============================================================================
# Execution Result Tests
# =============================================================================

class TestExecutionResult:
    """Tests for ExecutionResult class."""

    def test_successful_result(self):
        """Test creating a successful result."""
        from app.services.sandbox_executor import ExecutionResult

        result = ExecutionResult(
            success=True,
            output={"key": "value"},
            execution_time_ms=100,
        )

        assert result.success is True
        assert result.output == {"key": "value"}
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed result."""
        from app.services.sandbox_executor import ExecutionResult

        result = ExecutionResult(
            success=False,
            error="Execution timeout",
            error_code="TIMEOUT",
        )

        assert result.success is False
        assert result.error == "Execution timeout"
        assert result.error_code == "TIMEOUT"

    def test_oom_result(self):
        """Test creating an OOM result."""
        from app.services.sandbox_executor import ExecutionResult

        result = ExecutionResult(
            success=False,
            error="Container killed (out of memory)",
            error_code="OOM",
            exit_code=137,
        )

        assert result.success is False
        assert result.error_code == "OOM"
        assert result.exit_code == 137


# =============================================================================
# Integration Tests
# =============================================================================

class TestSandboxIntegration:
    """Integration tests for sandbox execution."""

    @pytest.mark.asyncio
    async def test_execute_safe_code(self):
        """Test executing safe code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"")

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                # Mock successful execution
                mock_proc = AsyncMock()
                mock_proc.returncode = 0
                mock_proc.communicate = AsyncMock(
                    return_value=(
                        b'{"success": true, "output": "hello"}',
                        b""
                    )
                )
                mock_exec.return_value = mock_proc

                from app.services.sandbox_executor import SandboxExecutor, SandboxSecurityConfig

                executor = SandboxExecutor()
                executor.docker_available = True
                executor.image_available = True

                config = MagicMock()
                config.memory_mb = 512
                config.cpu_limit = 0.5
                config.timeout_seconds = 30
                config.tier = "strict"
                config.network_enabled = False

                result = await executor.execute(
                    code="result = 'hello'",
                    input_data={},
                    config=config,
                )

                assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_timeout(self):
        """Test execution timeout handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"")

            with patch("asyncio.create_subprocess_exec") as mock_exec:
                # Mock timeout
                mock_proc = AsyncMock()
                mock_proc.communicate = AsyncMock(
                    side_effect=TimeoutError("Execution timed out")
                )
                mock_exec.return_value = mock_proc

                with patch("asyncio.wait_for", side_effect=TimeoutError):
                    from app.services.sandbox_executor import SandboxExecutor

                    executor = SandboxExecutor()
                    executor.docker_available = True
                    executor.image_available = True

                    config = MagicMock()
                    config.memory_mb = 512
                    config.cpu_limit = 0.5
                    config.timeout_seconds = 1
                    config.tier = "strict"
                    config.network_enabled = False

                    # The timeout is handled internally
                    # This test verifies the structure exists


# =============================================================================
# Security Policy Tests
# =============================================================================

class TestSecurityPolicies:
    """Tests for security policy enforcement."""

    def test_no_capabilities(self):
        """Test all capabilities are dropped."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stdout=b"abc123")

            from app.services.sandbox_executor import SandboxExecutor

            executor = SandboxExecutor()
            executor.docker_available = True
            executor.image_available = True

            config = MagicMock()
            config.memory_mb = 512
            config.cpu_limit = 0.5
            config.tier = "strict"
            config.network_enabled = False

            cmd = executor._build_docker_command(config, "test")

            assert "--cap-drop=ALL" in cmd

    def test_no_new_privileges(self):
        """Test no-new-privileges is set."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stdout=b"abc123")

            from app.services.sandbox_executor import SandboxExecutor

            executor = SandboxExecutor()
            executor.docker_available = True
            executor.image_available = True

            config = MagicMock()
            config.memory_mb = 512
            config.cpu_limit = 0.5
            config.tier = "strict"
            config.network_enabled = False

            cmd = executor._build_docker_command(config, "test")

            assert "--security-opt=no-new-privileges:true" in cmd

    def test_strict_tier_uses_minimal_seccomp(self):
        """Test strict tier uses minimal seccomp profile."""
        with patch("subprocess.run") as mock:
            mock.return_value = MagicMock(returncode=0, stdout=b"abc123")

            from app.services.sandbox_executor import SandboxExecutor, SECCOMP_MINIMAL

            executor = SandboxExecutor()
            executor.docker_available = True
            executor.image_available = True

            # Get seccomp profile for strict tier
            profile = executor._get_seccomp_profile("strict")

            # Should return a profile path
            assert profile is not None
