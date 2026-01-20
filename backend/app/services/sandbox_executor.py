"""Sandbox Executor Service (v3 - H2.2 Core Feature Hardening).

Production-grade isolated tool execution with:
- Custom Docker image (vivid-sandbox)
- Seccomp profiles for syscall filtering (minimal allowlist)
- gVisor (runsc) runtime support for defense-in-depth
- Resource limits (CPU, memory, timeout)
- Network/filesystem restrictions
- Execution tracking and logging
- Container pool management

H2.2 Security Enhancements:
- gVisor runtime support for user-space kernel isolation
- Stricter seccomp profile with minimal syscalls
- PIDs limit to prevent fork bombs
- Read-only root filesystem with tmpfs for /tmp
- Dropped ALL capabilities
- No-new-privileges security flag
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_sandbox import (
    SandboxConfig,
    SandboxExecution,
    ExecutionStatus,
    SandboxTier,
    DEFAULT_SANDBOX_CONFIGS,
)
from app.models_telemetry import ToolManifest, ToolTier
from app.models_versioning import ToolVersion

logger = logging.getLogger(__name__)

# Paths
SANDBOX_DIR = Path(__file__).parent.parent.parent / "sandbox"
SECCOMP_STRICT = SANDBOX_DIR / "seccomp-strict.json"
SECCOMP_MINIMAL = SANDBOX_DIR / "seccomp-minimal.json"


# =============================================================================
# H2.2: Runtime Configuration
# =============================================================================

class SandboxRuntime(str, Enum):
    """Container runtime options for sandbox execution."""
    RUNC = "runc"       # Default Docker runtime (seccomp only)
    RUNSC = "runsc"     # gVisor - user-space kernel (recommended)
    KATA = "kata"       # Kata Containers - lightweight VMs (optional)


@dataclass
class SandboxSecurityConfig:
    """
    H2.2: Enhanced sandbox security configuration.

    Defense-in-depth approach with multiple security layers:
    1. Container isolation (Docker/gVisor)
    2. Seccomp syscall filtering
    3. Capability dropping
    4. Resource limits
    5. Network isolation
    6. Filesystem restrictions
    """
    # Runtime selection
    runtime: SandboxRuntime = SandboxRuntime.RUNC

    # Resource limits
    memory_limit: str = "512m"
    cpu_limit: float = 0.5
    timeout_seconds: int = 30
    pids_limit: int = 50  # Prevent fork bombs

    # Isolation flags
    network_disabled: bool = True
    read_only_rootfs: bool = True
    no_new_privileges: bool = True

    # Seccomp configuration
    seccomp_profile: str = "strict"  # strict, minimal, standard

    # Allowed syscalls for minimal profile (H2.2)
    # Only essential syscalls for Python execution
    minimal_syscalls: List[str] = field(default_factory=lambda: [
        # Memory management
        "read", "write", "close", "fstat", "lseek",
        "mmap", "mprotect", "munmap", "brk",
        # Process lifecycle
        "exit", "exit_group",
        # Thread support (needed for Python)
        "futex", "set_robust_list", "set_tid_address",
        # Clock (needed for time operations)
        "clock_gettime", "clock_getres",
        # File operations (read-only)
        "openat", "newfstatat", "getdents64", "getcwd",
        "readlinkat", "faccessat2", "statx",
        # Signals
        "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
        "sigaltstack",
        # Misc required by Python
        "arch_prctl", "getrandom", "pread64",
        "fcntl", "dup", "dup2", "pipe2",
        "prctl", "prlimit64",
        # Memory info
        "madvise", "mremap",
        # UID/GID
        "getuid", "getgid", "geteuid", "getegid",
        "getpid", "getppid",
        # Poll/epoll for I/O
        "poll", "epoll_create1", "epoll_ctl", "epoll_wait",
    ])


# H2.2: Strict seccomp profile (minimal syscalls)
MINIMAL_SECCOMP_PROFILE = {
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"],
    "syscalls": [
        {
            "names": [
                # Memory management
                "read", "write", "close", "fstat", "lseek",
                "mmap", "mprotect", "munmap", "brk",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # Process lifecycle
                "exit", "exit_group",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # Threading support
                "futex", "set_robust_list", "set_tid_address",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # Clock
                "clock_gettime", "clock_getres",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # File operations (read-only)
                "openat", "newfstatat", "getdents64", "getcwd",
                "readlinkat", "faccessat2", "statx",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # Signals
                "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
                "sigaltstack",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # Misc Python requirements
                "arch_prctl", "getrandom", "pread64",
                "fcntl", "dup", "dup2", "pipe2",
                "prctl", "prlimit64",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # Memory info
                "madvise", "mremap",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # UID/GID
                "getuid", "getgid", "geteuid", "getegid",
                "getpid", "getppid",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        {
            "names": [
                # Poll/epoll
                "poll", "epoll_create1", "epoll_ctl", "epoll_wait",
            ],
            "action": "SCMP_ACT_ALLOW",
        },
        # Explicitly blocked dangerous syscalls
        {
            "names": ["execve", "execveat"],
            "action": "SCMP_ACT_ERRNO",
            "errnoRet": 1,
        },
        {
            "names": ["socket", "connect", "bind", "listen", "accept"],
            "action": "SCMP_ACT_ERRNO",
            "errnoRet": 1,
        },
        {
            "names": ["clone", "clone3", "fork", "vfork"],
            "action": "SCMP_ACT_ERRNO",
            "errnoRet": 1,
        },
        {
            "names": ["ptrace", "mount", "umount2", "chroot", "pivot_root"],
            "action": "SCMP_ACT_ERRNO",
            "errnoRet": 1,
        },
    ],
}


# =============================================================================
# Execution Result
# =============================================================================

class ExecutionResult:
    """Result of sandbox execution."""
    
    def __init__(
        self,
        success: bool,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        execution_time_ms: int = 0,
        memory_used_mb: int = 0,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        container_id: Optional[str] = None,
    ):
        self.success = success
        self.output = output or {}
        self.error = error
        self.error_code = error_code
        self.execution_time_ms = execution_time_ms
        self.memory_used_mb = memory_used_mb
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.container_id = container_id


# =============================================================================
# Sandbox Executor
# =============================================================================

class SandboxExecutor:
    """
    Executes tools in isolated sandbox environment (H2.2 Enhanced).

    Security layers:
    1. Container isolation (Docker or gVisor)
    2. Seccomp syscall filtering
    3. Capability dropping (ALL)
    4. Resource limits (memory, CPU, PIDs)
    5. Network isolation
    6. Read-only filesystem
    """

    # Docker images
    SANDBOX_IMAGE = "vivid-sandbox:latest"
    FALLBACK_IMAGE = "python:3.11-slim"

    def __init__(self, security_config: Optional[SandboxSecurityConfig] = None):
        self.docker_available = False
        self.image_available = False
        self.gvisor_available = False
        self.security_config = security_config or SandboxSecurityConfig()
        self._check_docker()
        self._check_gvisor()

    def _check_docker(self):
        """Check if Docker and our sandbox image are available."""
        try:
            # Check Docker daemon
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=10,
            )
            self.docker_available = result.returncode == 0

            if self.docker_available:
                # Check if our image exists
                result = subprocess.run(
                    ["docker", "images", "-q", self.SANDBOX_IMAGE],
                    capture_output=True,
                    timeout=5,
                )
                self.image_available = bool(result.stdout.strip())

                if not self.image_available:
                    logger.warning(
                        f"Sandbox image {self.SANDBOX_IMAGE} not found. "
                        f"Build with: cd backend/sandbox && docker build -t {self.SANDBOX_IMAGE} ."
                    )
        except Exception as e:
            logger.warning(f"Docker check failed: {e}")
            self.docker_available = False

    def _check_gvisor(self):
        """
        H2.2: Check if gVisor (runsc) runtime is available.

        gVisor provides user-space kernel isolation for defense-in-depth.
        """
        if not self.docker_available:
            return

        try:
            # Check if gVisor runtime is configured
            result = subprocess.run(
                ["docker", "info", "--format", "{{json .Runtimes}}"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                output = result.stdout.decode()
                # Check if runsc is in the runtimes
                self.gvisor_available = "runsc" in output.lower()
                if self.gvisor_available:
                    logger.info("gVisor (runsc) runtime available for sandbox")
                else:
                    logger.info(
                        "gVisor not available. Install runsc and configure Docker daemon "
                        "for enhanced security. See: https://gvisor.dev/docs/user_guide/install/"
                    )
        except Exception as e:
            logger.debug(f"gVisor check failed: {e}")
            self.gvisor_available = False
    
    async def execute(
        self,
        code: str,
        input_data: Dict[str, Any],
        config: SandboxConfig,
    ) -> ExecutionResult:
        """
        Execute code in sandbox.
        
        Args:
            code: Python code to execute
            input_data: Input parameters
            config: Sandbox configuration
            
        Returns:
            ExecutionResult with output or error
        """
        if self.docker_available:
            return await self._execute_docker(code, input_data, config)
        else:
            logger.warning("Docker unavailable, using subprocess fallback (less secure)")
            return await self._execute_subprocess(code, input_data, config)
    
    async def _execute_docker(
        self,
        code: str,
        input_data: Dict[str, Any],
        config: SandboxConfig,
        use_gvisor: bool = False,
    ) -> ExecutionResult:
        """
        Execute in Docker container with full security (H2.2 Enhanced).

        Security measures:
        1. gVisor runtime (optional, for defense-in-depth)
        2. Strict seccomp profile
        3. All capabilities dropped
        4. Read-only filesystem
        5. Network isolation
        6. Resource limits
        """
        start_time = time.time()
        container_name = f"sandbox-{uuid4().hex[:8]}"

        # H2.2: Use gVisor for strict tier by default if available
        if use_gvisor is False and config.tier == SandboxTier.STRICT.value:
            use_gvisor = self.gvisor_available

        # Prepare payload for runner.py
        payload = {
            "code": code,
            "input_data": input_data,
        }
        payload_json = json.dumps(payload)

        # Build Docker command with security options
        cmd = self._build_docker_command(config, container_name, use_gvisor=use_gvisor)
        
        try:
            # Create subprocess and pipe input
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Send payload to stdin with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=payload_json.encode()),
                    timeout=config.timeout_seconds + 5,
                )
            except asyncio.TimeoutError:
                # Kill the container
                await self._kill_container(container_name)
                return ExecutionResult(
                    success=False,
                    error=f"Execution timed out after {config.timeout_seconds}s",
                    error_code="TIMEOUT",
                    execution_time_ms=config.timeout_seconds * 1000,
                    exit_code=-1,
                    container_id=container_name,
                )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Parse output
            stdout_str = stdout.decode('utf-8', errors='replace')[:100000]
            stderr_str = stderr.decode('utf-8', errors='replace')[:50000]
            
            if proc.returncode == 0:
                try:
                    result = json.loads(stdout_str)
                    return ExecutionResult(
                        success=result.get('success', True),
                        output=result.get('output'),
                        error=result.get('error'),
                        error_code=result.get('error_code'),
                        execution_time_ms=execution_time_ms,
                        stdout=result.get('stdout', '')[:10000],
                        stderr=result.get('stderr', stderr_str)[:10000],
                        exit_code=0,
                        container_id=container_name,
                    )
                except json.JSONDecodeError:
                    return ExecutionResult(
                        success=True,
                        output={"raw_output": stdout_str[:10000]},
                        execution_time_ms=execution_time_ms,
                        stdout=stdout_str[:10000],
                        stderr=stderr_str[:10000],
                        exit_code=0,
                        container_id=container_name,
                    )
            else:
                # Check for OOM
                if "killed" in stderr_str.lower() or proc.returncode == 137:
                    return ExecutionResult(
                        success=False,
                        error="Container killed (likely out of memory)",
                        error_code="OOM",
                        execution_time_ms=execution_time_ms,
                        stdout=stdout_str[:10000],
                        stderr=stderr_str[:10000],
                        exit_code=proc.returncode or 137,
                        container_id=container_name,
                    )
                
                return ExecutionResult(
                    success=False,
                    error=stderr_str[:5000] or "Execution failed",
                    error_code="EXECUTION_ERROR",
                    execution_time_ms=execution_time_ms,
                    stdout=stdout_str[:10000],
                    stderr=stderr_str[:10000],
                    exit_code=proc.returncode or 1,
                    container_id=container_name,
                )
                
        except Exception as e:
            logger.exception(f"Docker execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                error_code="DOCKER_ERROR",
                exit_code=-1,
                container_id=container_name,
            )
    
    def _build_docker_command(
        self,
        config: SandboxConfig,
        container_name: str,
        use_gvisor: bool = False,
    ) -> List[str]:
        """
        Build Docker run command with security options (H2.2 Enhanced).

        Security layers applied:
        1. gVisor runtime (if available and requested)
        2. Seccomp profile (strict/minimal/standard)
        3. Capability dropping (ALL)
        4. Resource limits (memory, CPU, PIDs)
        5. Network isolation
        6. Read-only filesystem with tmpfs for /tmp
        7. No-new-privileges flag
        """
        image = self.SANDBOX_IMAGE if self.image_available else self.FALLBACK_IMAGE
        sec_config = self.security_config

        cmd = [
            "docker", "run",
            "--rm",                                         # Auto-remove container
            f"--name={container_name}",                     # Named for management
            "-i",                                           # Interactive (for stdin)
            f"--memory={config.memory_mb}m",                # Memory limit
            f"--memory-swap={config.memory_mb}m",           # No swap allowed
            f"--cpus={config.cpu_limit}",                   # CPU limit
            f"--pids-limit={sec_config.pids_limit}",        # H2.2: PIDs limit
            "--security-opt=no-new-privileges:true",        # H2.2: No privilege escalation
            "--cap-drop=ALL",                               # H2.2: Drop ALL capabilities
            "--read-only",                                  # H2.2: Read-only root filesystem
            "--tmpfs=/tmp:size=10M,mode=1777,noexec",       # H2.2: noexec on tmpfs
        ]

        # H2.2: gVisor runtime for defense-in-depth
        if use_gvisor and self.gvisor_available:
            cmd.append("--runtime=runsc")
            logger.debug(f"Using gVisor runtime for container {container_name}")
        else:
            # Use default runc but with enhanced seccomp
            pass

        # H2.2: Enhanced seccomp profile selection
        seccomp_profile_path = self._get_seccomp_profile(config.tier)
        if seccomp_profile_path:
            cmd.append(f"--security-opt=seccomp={seccomp_profile_path}")

        # Network isolation
        if not config.network_enabled:
            cmd.append("--network=none")
        else:
            # For network-enabled, use bridge but consider egress filtering
            cmd.append("--network=bridge")
            # Add DNS isolation for untrusted code
            cmd.extend(["--dns", "8.8.8.8", "--dns", "8.8.4.4"])

        # User (non-root) - critical for security
        if self.image_available:
            cmd.append("--user=sandbox")
        else:
            # Use nobody for fallback image
            cmd.append("--user=65534:65534")

        # H2.2: Additional hardening
        cmd.extend([
            "--ulimit=nofile=64:64",      # Limit open files
            "--ulimit=nproc=50:50",       # Limit processes
        ])

        # Add the image
        cmd.append(image)

        # If using fallback image, run runner.py from stdin
        if not self.image_available:
            runner_code = self._get_embedded_runner()
            cmd.extend(["python3", "-c", runner_code])

        return cmd

    def _get_seccomp_profile(self, tier: str) -> Optional[str]:
        """
        H2.2: Get the appropriate seccomp profile for the tier.

        Profiles:
        - strict: Minimal syscalls (most secure)
        - standard: Basic syscalls for verified tools
        - trusted: Extended syscalls for certified tools
        """
        if tier == SandboxTier.STRICT.value:
            # Use minimal seccomp profile
            if SECCOMP_MINIMAL.exists():
                return str(SECCOMP_MINIMAL)
            elif SECCOMP_STRICT.exists():
                return str(SECCOMP_STRICT)
            else:
                # Create inline profile
                return self._create_inline_seccomp_profile()
        elif tier == SandboxTier.STANDARD.value:
            if SECCOMP_STRICT.exists():
                return str(SECCOMP_STRICT)
        # trusted tier uses default Docker seccomp
        return None

    def _create_inline_seccomp_profile(self) -> str:
        """Create a temporary file with minimal seccomp profile."""
        import tempfile
        profile_path = Path(tempfile.gettempdir()) / "vivid-seccomp-minimal.json"
        if not profile_path.exists():
            profile_path.write_text(json.dumps(MINIMAL_SECCOMP_PROFILE))
        return str(profile_path)
    
    def _get_embedded_runner(self) -> str:
        """Get embedded runner code for fallback mode."""
        return '''
import sys
import json
import traceback

# Read from stdin
payload = json.loads(sys.stdin.read())
code = payload.get("code", "")
input_data = payload.get("input_data", {})

# Restricted builtins
safe_builtins = {
    k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
    for k in ["bool", "int", "float", "str", "list", "dict", "tuple", "set",
              "len", "range", "enumerate", "zip", "map", "filter", "sorted",
              "min", "max", "sum", "any", "all", "abs", "round",
              "True", "False", "None", "print", "Exception", "ValueError", "TypeError"]
    if hasattr(__builtins__, k) if not isinstance(__builtins__, dict) else k in __builtins__
}
safe_globals = {"__builtins__": safe_builtins, "input_data": input_data}

try:
    exec(code, safe_globals)
    result = safe_globals.get("result") or safe_globals.get("output")
    if "process" in safe_globals and callable(safe_globals["process"]):
        result = safe_globals["process"](input_data)
    print(json.dumps({"success": True, "output": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e), "error_code": type(e).__name__}))
'''
    
    async def _kill_container(self, container_name: str):
        """Kill a running container."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "kill", container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=5)
        except Exception as e:
            logger.warning(f"Failed to kill container {container_name}: {e}")
    
    async def _execute_subprocess(
        self,
        code: str,
        input_data: Dict[str, Any],
        config: SandboxConfig,
    ) -> ExecutionResult:
        """Fallback: Execute in subprocess with limited isolation.
        
        WARNING: This is less secure than Docker execution.
        Only use for development or when Docker is unavailable.
        """
        start_time = time.time()
        
        # Use the embedded runner
        runner_code = self._get_embedded_runner()
        payload = json.dumps({"code": code, "input_data": input_data})
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "python3", "-c", runner_code,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=payload.encode()),
                    timeout=config.timeout_seconds,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return ExecutionResult(
                    success=False,
                    error=f"Execution timed out after {config.timeout_seconds}s",
                    error_code="TIMEOUT",
                    execution_time_ms=config.timeout_seconds * 1000,
                    exit_code=-1,
                )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            if proc.returncode == 0:
                try:
                    result = json.loads(stdout_str)
                    return ExecutionResult(
                        success=result.get('success', True),
                        output=result.get('output'),
                        error=result.get('error'),
                        error_code=result.get('error_code'),
                        execution_time_ms=execution_time_ms,
                        stdout=stdout_str[:10000],
                        stderr=stderr_str[:10000],
                        exit_code=0,
                    )
                except json.JSONDecodeError:
                    return ExecutionResult(
                        success=True,
                        output={"raw_output": stdout_str[:10000]},
                        execution_time_ms=execution_time_ms,
                        stdout=stdout_str[:10000],
                        stderr=stderr_str[:10000],
                        exit_code=0,
                    )
            else:
                return ExecutionResult(
                    success=False,
                    error=stderr_str[:5000] or "Execution failed",
                    error_code="EXECUTION_ERROR",
                    execution_time_ms=execution_time_ms,
                    stdout=stdout_str[:10000],
                    stderr=stderr_str[:10000],
                    exit_code=proc.returncode or 1,
                )
                
        except Exception as e:
            logger.exception(f"Subprocess execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                error_code="SUBPROCESS_ERROR",
                exit_code=-1,
            )


