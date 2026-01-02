"""Sandbox Executor Service.

Handles isolated tool execution with:
- Docker-based container isolation
- Resource limits (CPU, memory, timeout)
- Network/filesystem restrictions
- Execution tracking and logging
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
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


# =============================================================================
# Sandbox Executor
# =============================================================================

class SandboxExecutor:
    """Executes tools in isolated sandbox environment."""
    
    # Docker image for sandbox
    SANDBOX_IMAGE = "python:3.11-slim"
    
    def __init__(self, docker_available: bool = True):
        self.docker_available = docker_available
        self._check_docker()
    
    def _check_docker(self):
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=5,
            )
            self.docker_available = result.returncode == 0
        except Exception:
            self.docker_available = False
            logger.warning("Docker not available, sandbox will use subprocess fallback")
    
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
            return await self._execute_subprocess(code, input_data, config)
    
    async def _execute_docker(
        self,
        code: str,
        input_data: Dict[str, Any],
        config: SandboxConfig,
    ) -> ExecutionResult:
        """Execute in Docker container."""
        start_time = time.time()
        
        # Create temp directory for execution
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write code file
            code_file = os.path.join(tmpdir, "main.py")
            with open(code_file, "w") as f:
                f.write(self._wrap_code(code))
            
            # Write input file
            input_file = os.path.join(tmpdir, "input.json")
            with open(input_file, "w") as f:
                json.dump(input_data, f)
            
            # Build Docker command
            cmd = [
                "docker", "run",
                "--rm",  # Auto-remove container
                f"--memory={config.memory_mb}m",
                f"--cpus={config.cpu_limit}",
                f"--timeout={config.timeout_seconds}",
            ]
            
            # Network restrictions
            if not config.network_enabled:
                cmd.append("--network=none")
            
            # Filesystem mount
            if config.filesystem_readonly:
                cmd.append(f"--volume={tmpdir}:/app:ro")
            else:
                cmd.append(f"--volume={tmpdir}:/app")
            
            cmd.extend([
                "--workdir=/app",
                self.SANDBOX_IMAGE,
                "python", "main.py",
            ])
            
            try:
                # Run with asyncio timeout
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    ),
                    timeout=config.timeout_seconds + 5,
                )
                
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=config.timeout_seconds,
                )
                
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                if proc.returncode == 0:
                    # Parse output
                    try:
                        output = json.loads(stdout.decode())
                        return ExecutionResult(
                            success=True,
                            output=output,
                            execution_time_ms=execution_time_ms,
                            stdout=stdout.decode()[:10000],
                            stderr=stderr.decode()[:10000],
                            exit_code=0,
                        )
                    except json.JSONDecodeError:
                        return ExecutionResult(
                            success=True,
                            output={"raw_output": stdout.decode()[:10000]},
                            execution_time_ms=execution_time_ms,
                            stdout=stdout.decode()[:10000],
                            stderr=stderr.decode()[:10000],
                            exit_code=0,
                        )
                else:
                    return ExecutionResult(
                        success=False,
                        error=stderr.decode()[:5000] or "Execution failed",
                        error_code="EXECUTION_ERROR",
                        execution_time_ms=execution_time_ms,
                        stdout=stdout.decode()[:10000],
                        stderr=stderr.decode()[:10000],
                        exit_code=proc.returncode or 1,
                    )
                    
            except asyncio.TimeoutError:
                return ExecutionResult(
                    success=False,
                    error=f"Execution timed out after {config.timeout_seconds}s",
                    error_code="TIMEOUT",
                    execution_time_ms=config.timeout_seconds * 1000,
                    exit_code=-1,
                )
            except Exception as e:
                logger.exception(f"Docker execution failed: {e}")
                return ExecutionResult(
                    success=False,
                    error=str(e),
                    error_code="DOCKER_ERROR",
                    exit_code=-1,
                )
    
    async def _execute_subprocess(
        self,
        code: str,
        input_data: Dict[str, Any],
        config: SandboxConfig,
    ) -> ExecutionResult:
        """Fallback: Execute in subprocess with limited isolation."""
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write files
            code_file = os.path.join(tmpdir, "main.py")
            with open(code_file, "w") as f:
                f.write(self._wrap_code(code))
            
            input_file = os.path.join(tmpdir, "input.json")
            with open(input_file, "w") as f:
                json.dump(input_data, f)
            
            try:
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        "python3", code_file,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=tmpdir,
                    ),
                    timeout=config.timeout_seconds,
                )
                
                stdout, stderr = await proc.communicate()
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                if proc.returncode == 0:
                    try:
                        output = json.loads(stdout.decode())
                        return ExecutionResult(
                            success=True,
                            output=output,
                            execution_time_ms=execution_time_ms,
                            stdout=stdout.decode()[:10000],
                            stderr=stderr.decode()[:10000],
                            exit_code=0,
                        )
                    except json.JSONDecodeError:
                        return ExecutionResult(
                            success=True,
                            output={"raw_output": stdout.decode()[:10000]},
                            execution_time_ms=execution_time_ms,
                            stdout=stdout.decode()[:10000],
                            stderr=stderr.decode()[:10000],
                            exit_code=0,
                        )
                else:
                    return ExecutionResult(
                        success=False,
                        error=stderr.decode()[:5000] or "Execution failed",
                        error_code="EXECUTION_ERROR",
                        execution_time_ms=execution_time_ms,
                        stdout=stdout.decode()[:10000],
                        stderr=stderr.decode()[:10000],
                        exit_code=proc.returncode or 1,
                    )
                    
            except asyncio.TimeoutError:
                return ExecutionResult(
                    success=False,
                    error=f"Execution timed out after {config.timeout_seconds}s",
                    error_code="TIMEOUT",
                    execution_time_ms=config.timeout_seconds * 1000,
                    exit_code=-1,
                )
            except Exception as e:
                logger.exception(f"Subprocess execution failed: {e}")
                return ExecutionResult(
                    success=False,
                    error=str(e),
                    error_code="SUBPROCESS_ERROR",
                    exit_code=-1,
                )
    
    def _wrap_code(self, code: str) -> str:
        """Wrap user code with input/output handling."""
        return f'''
import json
import sys

# Load input
with open("input.json", "r") as f:
    input_data = json.load(f)

# User code
{code}

# If there's a main function, call it
if 'process' in dir():
    result = process(input_data)
    print(json.dumps(result))
elif 'main' in dir():
    result = main(input_data)
    print(json.dumps(result))
else:
    # Try to find any function that takes input
    print(json.dumps({{"message": "No process/main function found", "input": input_data}}))
'''


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
        f"status={execution.status}, time={result.execution_time_ms}ms"
    )
    
    return execution, result
