"""Checklist Module - Code review checklists"""

def get_checklist(checklist_type: str = 'full') -> dict:
    """Get code review checklist."""
    if checklist_type == 'quick':
        return get_quick_checklist()
    return get_full_checklist()

def get_full_checklist() -> dict:
    """Get comprehensive code review checklist."""
    return {
        'Functionality & Logic': [
            'Code correctly implements requirements',
            'Edge cases and boundary conditions handled',
            'Input validation present',
            'No functional regressions',
            'Error handling implemented'
        ],
        'Object-Oriented Design (SOLID)': [
            'Single Responsibility Principle followed',
            'Open/Closed Principle applied',
            'Liskov Substitution Principle respected',
            'Interface Segregation used',
            'Dependency Inversion followed',
            'Composition over inheritance preferred'
        ],
        'JDK 17+ Modern Features': [
            'Records used for immutable DTOs',
            'Sealed classes for controlled inheritance',
            'Pattern matching (instanceof) used',
            'Switch expressions used (not fall-through)',
            'Text blocks for multiline strings',
            'Var for local type inference',
            'Stream API used appropriately'
        ],
        'Resource Management': [
            'Try-with-resources for AutoCloseable',
            'No manual close() in finally blocks',
            'Database connections in try-with-resources',
            'Thread pools properly shut down',
            'No suppressed exceptions'
        ],
        'Thread Safety & Concurrency': [
            'Synchronized blocks used correctly',
            'Volatile for simple flags only',
            'ConcurrentHashMap instead of Hashtable',
            'Immutable objects for shared state',
            'No partially constructed objects published'
        ],
        'Null Safety': [
            'Optional for return values (not parameters)',
            'Optional.of() only for known non-null',
            'Optional.orElseThrow() over get()',
            'Null checks before dereferencing',
            'Empty collections instead of null'
        ],
        'Exception Handling': [
            'No empty catch blocks',
            'Specific exception types used',
            'Meaningful error messages',
            'Custom exceptions when appropriate',
            '@throws documented in Javadoc'
        ],
        'Performance': [
            'No unnecessary object creation in loops',
            'StringBuilder for concatenation in loops',
            'Pre-sized collections when size known',
            'Lazy initialization when appropriate',
            'Efficient data structures used'
        ],
        'Security': [
            'No hardcoded credentials/API keys',
            'Input sanitization (SQL injection prevention)',
            'Proper authentication/authorization checks',
            'Sensitive data handling',
            'No logging of sensitive information'
        ],
        'Code Style & Readability': [
            'Java naming conventions followed',
            'Meaningful variable/method names',
            'Consistent formatting and indentation',
            'No magic numbers',
            'Logging instead of System.out/err'
        ],
        'Testing': [
            'Unit test coverage',
            'Edge cases tested',
            'Mock external dependencies',
            'Meaningful test names'
        ]
    }

def get_quick_checklist() -> dict:
    """Get quick code review checklist."""
    return {
        'Core Checks': [
            'Code compiles without errors',
            'Logic correctly implements requirements',
            'No security issues (credentials, injection)',
            'Proper exception handling',
            'Code follows naming conventions'
        ],
        'Java 17+ Quick Checks': [
            'Consider records for DTOs',
            'Consider switch expressions',
            'Consider var for type inference'
        ],
        'Performance Quick Checks': [
            'No obvious performance issues',
            'Resources properly managed'
        ]
    }
