# Java Code Review MCP Server

An MCP (Model Context Protocol) server that acts as a **Senior Java Software Engineer** with 15+ years of experience for automated code review. Built for **JDK 17/21** projects with full Spring Boot support and JBCT methodology compliance checking. Integrates with **OpenCode**, **Claude Code**, and **Claude Desktop**.

## Features

### Code Review Capabilities
- **Single File Review** — Analyze individual Java files with configurable review levels
- **Git Diff Review** — Review uncommitted changes, staged changes, or any git ref range
- **Full Project Review** — Project-wide analysis including dependency and architecture checks in one call
- **JBCT Compliance** — 37-rule Java Backend Coding Technology methodology validation
- **Spring Boot Compliance** — 6 rules covering common Spring pitfalls
- **File Result Caching** — Skips unchanged files on repeat project runs (keyed by mtime)

### Static Analysis (Pure Python)
- Code style checks (line length, indentation)
- Design pattern validation
- Security vulnerability detection (hardcoded credentials, SQL injection, sensitive logging)
- Performance optimization suggestions

### JDK 17+ Feature Detection
- Records for immutable DTOs
- Sealed classes for controlled inheritance
- Pattern matching (`instanceof`)
- Switch expressions
- Text blocks
- `var` keyword usage

### Java 21 Feature Detection
- Virtual threads (`Thread.ofVirtual()`)
- Structured concurrency (`StructuredTaskScope`)
- String templates

### Multi-Module Maven/Gradle Support
- Walks all `pom.xml` and `build.gradle` files in a project tree
- Aggregates dependencies across modules
- Detects cross-module version conflicts

### Review Levels
- **`full`** — All checks (default)
- **`quick`** — Critical & major severity only; skips style, JDK suggestions, JBCT style/naming
- **`security`** — Security checks only; no JBCT, no JDK suggestions

### Enhanced Reports
- Table of contents (when report has ≥3 sections)
- Summary dashboard with emoji severity indicators
- Top-5 most problematic files
- Issues grouped by severity then by file
- Layer dependency matrix for architecture reports

### Architecture Analysis
- Package structure validation (domain/adapter/usecase layers)
- Circular dependency detection
- Import flow validation (domain must not import adapter)
- Automatically included in `review_java_project` — no separate call needed

---

## Requirements

- Python 3.10+
- Git (for git diff reviews)

---

## Installation

```bash
# Clone or download this repository
cd java-code-review-mcp

# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Or with uv:

```bash
uv venv
uv add "mcp[cli]" fastmcp javalang rich pyyaml
```

---

## Configuration

Edit `config/code_review_config.md` (or a YAML file loaded via `load_custom_config`) to customize:

### Coding Style & Thresholds

```yaml
max_line_length: 120
indent_size: 4
use_spaces: true
max_method_length: 30
max_class_length: 500
max_parameters: 5
```

### Security Checks

```yaml
security:
  check_hardcoded_secrets: true
  check_sql_injection: true
  check_logging_sensitive: true
```

### JDK 17+ Feature Recommendations

```yaml
jdk17_features:
  recommend_records: true
  recommend_sealed_classes: true
  recommend_switch_expressions: true
  recommend_text_blocks: true
  recommend_var_keyword: true
  recommend_pattern_matching: true
```

### Java 21 Feature Recommendations

```yaml
jdk21_features:
  recommend_virtual_threads: true
  recommend_structured_concurrency: true
  recommend_string_templates: true
```

### Spring Boot Analysis

Spring analysis is **disabled by default** to avoid false positives on non-Spring projects.

```yaml
spring_enabled: true   # Enable Spring Boot rule checks

spring_rules:
  transactional: true        # SPRING-TX-01
  field_injection: true      # SPRING-DI-01
  circular_autowired: true   # SPRING-DI-02
  missing_stereotype: true   # SPRING-STEREO-01
  rest_return_types: true    # SPRING-REST-01
  value_fallback: true       # SPRING-CONFIG-01