# =============================================================================
# Container Manager (for future use)
# =============================================================================

class ContainerPool:
    """Manages pre-warmed containers for faster execution."""
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.available: List[str] = []
        self.in_use: List[str] = []
    
    async def get_container(self) -> Optional[str]:
        """Get an available container from pool."""
        if self.available:
            container_id = self.available.pop()
            self.in_use.append(container_id)
            return container_id
        return None
    
    async def release_container(self, container_id: str):
        """Return container to pool."""
        if container_id in self.in_use:
            self.in_use.remove(container_id)
            self.available.append(container_id)
    
    async def warm_pool(self):
        """Pre-create containers for the pool."""
        # TODO: Implement container pre-warming
        pass


# =============================================================================
# Service Functions
# =============================================================================

# Global executor instance
_executor: Optional[SandboxExecutor] = None


def get_executor() -> SandboxExecutor:
    """Get or create sandbox executor."""
    global _executor
    if _executor is None:
        _executor = SandboxExecutor()
    return _executor


async def get_or_create_default_config(
    db: AsyncSession,
    tier: str = "strict",
) -> SandboxConfig:
    """Get or create a sandbox config by tier."""
    result = await db.execute(
        select(SandboxConfig).where(SandboxConfig.name == tier)
    )
    config = result.scalars().first()
    
    if not config:
        # Find default config
        defaults = {c["name"]: c for c in DEFAULT_SANDBOX_CONFIGS}
        cfg_data = defaults.get(tier, defaults["strict"])
        
        config = SandboxConfig(
            id=uuid4(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            **cfg_data,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    
    return config


async def determine_sandbox_tier(
    db: AsyncSession,
    tool: ToolManifest,
) -> str:
    """Determine appropriate sandbox tier based on tool tier."""
    tier_map = {
        ToolTier.EXPERIMENTAL.value: "strict",
        ToolTier.VERIFIED.value: "standard",
        ToolTier.CERTIFIED.value: "trusted",
    }
    return tier_map.get(tool.tier, "strict")


async def execute_tool_sandboxed(
    db: AsyncSession,
    tool_id: UUID,
    input_data: Dict[str, Any],
    user_id: str,
    session_id: Optional[str] = None,
) -> Tuple[SandboxExecution, ExecutionResult]:
    """
    Execute a tool in sandbox.
    
    Args:
        db: Database session
        tool_id: Tool to execute
        input_data: Execution inputs
        user_id: User triggering execution
        session_id: Optional session ID
        
    Returns:
        Tuple of (SandboxExecution record, ExecutionResult)
    """
    # Get tool
    tool = await db.get(ToolManifest, tool_id)
    if not tool:
        raise ValueError("Tool not found")
    
    # Get live version
    version_result = await db.execute(
        select(ToolVersion)
        .where(ToolVersion.tool_id == tool_id)
        .where(ToolVersion.is_live == True)
    )
    version = version_result.scalars().first()
    
    if not version or not version.code_content:
        raise ValueError("Tool has no executable code")
    
    # Determine sandbox tier and get config
    tier = await determine_sandbox_tier(db, tool)
    config = await get_or_create_default_config(db, tier)
    
    # Create execution record
    execution = SandboxExecution(
        id=uuid4(),
        tool_id=tool_id,
        version_id=version.id,
        config_id=config.id,
        user_id=user_id,
        session_id=session_id,
        input_data=input_data,
        status=ExecutionStatus.PENDING.value,
        queued_at=datetime.utcnow(),
        credits_charged=tool.credit_cost,
    )
    db.add(execution)
    await db.commit()
    
    # Execute
    execution.status = ExecutionStatus.RUNNING.value
    execution.started_at = datetime.utcnow()
    await db.commit()
    
    executor = get_executor()
    result = await executor.execute(version.code_content, input_data, config)
    
    # Update execution record
    execution.finished_at = datetime.utcnow()
    execution.execution_time_ms = result.execution_time_ms
    execution.memory_used_mb = result.memory_used_mb
    execution.container_id = result.container_id
    execution.stdout = result.stdout
    execution.stderr = result.stderr
    execution.exit_code = result.exit_code
    
    if result.success:
        execution.status = ExecutionStatus.SUCCESS.value
        execution.output_data = result.output
    else:
        if result.error_code == "TIMEOUT":
            execution.status = ExecutionStatus.TIMEOUT.value
        elif result.error_code == "OOM":
            execution.status = ExecutionStatus.OOM.value
        else:
            execution.status = ExecutionStatus.FAILED.value
        
        execution.error_message = result.error
        execution.error_code = result.error_code
        execution.credits_refunded = execution.credits_charged
    
    await db.commit()
    await db.refresh(execution)
    
    logger.info(
        f"Sandbox execution {execution.id}: "
        f"status={execution.status}, time={result.execution_time_ms}ms, "
        f"container={result.container_id}"
    )
    
    return execution, result


async def build_sandbox_image() -> bool:
    """Build the sandbox Docker image."""
    if not SANDBOX_DIR.exists():
        logger.error(f"Sandbox directory not found: {SANDBOX_DIR}")
        return False
    
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "build", "-t", "vivid-sandbox:latest", ".",
            cwd=str(SANDBOX_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.wait(), timeout=300)
        
        if proc.returncode == 0:
            logger.info("Sandbox image built successfully")
            return True
        else:
            logger.error(f"Failed to build sandbox image: {stderr.decode()}")
            return False
    except Exception as e:
        logger.exception(f"Error building sandbox image: {e}")
        return False
