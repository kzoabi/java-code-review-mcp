# Java Code Review MCP Server

An MCP (Model Context Protocol) server that acts as a **Senior Java Software Engineer** with 15+ years of experience for automated code review. Built for **JDK 17+** projects and integrates with **OpenCode** and **Claude Code**.

## Features

### Code Review Capabilities
- **Single File Review** - Analyze individual Java files
- **Git Diff Review** - Review uncommitted changes
- **Full Project Review** - Comprehensive project-wide analysis
- **Dependency Analysis** - Maven and Gradle support

### Static Analysis (Pure Python)
- Code style checks
- Design pattern validation
- Security vulnerability detection
- Performance optimization suggestions

### JDK 17+ Migration Support
- Records for immutable DTOs
- Sealed classes for controlled inheritance
- Pattern matching (instanceof)
- Switch expressions
- Text blocks
- Var keyword usage

### JBCT Methodology Support
- **JBCT Compliance Checking** - Validate code against Java Backend Coding Technology methodology
- **37 Rules** covering:
  - Return types (T, Option, Result, Promise)
  - Exception handling (use Cause, not exceptions)
  - Value object patterns (factory methods)
  - Lambda complexity rules
  - Functional iteration patterns
  - Architecture (no I/O in domain packages)
  - Naming conventions
  - Zone-based method naming
  - Style, logging, static imports, utilities, sealed types
- **SARIF Output** - Industry-standard format for CI/CD integration

### Architecture Analysis
- **Package Structure Validation** - Check for domain/adapter/usecase layers
- **Circular Dependency Detection** - Find circular imports between packages
- **Import Flow Validation** - Ensure domain doesn't import adapter

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

## Configuration

Edit `config/code_review_config.md` to customize:

- Line length limits
- Method/class length thresholds
- JDK 17+ feature recommendations
- Security checks
- Rule severity levels

## Usage

### Running the Server

```bash
# With Python
python src/server.py

# With uv
uv run python src/server.py
```

### MCP Tools Available

| Tool | Description |
|------|-------------|
| `review_java_file` | Review a single Java file |
| `review_java_git_diff` | Review uncommitted changes |
| `review_java_project` | Review entire project |
| `analyze_java_static` | Run static analysis |
| `analyze_java_dependencies` | Analyze Maven/Gradle deps |
| `analyze_java_architecture` | Analyze package structure and dependencies |
| `get_review_checklist` | Get review checklist |
| `get_current_config` | Show current config |
| `load_custom_config` | Load custom config |
| `review_jbct_compliance` | JBCT methodology compliance check |
| `get_jbct_config` | Show JBCT configuration |

## OpenCode Integration

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

## Claude Desktop Integration

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

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

## Example Usage

### Review a file:
```
Review the Java file src/main/java/com/example/MyService.java
```

### Review git changes:
```
Review my uncommitted changes in this Java project
```

### Review entire project:
```
Do a full code review of this Java project
```

### Analyze architecture:
```
Analyze the architecture of this project
```

### Analyze dependencies:
```
Analyze Maven dependencies in this project
```

## Output Formats

Reports can be generated in:
- **Markdown** (default) - Human-readable
- **JSON** - For CI/CD integration
- **SARIF** - Industry-standard format for GitHub Code Scanning, Azure DevOps, etc.
- **Both** - Combined output

---

## JBCT Methodology Support

The server includes **JBCT (Java Backend Coding Technology)** compliance checking - a methodology for writing predictable, testable Java code. This is especially useful for AI-assisted development.

### What is JBCT?

JBCT provides mechanical rules for:
- **Return Types**: Every method returns one of `T`, `Option<T>`, `Result<T>`, or `Promise<T>`
- **Error Handling**: Use `Cause` with `Result/Promise`, not exceptions
- **Value Objects**: Factory methods returning `Result<T>`
- **Lambda Rules**: No complex logic in lambdas
- **Architecture**: No I/O in domain packages
- **Naming**: Consistent conventions for factories and validation

### JBCT Rules (37 Total Rules)

#### Return Types (5 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-RET-01 | ERROR | Business methods must use T, Option, Result, or Promise |
| JBCT-RET-02 | ERROR | No nested wrappers (Promise<Result<T>>, Option<Option<T>>) |
| JBCT-RET-03 | ERROR | Never return null - use Option<T> |
| JBCT-RET-04 | WARNING | Use Unit instead of Void |
| JBCT-RET-05 | WARNING | Avoid always-succeeding Result (return T directly) |

#### Exceptions (2 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-EX-01 | ERROR | No business exceptions - use Cause with Result/Promise |
| JBCT-EX-02 | ERROR | Don't use orElseThrow() - use Result/Option |

#### Value Objects (2 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-VO-01 | WARNING | Value objects should have factory returning Result<T> |
| JBCT-VO-02 | WARNING | Don't bypass factory - use factory method |

#### Lambda (4 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-LAM-01 | WARNING | No complex logic in lambdas (if, switch, try-catch) |
| JBCT-LAM-02 | WARNING | No braces in lambdas - extract to methods |
| JBCT-LAM-03 | WARNING | No ternary in lambdas - use filter() or extract |
| JBCT-NEST-01 | WARNING | No nested monadic operations in lambdas |

#### Patterns (3 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-PAT-01 | WARNING | Use functional iteration instead of raw loops |
| JBCT-PAT-02 | WARNING | No Fork-Join inside Sequencer |
| JBCT-SEQ-01 | WARNING | Chain length limit (2-5 steps) |

#### Architecture (1 rule)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-MIX-01 | ERROR | No I/O operations in domain packages |