```

### JBCT Profile Settings

```yaml
jbct_profile: basic   # disabled | basic | full

jbct_rules:
  return_types: true      # RET-01 to RET-05
  exceptions: true        # EX-01, EX-02
  value_objects: true     # VO-01, VO-02
  lambda_rules: true      # LAM-01, LAM-02, LAM-03, NEST-01
  patterns: true          # PAT-01, PAT-02, SEQ-01
  architecture: true      # MIX-01
  naming: true            # NAM-01, NAM-02, ACR-01
  zones: true             # ZONE-01, ZONE-02, ZONE-03
  style: true             # STY-01 to STY-06
  logging: true           # LOG-01, LOG-02
  static_imports: true    # STATIC-01
  utilities: true         # UTIL-01, UTIL-02
  sealed_types: true      # SEAL-01
  usecase: true           # UC-01
```

**Profile levels:**
- **`disabled`** — No JBCT checks
- **`basic`** — Core 12 rules (return types, exceptions, value objects, lambdas, patterns, architecture, naming, zones)
- **`full`** — All 37 JBCT rules

### Package Patterns

```yaml
jbct_packages:
  domain_patterns:
    - "**.domain.**"
    - "**.usecase.**"
  adapter_patterns:
    - "**.adapter.**"
    - "**.io.**"
```

### Zone Verbs

```yaml
zone2_verbs:
  - validate
  - process
  - handle
  - execute

zone3_verbs:
  - get
  - fetch
  - parse
  - load
```

---

## Running the Server

```bash
# With Python
python src/server.py

# With uv
uv run python src/server.py
```

The server uses the `JAVA_REVIEW_CONFIG` environment variable to locate a custom config file:

```bash
JAVA_REVIEW_CONFIG=/path/to/config.yaml python src/server.py
```

---

## MCP Tools Reference

### Tool Summary

| Tool | Key Parameters | Description |
|------|---------------|-------------|
| `review_java_file` | `file_path`, `output_format`, `review_level` | Review a single Java file |
| `review_java_git_diff` | `repo_path`, `output_format`, `review_level`, `ref`, `staged` | Review git diff (uncommitted, staged, or any ref) |
| `review_java_project` | `project_path`, `output_format`, `review_level`, `include_deps`, `use_cache` | Full project review including architecture |
| `analyze_java_static` | `file_path`, `tools` | Low-level static analysis on a single file |
| `analyze_java_dependencies` | `project_path`, `build_tool` | Maven/Gradle multi-module dependency analysis |
| `analyze_java_architecture` | `project_path`, `output_format` | Architecture validation with layer matrix |
| `analyze_spring_compliance` | `file_path`, `output_format` | Spring Boot / Spring Framework rule checks |
| `review_jbct_compliance` | `file_path`, `output_format`, `profile` | JBCT methodology compliance (file or directory) |
| `get_review_checklist` | `checklist_type` | Retrieve the review checklist |
| `get_current_config` | — | Display active configuration |
| `get_jbct_config` | — | Display JBCT-specific configuration |
| `load_custom_config` | `config_path` | Load a YAML or Markdown config file |

---

### `review_java_file`

Review a single Java file for style, security, design, and JDK modernization issues.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | required | Path to the `.java` file |
| `output_format` | string | `"markdown"` | `markdown`, `json`, `sarif`, or `both` |
| `review_level` | string | `"full"` | `full`, `quick`, or `security` |

---

### `review_java_git_diff`

Review Java changes from git. By default reviews unstaged changes (`git diff`).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_path` | string | `"."` | Path to git repository root |
| `output_format` | string | `"markdown"` | `markdown`, `json`, `sarif`, or `both` |
| `review_level` | string | `"full"` | `full`, `quick`, or `security` |
| `ref` | string | `""` | Compare against a git ref (e.g. `HEAD~1`, `main`, a commit SHA). Mutually exclusive with `staged`. |
| `staged` | boolean | `false` | When `true`, reviews only staged changes (`git diff --cached`) |

---

### `review_java_project`

