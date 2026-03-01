"""Java Code Review MCP Server"""
import os
import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

mcp = FastMCP("JavaCodeReview")

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "code_review_config.md"

from src.tools.code_review import review_file, review_git_diff, review_project, review_jbct_file, review_jbct_project
from src.tools.static_analysis import run_static_analysis
from src.tools.dependency_analyzer import analyze_dependencies
from src.tools.architecture_analyzer import analyze_architecture
from src.tools.report_generator import generate_report
from src.config.loader import load_config, get_config

@mcp.tool()
async def review_java_file(file_path: str, output_format: str = "markdown", review_level: str = "full") -> str:
    """Review a single Java file."""
    logger.info(f"Reviewing file: {file_path}")
    try:
        config = get_config()
        result = await review_file(file_path, review_level, config)
        return generate_report(result, output_format)
    except Exception as e:
        logger.error(f"Error reviewing file: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def review_java_git_diff(repo_path: str = ".", output_format: str = "markdown", review_level: str = "full") -> str:
    """Review uncommitted changes (git diff)."""
    logger.info(f"Reviewing git diff in: {repo_path}")
    try:
        config = get_config()
        result = await review_git_diff(repo_path, review_level, config)
        return generate_report(result, output_format)
    except Exception as e:
        logger.error(f"Error reviewing git diff: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def review_java_project(project_path: str, output_format: str = "markdown", review_level: str = "full", include_deps: bool = True) -> str:
    """Review an entire Java project."""
    logger.info(f"Reviewing project: {project_path}")
    try:
        config = get_config()
        result = await review_project(project_path, review_level, config, include_deps)
        return generate_report(result, output_format)
    except Exception as e:
        logger.error(f"Error reviewing project: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def analyze_java_static(file_path: str, tools: str = "all") -> str:
    """Run static analysis on a Java file."""
    logger.info(f"Running static analysis on: {file_path}")
    try:
        config = get_config()
        result = await run_static_analysis(file_path, tools, config)
        return generate_report(result, "markdown")
    except Exception as e:
        logger.error(f"Error in static analysis: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def analyze_java_dependencies(project_path: str, build_tool: str = "auto") -> str:
    """Analyze Maven or Gradle dependencies."""
    logger.info(f"Analyzing dependencies in: {project_path}")
    try:
        result = await analyze_dependencies(project_path, build_tool)
        return generate_report(result, "markdown")
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def get_review_checklist(checklist_type: str = "full") -> str:
    """Get the code review checklist."""
    from src.checklist import get_checklist
    checklist = get_checklist(checklist_type)
    md = "# Java Code Review Checklist\n\n"
    for category, items in checklist.items():
        md += f"## {category}\n\n"
        for item in items:
            md += f"- [ ] {item}\n"
        md += "\n"
    return md

@mcp.tool()
async def get_current_config() -> str:
    """Get the current configuration."""
    config = get_config()
    md = "# Current Code Review Configuration\n\n"
    md += f"## Coding Style\n- Max Line Length: {config.get('max_line_length', 120)}\n- Indent Size: {config.get('indent_size', 4)}\n- Use Spaces: {config.get('use_spaces', True)}\n\n"
    md += f"## Thresholds\n- Max Method Length: {config.get('max_method_length', 30)}\n- Max Class Length: {config.get('max_class_length', 500)}\n- Max Parameters: {config.get('max_parameters', 5)}\n\n"
    md += f"## JDK 17+ Features\n"
    jdk17 = config.get('jdk17_features', {})
    for feature, enabled in jdk17.items():
        md += f"- {feature}: {'Enabled' if enabled else 'Disabled'}\n"
    md += f"\n## JBCT Profile\n- Profile: {config.get('jbct_profile', 'disabled')}\n"
    jbct_rules = config.get('jbct_rules', {})
    for rule, enabled in jbct_rules.items():
        md += f"- {rule}: {'Enabled' if enabled else 'Disabled'}\n"
    return md

@mcp.tool()
async def load_custom_config(config_path: str) -> str:
    """Load a custom configuration file."""
    try:
        load_config(config_path)
        return f"Successfully loaded configuration from: {config_path}"
    except Exception as e:
        return f"Error loading config: {str(e)}"

@mcp.tool()
async def review_jbct_compliance(file_path: str, output_format: str = "markdown", profile: str = "basic") -> str:
    """Review Java file for JBCT methodology compliance.
    
    JBCT (Java Backend Coding Technology) is a methodology for writing
    predictable, testable Java backend code. This tool checks for:
    - Return types (T, Option, Result, Promise)
    - Exception handling (use Cause, not exceptions)
    - Value object patterns (factory methods)
    - Lambda complexity rules
    - Functional iteration patterns
    - Architecture (no I/O in domain)
    - Naming conventions
    - Zone-based method naming
    
    Args:
        file_path: Path to Java file or project directory
        output_format: Output format - markdown, json, or sarif
        profile: JBCT profile - basic or full
    """
    logger.info(f"Running JBCT compliance review on: {file_path}")
    try:
        config = get_config()
        config['jbct_profile'] = profile
        
        import os
        if os.path.isdir(file_path):
            result = await review_jbct_project(file_path, config)
        else:
            result = await review_jbct_file(file_path, config)
        
        return generate_report(result, output_format)
    except Exception as e:
        logger.error(f"Error in JBCT compliance review: {e}")
        return f"Error: {str(e)}"

@mcp.tool()
async def get_jbct_config() -> str:
    """Get current JBCT configuration."""
    config = get_config()
    md = "# JBCT Configuration\n\n"
    md += f"**Profile:** {config.get('jbct_profile', 'disabled')}\n\n"
    md += "## Enabled Rules\n\n"
    jbct_rules = config.get('jbct_rules', {})
    for rule, enabled in jbct_rules.items():
        status = "✓" if enabled else "✗"
        md += f"- {status} {rule}\n"
    md += "\n## Package Patterns\n\n"
    jbct_packages = config.get('jbct_packages', {})
    for pattern_type, patterns in jbct_packages.items():
        md += f"**{pattern_type}:**\n"
        for p in patterns:
            md += f"- {p}\n"
    return md

@mcp.tool()
async def analyze_java_architecture(project_path: str, output_format: str = "markdown") -> str:
    """Analyze Java project architecture.
    
    Performs architecture validation including:
    - Package structure validation
    - Circular dependency detection
    - Import flow validation (domain should not import adapter)
    
    Args:
        project_path: Path to Java project directory
        output_format: Output format - markdown, json, or sarif
    """
    logger.info(f"Analyzing architecture for: {project_path}")
    try:
        config = get_config()
        result = await analyze_architecture(project_path, config)
        return generate_report(result, output_format)
    except Exception as e:
        logger.error(f"Error in architecture analysis: {e}")
        return f"Error: {str(e)}"

@mcp.resource("checklist://full")
def get_full_checklist() -> str:
    from src.checklist import get_checklist
    import json
    return json.dumps(get_checklist("full"), indent=2)

@mcp.resource("checklist://quick")
def get_quick_checklist() -> str:
    from src.checklist import get_checklist
    import json
    return json.dumps(get_checklist("quick"), indent=2)

@mcp.resource("config://current")
def get_current_config_resource() -> str:
    import json
    return json.dumps(get_config(), indent=2)

def main():
    logger.info("Starting Java Code Review MCP Server...")
    config_path = os.environ.get("JAVA_REVIEW_CONFIG", str(DEFAULT_CONFIG_PATH))
    if os.path.exists(config_path):
        load_config(config_path)
        logger.info(f"Loaded configuration from: {config_path}")
    else:
        logger.warning(f"Config file not found: {config_path}, using defaults")
        load_config()
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