#### Naming (3 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-NAM-01 | WARNING | Factory methods: TypeName.typeName() |
| JBCT-NAM-02 | WARNING | Use Valid prefix, not Validated |
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
| JBCT-STY-01 | WARNING | Prefer fluent failure: cause.result() |
| JBCT-STY-02 | WARNING | Prefer constructor references: X::new |
| JBCT-STY-03 | WARNING | No fully qualified class names in code |
| JBCT-STY-04 | WARNING | Utility class pattern: sealed interface |
| JBCT-STY-05 | WARNING | Prefer method references over lambdas |
| JBCT-STY-06 | WARNING | Import ordering: java → javax → pragmatica → third-party → project |

#### Logging (2 rules)
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-LOG-01 | WARNING | No conditional logging |
| JBCT-LOG-02 | WARNING | No logger as method parameter |

#### Other Rules
| Rule | Severity | Description |
|------|----------|-------------|
| JBCT-STATIC-01 | WARNING | Prefer static imports for Pragmatica |
| JBCT-UTIL-01 | WARNING | Use Pragmatica parsing utilities |
| JBCT-UTIL-02 | WARNING | Use Verify.Is predicates |
| JBCT-SEAL-01 | WARNING | Error interfaces should be sealed |
| JBCT-UC-01 | WARNING | Use case factories return lambdas |

---

## OpenCode Usage

### Configuration

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

### Available Commands

```markdown
# Review a single file
Review the Java file src/main/java/com/example/MyService.java

# Review with JBCT compliance
Check this file for JBCT compliance: src/main/java/com/example/MyService.java

# Full project review
Do a full code review of this project

# Run JBCT analysis on entire project
Run JBCT compliance check on the src/main/java directory

# Get current configuration
Show me the current code review configuration

# Get JBCT configuration
Show me the JBCT configuration
```

### JBCT-Specific OpenCode Commands

```markdown
# Check JBCT compliance on a file (basic profile)
Review file src/main/java/com/example/Service.java for JBCT compliance

# Check JBCT compliance on entire project
Run JBCT methodology check on this project

# Check with full JBCT profile
Run full JBCT compliance check on src/main/java

# Check with SARIF output for CI/CD
Run JBCT check on src/main/java and output as SARIF

# View JBCT rules
What JBCT rules are enabled?
```

---

## Claude Code Usage

### Configuration

Add to Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`):

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

### Available Commands

```markdown
# Review a single file
/review-java-file src/main/java/com/example/MyService.java

# Review project
/review-java-project /path/to/project

# JBCT compliance check
/review-jbct src/main/java/com/example/MyService.java

# Full JBCT project check
/review-jbct /path/to/project

# Get configuration
/get-config

# Get JBCT config
/get-jbct-config
```

### JBCT-Specific Claude Code Commands

```markdown
# Basic JBCT check
Use review_jbct_compliance on src/main/java/com/example/Service.java

# Full JBCT profile
Run review_jbct_compliance with profile "full" on the project

# SARIF output for GitHub
Run JBCT check with SARIF output format on the src directory

# Check specific rules
Show me JBCT value object violations in this file
```

---

## Configuration

### JBCT Profile Settings

Edit `config/code_review_config.md` to customize JBCT:

```yaml
## JBCT Profile
jbct_profile: basic  # disabled | basic | full

## JBCT Rule Categories (14 categories, 37 rules total)
jbct_rules:
  return_types: true      # RET-01 to RET-05
  exceptions: true         # EX-01, EX-02
  value_objects: true     # VO-01, VO-02
  lambda_rules: true      # LAM-01, LAM-02, LAM-03, NEST-01
  patterns: true         # PAT-01, PAT-02, SEQ-01
  architecture: true     # MIX-01
  naming: true          # NAM-01, NAM-02, ACR-01
  zones: true           # ZONE-01, ZONE-02, ZONE-03
  style: true           # STY-01 to STY-06
  logging: true         # LOG-01, LOG-02
  static_imports: true  # STATIC-01
  utilities: true      # UTIL-01, UTIL-02
  sealed_types: true   # SEAL-01
  usecase: true        # UC-01
```

### Profile Levels

- **disabled**: No JBCT checks
- **basic**: Core 12 rules (return types, exceptions, value objects, lambdas, patterns, architecture, naming, zones)
- **full**: All 37 JBCT rules

### Package Patterns

Configure domain and adapter package patterns:

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

Customize zone verbs for naming rules:

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

## SARIF Output for CI/CD

### GitHub Code Scanning

```bash
# Run JBCT check with SARIF output
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
```

### GitHub Actions

```yaml
name: JBCT Code Review

on: [pull_request]

jobs:
  jbct:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run JBCT Check
        run: |
          # Run your JBCT check and save SARIF
          python -c "..." > results.sarif
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

### Azure DevOps

Configure the SARIF results in your pipeline for security scanning.

---

## Architecture Analysis

The `analyze_java_architecture` tool performs comprehensive architecture validation:

### Features

1. **Package Structure Validation**
   - Checks for domain, adapter, and usecase layers
   - Reports missing architectural layers

2. **Circular Dependency Detection**
   - Finds circular imports between packages
   - Shows dependency cycle path

3. **Import Flow Validation**
   - Ensures domain packages don't import adapter packages
   - Validates clean architecture boundaries

### Usage

```bash
# Analyze project architecture
analyze_java_architecture /path/to/project

# With SARIF output for CI/CD
analyze_java_architecture /path/to/project --output-format sarif
```

### OpenCode/Claude Code Commands

```markdown
# Analyze architecture
Analyze the architecture of this Java project

# Check for circular dependencies
Check for circular dependencies in the codebase
```

## Requirements

- Python 3.10+
- JDK 17+ (for analyzing modern Java code)
- Git (for git diff reviews)

## License

MIT License

## Author

Java Code Review MCP Team