Review an entire Java project. Automatically includes architecture analysis and (optionally) dependency analysis.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_path` | string | required | Path to Java project root |
| `output_format` | string | `"markdown"` | `markdown`, `json`, `sarif`, or `both` |
| `review_level` | string | `"full"` | `full`, `quick`, or `security` |
| `include_deps` | boolean | `true` | Analyze Maven/Gradle dependencies |
| `use_cache` | boolean | `true` | Cache per-file results (keyed by path + mtime); skips unchanged files on re-runs |

---

### `analyze_java_static`

Run low-level static analysis on a single Java file.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | required | Path to the `.java` file |
| `tools` | string | `"all"` | Which checks to run |

---

### `analyze_java_dependencies`

Analyze Maven or Gradle dependencies. Supports multi-module projects — walks the full project tree for all `pom.xml` / `build.gradle` files and detects cross-module version conflicts.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_path` | string | required | Path to Java project root |
| `build_tool` | string | `"auto"` | `auto`, `maven`, or `gradle` |

---

### `analyze_java_architecture`

Validate project architecture: package structure, circular dependency detection, and import flow (domain must not import adapter). Also generates a layer dependency matrix.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_path` | string | required | Path to Java project directory |
| `output_format` | string | `"markdown"` | `markdown`, `json`, or `sarif` |

> **Note:** `review_java_project` automatically calls this — you only need `analyze_java_architecture` directly for architecture-only analysis.

---

### `analyze_spring_compliance`

Check a Java file or project directory for Spring Boot / Spring Framework issues. Requires `spring_enabled: true` in config for the rules to fire.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | required | Path to a `.java` file or project directory |
| `output_format` | string | `"markdown"` | `markdown`, `json`, or `sarif` |

---

### `review_jbct_compliance`

Check a Java file or directory for JBCT methodology compliance.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | required | Path to a `.java` file or project directory |
| `output_format` | string | `"markdown"` | `markdown`, `json`, or `sarif` |
| `profile` | string | `"basic"` | `basic` (12 core rules) or `full` (all 37 rules) |

---

### `get_review_checklist`

Retrieve the code review checklist.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `checklist_type` | string | `"full"` | `full` or `quick` |

---

### `load_custom_config`

Load a YAML or Markdown configuration file at runtime.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_path` | string | required | Path to `.yaml`, `.yml`, or `.md` config file |

---

## Output Formats

Reports can be generated in:

| Format | Description |
|--------|-------------|
| `markdown` | Human-readable (default) |
| `json` | Machine-readable for CI/CD pipelines |
| `sarif` | Industry-standard for GitHub Code Scanning, Azure DevOps, etc. |
| `both` | Markdown + JSON combined |

---

## Review Levels

| Level | What is checked |
|-------|----------------|
| `full` | Everything — style, design, security, JDK suggestions, JBCT (all severities) |
| `quick` | Critical and major severity issues only; skips style rules, JDK suggestions, and JBCT style/naming rules |
| `security` | Security category only (`HardcodedCredentials`, `SQLInjection`); no JBCT, no JDK suggestions |

---

## MCP Resources

The server exposes three read-only resources accessible via MCP resource URIs:

| URI | Description |
|-----|-------------|
| `checklist://full` | Full code review checklist as JSON |
| `checklist://quick` | Quick checklist as JSON |
| `config://current` | Active configuration as JSON |

---

## Integration

### OpenCode

Add to your project's `opencode.json`:

```json
{
  "mcp": {
    "java-code-review": {
      "type": "local",
      "command": ["python", "path/to/java-code-review-mcp/src/server.py"],
      "enabled": true
    }
  }
}
```

**Example prompts:**

```
Review the Java file src/main/java/com/example/MyService.java
Check this file for JBCT compliance: src/main/java/com/example/MyService.java
Do a full code review of this project
Run JBCT compliance check on the src/main/java directory
Analyze Spring Boot issues in this project
Show me the current code review configuration
```

---

### Claude Code

Add to `~/.claude/claude_desktop_config.json` (or via `claude mcp add`):

