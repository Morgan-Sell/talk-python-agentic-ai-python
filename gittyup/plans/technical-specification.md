# Gitty Up - Technical Specification
**Version:** 1.0  
**Date:** November 2, 2025  
**Related:** project-plan.md

---

## Purpose

This document provides detailed technical specifications for implementing Gitty Up. It complements the project plan with implementation-level details, API designs, and technical decision rationale.

---

## Table of Contents

1. [Architecture Details](#architecture-details)
2. [Module Specifications](#module-specifications)
3. [Data Models](#data-models)
4. [API Contracts](#api-contracts)
5. [Error Taxonomy](#error-taxonomy)
6. [Performance Specifications](#performance-specifications)
7. [Security Specifications](#security-specifications)

---

## Architecture Details

### Design Principles

1. **Separation of Concerns**
   - Scanner: Only discovers repositories
   - Executor: Only runs git commands
   - Reporter: Only handles output
   - Each module has single responsibility

2. **Dependency Inversion**
   - Core modules don't depend on CLI
   - Core modules don't depend on specific libraries (abstract interfaces)
   - Easy to swap implementations

3. **Testability**
   - All external interactions (filesystem, subprocess) are abstracted
   - Easy to mock dependencies
   - Pure functions where possible

4. **Fail-Safe**
   - Never corrupt repositories
   - Operations are read-mostly (only git pull modifies)
   - Graceful degradation
   - Clear error states

### Component Interaction Flow

```
User Input → CLI Parser → Config Merger → Core Orchestrator
                                               ↓
                                    ┌──────────┴──────────┐
                                    ↓                     ↓
                            Scanner Module         Reporter Module
                                    ↓                     ↑
                            [Repository List]             │
                                    ↓                     │
                            Executor Module ──────────────┘
                                    ↓
                            [Results Collection]
                                    ↓
                            Reporter Module
                                    ↓
                            User Output
```

---

## Module Specifications

### 1. Scanner Module

**File:** `src/gittyup/core/scanner.py`

#### Purpose
Traverse directory tree and identify git repositories.

#### Key Classes

##### `RepositoryScanner`
```
Class: RepositoryScanner
Purpose: Main class for scanning directories

Attributes:
  - root_path: Path
    Starting directory for scan
  
  - max_depth: Optional[int]
    Maximum depth to traverse (None = unlimited)
  
  - exclude_patterns: List[str]
    Patterns to exclude from scanning
  
  - follow_symlinks: bool
    Whether to follow symbolic links
  
  - _visited_inodes: Set[int]
    Track visited inodes to prevent cycles

Methods:
  - scan() -> List[Repository]
    Main scanning method
    Returns: List of discovered Repository objects
    Raises: ScanError on fatal errors
  
  - _is_git_repository(path: Path) -> bool
    Check if directory is a git repository
    Returns: True if .git directory exists and is valid
  
  - _should_exclude(path: Path) -> bool
    Check if path matches exclusion patterns
    Returns: True if should be excluded
  
  - _has_permission(path: Path) -> bool
    Check if we have read permission
    Returns: True if readable
  
  - _detect_symlink_cycle(path: Path) -> bool
    Check for symlink cycles using inode tracking
    Returns: True if cycle detected
```

#### Key Functions

```
Function: is_valid_git_repo(path: Path) -> bool
Purpose: Validate that .git directory is legitimate
Checks:
  - .git directory exists
  - .git/HEAD exists
  - .git/config exists
Returns: True if valid git repository

Function: get_repo_info(path: Path) -> Dict[str, Any]
Purpose: Extract basic repository information
Returns: Dictionary with:
  - current_branch: str
  - has_remote: bool
  - remote_url: Optional[str]
  - has_uncommitted: bool
Raises: GitInfoError if can't read git info
```

#### Configuration

```
ScannerConfig:
  - max_depth: int | None = None
  - follow_symlinks: bool = True
  - exclude_patterns: List[str] = ["node_modules", "venv", "__pycache__"]
  - show_progress: bool = True
```

#### Error Handling

- **PermissionError**: Log and skip, continue scanning
- **SymlinkCycleError**: Log and skip, continue scanning
- **PathNotFoundError**: Raise to caller (fatal)

---

### 2. Executor Module

**File:** `src/gittyup/core/executor.py`

#### Purpose
Execute git commands on repositories with error handling and parallelization.

#### Key Classes

##### `GitExecutor`
```
Class: GitExecutor
Purpose: Execute git commands on repositories

Attributes:
  - timeout: int
    Command timeout in seconds (default: 300)
  
  - retry_attempts: int
    Number of retry attempts (default: 3)
  
  - retry_delay: int
    Delay between retries in seconds (default: 5)
  
  - parallel: bool
    Enable parallel execution
  
  - max_workers: int
    Number of parallel workers (default: 4)

Methods:
  - execute_batch(repos: List[Repository], operation: GitOperation) -> List[OperationResult]
    Execute operation on multiple repositories
    Returns: List of results (one per repository)
  
  - execute_single(repo: Repository, operation: GitOperation) -> OperationResult
    Execute operation on single repository
    Returns: Result object with status and output
  
  - _run_git_command(repo: Repository, args: List[str]) -> CommandResult
    Low-level git command execution
    Uses subprocess.run with security measures
  
  - _parse_git_output(stdout: str, stderr: str) -> ParsedOutput
    Parse git command output
    Extracts commits updated, errors, warnings
```

##### `GitOperation` (Enum)
```
Enum: GitOperation
Values:
  - PULL: Execute git pull --all
  - FETCH: Execute git fetch --all
  - STATUS: Execute git status
  
Each has associated:
  - command_args: List[str]
  - requires_clean_tree: bool
  - modifies_repo: bool
```

#### Parallel Execution Strategy

```
Strategy: ThreadPoolExecutor
Reason: I/O-bound operations (git commands wait on network/disk)

Implementation:
1. Create thread pool with max_workers threads
2. Submit all repositories to pool
3. Collect results as they complete
4. Handle exceptions gracefully
5. Ensure output thread safety (use locks)

Fallback:
- If parallel fails → fall back to sequential
- If system resources low → reduce workers
- Log performance metrics
```

#### Command Security

```
Security Measures:
1. Never use shell=True
2. Always use list-style arguments: ["git", "pull", "--all"]
3. Validate repository paths before execution
4. Set working directory explicitly
5. Limit environment variables
6. Set resource limits (timeout, memory)
7. Sanitize all outputs before display
```

---

### 3. Reporter Module

**File:** `src/gittyup/core/reporter.py`

#### Purpose
Format and display operation results with colors and progress indicators.

#### Key Classes

##### `Reporter`
```
Class: Reporter
Purpose: Handle all user-facing output

Attributes:
  - verbosity: VerbosityLevel
    Output verbosity (QUIET, NORMAL, VERBOSE)
  
  - use_color: bool
    Enable colored output
  
  - show_progress: bool
    Show progress bars
  
  - console: rich.Console
    Rich console for advanced formatting

Methods:
  - report_scan_start(path: Path) -> None
    Display scan start message
  
  - report_scan_progress(current: int, total: int) -> None
    Update scan progress
  
  - report_repositories_found(count: int) -> None
    Display count of found repositories
  
  - report_operation_start(repo: Repository, operation: GitOperation) -> None
    Display operation start for a repository
  
  - report_operation_result(result: OperationResult) -> None
    Display operation result with appropriate formatting
  
  - report_summary(results: List[OperationResult], elapsed_time: float) -> None
    Display final summary with statistics
  
  - report_error(error: Exception, context: str) -> None
    Display error message with context
```

#### Output Formatting Specifications

##### Success Output
```
Format: ✓ {repo_path} [{branch}] ← {status_message}
Color: Green (RGB: 0, 255, 0)
Example: ✓ ~/projects/gittyup [main] ← Updated (3 commits)
```

##### Warning Output
```
Format: ⚠ {repo_path} [{branch}] ← {warning_message}
Color: Yellow (RGB: 255, 255, 0)
Example: ⚠ ~/projects/api [develop] ← Uncommitted changes
```

##### Error Output
```
Format: ✗ {repo_path} [{branch}] ← {error_message}
Color: Red (RGB: 255, 0, 0)
Example: ✗ ~/projects/old [main] ← Error: Remote not found
```

##### Info Output
```
Format: 🔍 {message}
Color: Blue (RGB: 0, 150, 255)
Example: 🔍 Scanning for git repositories...
```

#### Progress Bar Specifications

```
Type: Rich progress bar
Update frequency: Every repository or every 100ms
Components:
  - Description: Current operation
  - Progress bar: Visual indicator
  - Percentage: Numeric progress
  - Count: X/Y items
  - Speed: Items per second
  - ETA: Estimated time remaining
```

---

## Data Models

### Repository Model

```
Class: Repository
Purpose: Represent a discovered git repository

Attributes:
  - path: Path
    Absolute path to repository root
  
  - branch: str
    Current branch name
  
  - has_remote: bool
    Whether repository has remote configured
  
  - remote_url: Optional[str]
    URL of primary remote (origin)
  
  - has_uncommitted_changes: bool
    Whether there are uncommitted changes
  
  - has_untracked_files: bool
    Whether there are untracked files
  
  - discovered_at: datetime
    When repository was discovered

Methods:
  - __str__() -> str
    Human-readable representation
  
  - to_dict() -> Dict[str, Any]
    Convert to dictionary (for JSON export)
  
  - is_clean() -> bool
    Check if working tree is clean
```

### OperationResult Model

```
Class: OperationResult
Purpose: Store result of git operation

Attributes:
  - repository: Repository
    Repository operated on
  
  - operation: GitOperation
    Operation performed
  
  - success: bool
    Whether operation succeeded
  
  - status: ResultStatus
    Detailed status (SUCCESS, WARNING, ERROR, SKIPPED)
  
  - message: str
    Human-readable result message
  
  - stdout: str
    Command standard output
  
  - stderr: str
    Command standard error
  
  - exit_code: int
    Command exit code
  
  - duration: float
    Operation duration in seconds
  
  - commits_updated: int
    Number of commits pulled (if applicable)
  
  - error: Optional[Exception]
    Exception if operation failed
  
  - executed_at: datetime
    When operation was executed

Methods:
  - is_success() -> bool
    Check if completely successful
  
  - is_warning() -> bool
    Check if succeeded with warnings
  
  - is_error() -> bool
    Check if failed
  
  - to_dict() -> Dict[str, Any]
    Convert to dictionary
```

### ResultStatus Enum

```
Enum: ResultStatus
Values:
  - SUCCESS: Operation completed successfully
  - SUCCESS_UP_TO_DATE: Already up to date (no changes)
  - WARNING_UNCOMMITTED: Has uncommitted changes
  - WARNING_UNTRACKED: Has untracked files
  - ERROR_NO_REMOTE: No remote configured
  - ERROR_AUTH_FAILED: Authentication failure
  - ERROR_NETWORK: Network error
  - ERROR_MERGE_CONFLICT: Merge conflict
  - ERROR_TIMEOUT: Operation timed out
  - ERROR_UNKNOWN: Unknown error
  - SKIPPED: Operation skipped (e.g., dry run)
```

---

## API Contracts

### Public API (for potential library usage)

#### Main Function

```
Function: sync_repositories(
    root_path: str | Path,
    *,
    operation: str = "pull",
    max_depth: int | None = None,
    exclude: List[str] | None = None,
    parallel: bool = True,
    max_workers: int = 4,
    verbose: bool = False,
    dry_run: bool = False,
    config_file: str | Path | None = None
) -> SyncResult

Purpose: Main entry point for repository synchronization

Parameters:
  - root_path: Directory to scan
  - operation: Git operation to perform (pull, fetch, status)
  - max_depth: Maximum depth to scan
  - exclude: Patterns to exclude
  - parallel: Enable parallel execution
  - max_workers: Number of parallel workers
  - verbose: Enable verbose output
  - dry_run: Don't execute, just show what would happen
  - config_file: Path to configuration file

Returns: SyncResult object containing:
  - repositories: List[Repository]
  - results: List[OperationResult]
  - summary: SummaryStats
  - duration: float

Raises:
  - ValueError: Invalid parameters
  - PathNotFoundError: root_path doesn't exist
  - ConfigError: Invalid configuration
```

#### Configuration API

```
Function: load_config(
    config_file: str | Path | None = None,
    override: Dict[str, Any] | None = None
) -> Config

Purpose: Load and merge configuration

Parameters:
  - config_file: Explicit config file path
  - override: Dictionary of values to override

Returns: Config object

Raises:
  - ConfigError: Invalid configuration file
  - FileNotFoundError: Config file not found
```

---

## Error Taxonomy

### Exception Hierarchy

```
GittyUpError (base exception)
├── ConfigError
│   ├── ConfigFileNotFoundError
│   ├── ConfigParseError
│   └── ConfigValidationError
├── ScanError
│   ├── PathNotFoundError
│   ├── PermissionDeniedError
│   └── SymlinkCycleError
├── ExecutionError
│   ├── GitCommandError
│   │   ├── GitAuthError
│   │   ├── GitNetworkError
│   │   ├── GitMergeConflictError
│   │   └── GitTimeoutError
│   └── ParallelExecutionError
└── ReportingError
    └── OutputError
```

### Error Handling Strategy by Exception Type

#### ConfigError
- **Action**: Display clear error with config file location
- **User Guidance**: Show what's wrong, how to fix
- **Exit Code**: 1
- **Recovery**: None (fatal)

#### PathNotFoundError
- **Action**: Display error with provided path
- **User Guidance**: Check path exists and is accessible
- **Exit Code**: 1
- **Recovery**: None (fatal)

#### PermissionDeniedError
- **Action**: Log warning, skip directory
- **User Guidance**: Check permissions if important
- **Exit Code**: 0 (if other repos succeed)
- **Recovery**: Continue with other directories

#### GitCommandError
- **Action**: Mark repository as failed, continue
- **User Guidance**: Provide git command to fix manually
- **Exit Code**: 3 (partial failure)
- **Recovery**: Continue with other repositories

#### GitAuthError
- **Action**: Mark repository as failed
- **User Guidance**: Check credentials, SSH keys, tokens
- **Exit Code**: 3
- **Recovery**: Continue with other repositories

---

## Performance Specifications

### Performance Targets

| Operation | Target | Measured As |
|-----------|--------|-------------|
| Directory scan | < 1ms per directory | Average time per directory |
| Git repository detection | < 5ms per directory | Time to check .git validity |
| Git pull (no updates) | < 2s per repo | Time from start to completion |
| Git pull (with updates) | < 10s per repo | Time from start to completion |
| Output rendering | < 100ms | Time to display all results |
| Startup time | < 100ms | Time from invocation to first output |

### Optimization Techniques

#### 1. Lazy Loading
```
Technique: Don't load full repository info until needed
Example: Only read git config if verbose mode requested
Benefit: Faster scanning, less I/O
```

#### 2. Caching
```
Technique: Cache repository discovery results
Example: .gittyup_cache with last scan results
Benefit: Skip unchanged directories on subsequent runs
Invalidation: Check directory mtime
```

#### 3. Parallel I/O
```
Technique: Use ThreadPoolExecutor for I/O operations
Example: Read multiple git configs in parallel
Benefit: Better utilization of I/O wait time
```

#### 4. Efficient Data Structures
```
Technique: Use generators instead of lists
Example: yield repositories as discovered
Benefit: Lower memory usage, faster startup
```

#### 5. Minimal Git Operations
```
Technique: Use porcelain commands, parse efficiently
Example: Use git rev-parse instead of full status when possible
Benefit: Faster git operations
```

### Performance Monitoring

```
Metrics to Track:
- scan_duration: Time spent scanning
- execution_duration: Time spent executing git commands
- total_duration: End-to-end time
- repositories_per_second: Throughput
- directories_scanned: Total directories checked
- memory_peak: Peak memory usage

Logging:
- Log performance metrics in verbose mode
- Optional --profile flag for detailed profiling
- Use cProfile for development profiling
```

---

## Security Specifications

### Input Validation

#### Path Validation
```
Function: validate_path(path: str | Path) -> Path
Checks:
  1. Path is not empty
  2. Path doesn't contain null bytes
  3. Path doesn't contain suspicious patterns (../../etc/passwd)
  4. Path resolves to real location (resolve symlinks)
  5. Path is within allowed boundaries
Returns: Validated, normalized Path object
Raises: ValidationError if invalid
```

#### Pattern Validation
```
Function: validate_pattern(pattern: str) -> str
Checks:
  1. Pattern is not empty
  2. Pattern doesn't contain suspicious characters
  3. Pattern is valid glob/regex
Returns: Validated pattern
Raises: ValidationError if invalid
```

### Subprocess Security

#### Command Execution Template
```
Best Practice Template:

def execute_git_command(repo_path: Path, args: List[str]) -> CommandResult:
    # 1. Validate all inputs
    validate_path(repo_path)
    validate_git_args(args)
    
    # 2. Build command safely
    cmd = ["git"] + args  # Never use shell=True
    
    # 3. Set secure environment
    env = {
        "GIT_TERMINAL_PROMPT": "0",  # Disable prompts
        "GIT_ASKPASS": "",           # No password prompts
    }
    
    # 4. Execute with constraints
    result = subprocess.run(
        cmd,
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=300,  # Prevent hanging
        env=env,
        shell=False,  # CRITICAL: Never True
    )
    
    # 5. Sanitize output before logging/display
    return sanitize_result(result)
```

### File System Security

#### Safe Path Operations
```
Rules:
1. Always use pathlib.Path for path operations
2. Use Path.resolve() to get absolute paths
3. Check for symlink cycles before following
4. Validate paths before any operation
5. Use context managers for file operations
6. Handle TOCTOU (Time-of-check-time-of-use) races
7. Never trust user input in file operations
```

### Dependency Security

#### Dependency Pinning
```
Strategy: Pin all dependencies to specific versions
Format: package==exact.version.number
Audit: Monthly dependency audits
Tools: 
  - pip-audit for vulnerability scanning
  - dependabot for automated updates
  - safety for known vulnerabilities
```

#### Minimal Dependencies
```
Principle: Only include necessary dependencies
Review: Each dependency must justify its inclusion
Alternatives: Prefer standard library when possible
```

---

## Testing Specifications

### Test Organization

```
tests/
├── unit/
│   ├── test_scanner.py         # Scanner module tests
│   ├── test_executor.py        # Executor module tests
│   ├── test_reporter.py        # Reporter module tests
│   ├── test_config.py          # Config handling tests
│   └── test_utils.py           # Utility function tests
├── integration/
│   ├── test_scan_execute.py    # Scanner + Executor integration
│   ├── test_config_loading.py  # Config + CLI integration
│   └── test_error_handling.py  # Error propagation
├── e2e/
│   ├── test_cli.py             # CLI end-to-end tests
│   └── test_real_repos.py      # Tests with real git repos
├── fixtures/
│   ├── configs/                # Sample config files
│   └── repos/                  # Sample repository structures
└── conftest.py                 # Shared fixtures
```

### Key Test Fixtures

```
Fixture: mock_git_repo
Purpose: Create temporary git repository for testing
Provides: Path to repo, git initialized, has commits

Fixture: mock_repo_tree
Purpose: Create directory tree with multiple git repos
Provides: Root path, list of repo paths

Fixture: mock_subprocess
Purpose: Mock subprocess.run for git commands
Provides: Controllable git command responses

Fixture: capture_output
Purpose: Capture console output for assertion
Provides: String buffer of output

Fixture: temp_config
Purpose: Create temporary config file
Provides: Path to config file, cleanup
```

### Test Coverage Requirements

```
Module Coverage Requirements:
- scanner.py: 95%+ (critical path)
- executor.py: 95%+ (critical path)
- reporter.py: 85%+ (mostly output formatting)
- config/: 90%+ (important for user experience)
- utils/: 90%+ (helper functions)
- cli.py: 75%+ (integration-focused)

Overall: 85%+ total coverage
```

---

## Appendix: Decision Log

### Decision 1: Click vs argparse
**Decision**: Use Click  
**Rationale**: Better UX, decorator-based, extensible, better help  
**Trade-offs**: Additional dependency vs standard library  
**Date**: Nov 2, 2025

### Decision 2: Rich vs colorama only
**Decision**: Use both (colorama as fallback, rich for enhanced)  
**Rationale**: Rich provides much better UX (progress bars, tables)  
**Trade-offs**: Larger dependency footprint vs much better UX  
**Date**: Nov 2, 2025

### Decision 3: GitPython vs subprocess
**Decision**: Use subprocess primarily, GitPython optional  
**Rationale**: Less abstraction, more control, fewer dependencies  
**Trade-offs**: More code vs more control  
**Date**: Nov 2, 2025

### Decision 4: Threading vs multiprocessing
**Decision**: Use threading (ThreadPoolExecutor)  
**Rationale**: I/O-bound workload, simpler communication  
**Trade-offs**: GIL limitation vs simplicity (not an issue for I/O)  
**Date**: Nov 2, 2025

### Decision 5: YAML vs TOML for config
**Decision**: Use YAML  
**Rationale**: More human-friendly, better for nested config  
**Trade-offs**: Parsing complexity vs readability  
**Date**: Nov 2, 2025

---

**Document Status:** Ready for Implementation  
**Last Updated:** November 2, 2025  
**Approval Required**: Yes - before Phase 1 coding begins

