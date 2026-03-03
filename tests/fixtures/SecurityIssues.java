package com.example;

public class SecurityIssues {
    // Hardcoded credential — should trigger HardcodedCredentials rule
    private String password = "super_secret_123";
    private String api_key = "AKIAIOSFODNN7EXAMPLE";

    // SQL injection risk — should trigger SQLInjection rule
    public void loadUser(String name) {
        // Direct string concatenation in execute call — matches SQL_PATTERNS
        execute("SELECT * FROM users WHERE name = '" + name);
    }

    private void execute(String sql) {}
}