```json
{
  "mcpServers": {
    "java-code-review": {
      "command": "python",
      "args": ["path/to/java-code-review-mcp/src/server.py"]
    }
  }
}
```

**Example prompts:**

```
Review this Java file for issues
Review my uncommitted Java changes
Run a quick review of the project (critical issues only)
Check for Spring Boot problems in src/main/java
Run JBCT compliance check on this directory
What JBCT rules are enabled?
Show the current config
```

---

### Claude Desktop

Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "java-code-review": {
      "command": "python",
      "args": ["path/to/java-code-review-mcp/src/server.py"]
    }
  }
}
```

---

## JBCT Methodology

The server includes **JBCT (Java Backend Coding Technology)** compliance checking — a methodology for writing predictable, testable Java backend code. Especially useful for AI-assisted development.

### What is JBCT?

JBCT provides mechanical rules for:
- **Return Types**: Every method returns one of `T`, `Option<T>`, `Result<T>`, or `Promise<T>`
- **Error Handling**: Use `Cause` with `Result/Promise`, not exceptions
- **Value Objects**: Factory methods returning `Result<T>`
- **Lambda Rules**: No complex logic in lambdas
- **Architecture**: No I/O in domain packages
- **Naming**: Consistent conventions for factories and validation

### JBCT Rules (37 Total)

#### Return Types (5 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-RET-01 | ERROR | Business methods must use T, Option, Result, or Promise |
| JBCT-RET-02 | ERROR | No nested wrappers (`Promise<Result<T>>`, `Option<Option<T>>`) |
| JBCT-RET-03 | ERROR | Never return null — use `Option<T>` |
| JBCT-RET-04 | WARNING | Use `Unit` instead of `Void` |
| JBCT-RET-05 | WARNING | Avoid always-succeeding Result (return T directly) |

#### Exceptions (2 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-EX-01 | ERROR | No business exceptions — use Cause with Result/Promise |
| JBCT-EX-02 | ERROR | Don't use `orElseThrow()` — use Result/Option |

#### Value Objects (2 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-VO-01 | WARNING | Value objects should have factory returning `Result<T>` |
| JBCT-VO-02 | WARNING | Don't bypass factory — use factory method |

#### Lambda (4 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-LAM-01 | WARNING | No complex logic in lambdas (if, switch, try-catch) |
| JBCT-LAM-02 | WARNING | No braces in lambdas — extract to methods |
| JBCT-LAM-03 | WARNING | No ternary in lambdas — use `filter()` or extract |
| JBCT-NEST-01 | WARNING | No nested monadic operations in lambdas |

#### Patterns (3 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-PAT-01 | WARNING | Use functional iteration instead of raw loops |
| JBCT-PAT-02 | WARNING | No Fork-Join inside Sequencer |
| JBCT-SEQ-01 | WARNING | Chain length limit (2–5 steps) |

#### Architecture (1 rule)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-MIX-01 | ERROR | No I/O operations in domain packages |

#### Naming (3 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-NAM-01 | WARNING | Factory methods: `TypeName.typeName()` |
| JBCT-NAM-02 | WARNING | Use `Valid` prefix, not `Validated` |
| JBCT-ACR-01 | WARNING | Acronyms should use PascalCase |

#### Zones (3 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-ZONE-01 | WARNING | Step interfaces use Zone 2 verbs |
| JBCT-ZONE-02 | WARNING | Leaf functions use Zone 3 verbs |
| JBCT-ZONE-03 | WARNING | No zone mixing in sequencer chains |

#### Style (6 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-STY-01 | WARNING | Prefer fluent failure: `cause.result()` |
| JBCT-STY-02 | WARNING | Prefer constructor references: `X::new` |
| JBCT-STY-03 | WARNING | No fully qualified class names in code |
| JBCT-STY-04 | WARNING | Utility class pattern: sealed interface |
| JBCT-STY-05 | WARNING | Prefer method references over lambdas |
| JBCT-STY-06 | WARNING | Import ordering: java → javax → pragmatica → third-party → project |

#### Logging (2 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-LOG-01 | WARNING | No conditional logging |
| JBCT-LOG-02 | WARNING | No logger as method parameter |

#### Other Rules (5 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-STATIC-01 | WARNING | Prefer static imports for Pragmatica |
| JBCT-UTIL-01 | WARNING | Use Pragmatica parsing utilities |
| JBCT-UTIL-02 | WARNING | Use `Verify.Is` predicates |
| JBCT-SEAL-01 | WARNING | Error interfaces should be sealed |
| JBCT-UC-01 | WARNING | Use case factories return lambdas |

---

## Spring Boot Support

The `analyze_spring_compliance` tool (and the `spring_enabled` config flag) add Spring-specific checks. Enable with `spring_enabled: true` in your config.

### Spring Rules (6 rules)

| Rule | Severity | Description |
|------|----------|-------------|
| SPRING-TX-01 | major | `@Transactional` on non-public method — Spring proxy cannot intercept it |
| SPRING-DI-01 | major | `@Autowired` field injection — prefer constructor injection |
| SPRING-DI-02 | major | Class appears to inject itself — likely circular dependency |
| SPRING-STEREO-01 | minor | Missing `@Service`/`@Repository`/`@Component` on service-like class |
| SPRING-REST-01 | minor | `@RestController` method returns raw type instead of `ResponseEntity` |
| SPRING-CONFIG-01 | minor | `@Value` with hardcoded fallback masks missing config property |

### Quick Start

```yaml
# config/code_review_config.md (or your YAML config)
spring_enabled: true
```

Then in your AI assistant:

```
Analyze Spring Boot issues in src/main/java/com/example/
```

---

## Architecture Analysis

The `analyze_java_architecture` tool (and the automatic architecture step in `review_java_project`) perform:

1. **Package Structure Validation** — checks for domain, adapter, and usecase layers
2. **Circular Dependency Detection** — finds circular imports between packages and shows the cycle path
3. **Import Flow Validation** — ensures domain packages don't import adapter packages
4. **Layer Dependency Matrix** — renders a layer × layer table showing allowed/violated dependencies

### Usage

Call directly for architecture-only analysis:

```
Analyze the architecture of this Java project
Check for circular dependencies in the codebase
```

Or get it automatically as part of a full project review:

```
Do a full code review of this Java project
```

---

## CI/CD: SARIF Output

### GitHub Actions

```yaml
name: Java Code Review

