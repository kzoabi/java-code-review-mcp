"""Configuration Loader Module"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_CONFIG = {
    'max_line_length': 120,
    'indent_size': 4,
    'use_spaces': True,
    'max_method_length': 30,
    'max_class_length': 500,
    'max_parameters': 5,
    'jdk17_features': {
        'recommend_records': True,
        'recommend_sealed_classes': True,
        'recommend_switch_expressions': True,
        'recommend_text_blocks': True,
        'recommend_var_keyword': True,
        'recommend_pattern_matching': True
    },
    'jdk21_features': {
        'recommend_virtual_threads': True,
        'recommend_structured_concurrency': True,
        'recommend_string_templates': True,
    },
    'spring_enabled': False,
    'spring_rules': {
        'transactional': True,
        'field_injection': True,
        'missing_stereotype': True,
        'rest_return_types': True,
        'value_fallback': True,
        'circular_autowired': True,
    },
    'security': {
        'check_hardcoded_secrets': True,
        'check_sql_injection': True,
        'check_logging_sensitive': True
    },
    'rule_severity': {
        'critical': ['security', 'hardcoded-credentials'],
        'major': ['empty-catch-block', 'magic-numbers'],
        'minor': ['line-length', 'import-order']
    },
    'jbct_profile': 'basic',
    'jbct_rules': {
        'return_types': True,
        'exceptions': True,
        'value_objects': True,
        'lambda_rules': True,
        'patterns': True,
        'architecture': True,
        'naming': True,
        'zones': True,
        'style': True,
        'logging': True,
        'static_imports': True,
        'utilities': True,
        'sealed_types': True,
        'usecase': True
    },
    'jbct_packages': {
        'domain_patterns': ['**.domain.**', '**.usecase.**'],
        'adapter_patterns': ['**.adapter.**', '**.io.**']
    },
    'zone2_verbs': ['validate', 'process', 'handle', 'execute', 'perform', 'transform'],
    'zone3_verbs': ['get', 'fetch', 'load', 'parse', 'convert', 'find', 'query']
}

_current_config = DEFAULT_CONFIG.copy()

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file."""
    global _current_config
    if config_path is None:
        default_path = Path(__file__).parent.parent / "config" / "code_review_config.md"
        if default_path.exists():
            config_path = str(default_path)
        else:
            _current_config = DEFAULT_CONFIG.copy()
            return _current_config
    if config_path and os.path.exists(config_path):
        ext = os.path.splitext(config_path)[1].lower()
        if ext in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    _current_config = merge_config(DEFAULT_CONFIG, loaded)
        elif ext == '.md':
            _current_config = load_config_from_md(config_path)
    return _current_config

def load_config_from_md(md_path: str) -> Dict[str, Any]:
    """Load configuration from markdown file."""
    config = DEFAULT_CONFIG.copy()
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    current_section = None
    section_content = {}
    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            continue
        if line.startswith('## '):
            if current_section and section_content:
                config = apply_section_config(config, current_section, section_content)
            current_section = line[3:].strip()
            section_content = {}
        elif ':' in line and not line.startswith('-'):
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            section_content[key] = value
    if current_section and section_content:
        config = apply_section_config(config, current_section, section_content)
    return config

def apply_section_config(config: Dict, section: str, section_content: Dict) -> Dict:
    """Apply configuration from a section."""
    section_lower = section.lower()
    if 'coding style' in section_lower:
        config.update(section_content)
    elif 'threshold' in section_lower or 'thresholds' in section_lower:
        config.update(section_content)
    elif 'jdk' in section_lower or '17' in section_lower:
        if 'jdk17_features' not in config:
            config['jdk17_features'] = {}
        config['jdk17_features'].update(section_content)
    elif 'security' in section_lower:
        if 'security' not in config:
            config['security'] = {}
        config['security'].update(section_content)
    elif 'jbct' in section_lower:
        if 'jbct_profile' in section_content:
            config['jbct_profile'] = section_content['jbct_profile']
        if 'jbct_rules' in section_content:
            config['jbct_rules'] = section_content['jbct_rules']
        if 'jbct_packages' in section_content:
            config['jbct_packages'] = section_content['jbct_packages']
    elif 'zone2' in section_lower:
        if 'zone2_verbs' not in config:
            config['zone2_verbs'] = []
        config['zone2_verbs'] = section_content.get('zone2_verbs', config.get('zone2_verbs', []))
    elif 'zone3' in section_lower:
        if 'zone3_verbs' not in config:
            config['zone3_verbs'] = []
        config['zone3_verbs'] = section_content.get('zone3_verbs', config.get('zone3_verbs', []))
    return config

def merge_config(default: Dict, loaded: Dict) -> Dict:
    """Deep merge loaded config into default."""
    result = default.copy()
    for key, value in loaded.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result

def get_config() -> Dict[str, Any]:
    """Get the current configuration."""
    return _current_config
