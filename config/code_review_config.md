# Java Code Review Configuration

## Coding Style
max_line_length: 120
indent_size: 4
use_spaces: true

## Thresholds
max_method_length: 30
max_class_length: 500
max_parameters: 5

## JDK 17+ Features (Migration Mode)
recommend_records: true
recommend_sealed_classes: true
recommend_switch_expressions: true
recommend_text_blocks: true
recommend_var_keyword: true
recommend_pattern_matching: true

## Security
check_hardcoded_secrets: true
check_sql_injection: true
check_logging_sensitive: true

## Rules Severity
rule_severity:
  critical:
    - security
    - hardcoded-credentials
  major:
    - empty-catch-block
    - magic-numbers
  minor:
    - line-length
    - import-order

## JBCT Profile (Java Backend Coding Technology)
# Profile levels: disabled | basic | full
# - disabled: No JBCT-specific checks
# - basic: Core return type and exception rules (12 rules)
# - full: All 37 JBCT rules (see CLI-TOOLING.md)
jbct_profile: basic

# JBCT Rule Categories (enabled when jbct_profile is not disabled)
jbct_rules:
  # Return Types (JBCT-RET-01 to RET-05)
  return_types: true
  
  # Exceptions (JBCT-EX-01, EX-02)
  exceptions: true
  
  # Value Objects (JBCT-VO-01, VO-02)
  value_objects: true
  
  # Lambda Rules (JBCT-LAM-01, LAM-02, LAM-03, NEST-01)
  lambda_rules: true
  
  # Patterns (JBCT-PAT-01, PAT-02, SEQ-01)
  patterns: true
  
  # Architecture (JBCT-MIX-01)
  architecture: true
  
  # Naming (JBCT-NAM-01, NAM-02, ACR-01)
  naming: true
  
  # Zones (JBCT-ZONE-01, ZONE-02, ZONE-03)
  zones: true
  
  # Style Rules (JBCT-STY-01 to STY-06)
  style: true
  
  # Logging Rules (JBCT-LOG-01, LOG-02)
  logging: true
  
  # Static Import Rules (JBCT-STATIC-01)
  static_imports: true
  
  # Utility Rules (JBCT-UTIL-01, UTIL-02)
  utilities: true
  
  # Sealed Type Rules (JBCT-SEAL-01)
  sealed_types: true
  
  # Use Case Rules (JBCT-UC-01)
  usecase: true

# Package patterns for architecture rules
# Adjust these to match your project structure
jbct_packages:
  domain_patterns:
    - "**.domain.**"
    - "**.usecase.**"
  adapter_patterns:
    - "**.adapter.**"
    - "**.io.**"

# Step interface verbs (for Zone rules)
zone2_verbs:
  - validate
  - process
  - handle
  - execute
  - perform
  - transform

zone3_verbs:
  - get
  - fetch
  - load
  - parse
  - convert
  - find
  - query