on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run JBCT Check
        run: |
          python -c "
          from src.tools.code_review import review_jbct_project
          from src.tools.report_generator import generate_report
          from src.config.loader import load_config, get_config
          import asyncio

          load_config()
          config = get_config()
          config['jbct_profile'] = 'basic'

          result = asyncio.run(review_jbct_project('src/main/java', config))
          print(generate_report(result, 'sarif'))
          " > results.sarif
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

### Azure DevOps

Configure the SARIF results in your pipeline for security scanning integration.

---

## Testing

The project includes a test suite with 61 tests across 6 modules.

### Running Tests

```bash
# Quick summary
python -m pytest tests/ -q

# Verbose with test names
python -m pytest tests/ -v

# Single module
python -m pytest tests/test_spring_analyzer.py -v
```

### Test Modules

| Module | Coverage |
|--------|----------|
| `test_static_analysis.py` | Static analysis rules, JDK 17/21 suggestions, security checks |
| `test_jbct_analyzer.py` | All 37 JBCT rules |
| `test_dependency_analyzer.py` | Maven/Gradle multi-module parsing, version conflict detection |
| `test_git_diff_parser.py` | Git diff parsing, ref and staged modes |
| `test_spring_analyzer.py` | All 6 Spring rules |
| `test_code_review.py` | End-to-end orchestration (review_file, review_project, caching) |

Test fixtures are in `tests/fixtures/` (e.g., `SecurityIssues.java`, `JbctViolations.java`, `SpringIssues.java`).

---

## License

MIT License
