"""Predefined prompt templates for common planning scenarios."""

from __future__ import annotations

from typing import Dict, List

# Predefined prompt templates for development planning
PROMPT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "new_feature": {
        "title": "New Feature Development",
        "prompt": """I want to plan a new feature for my project. Here are the details:

Feature Name: [Feature name]
Description: [Brief description]
User Story: [As a... I want to... so that...]
Acceptance Criteria: [List criteria]

Please help me create a comprehensive development plan including:
- Technical design considerations
- Implementation phases
- Testing strategy
- Deployment approach""",
        "category": "Development",
    },
    "bug_fix": {
        "title": "Bug Fix & Debugging",
        "prompt": """I need to fix a bug in my project:

Bug Description: [What's wrong?]
Steps to Reproduce: [How to trigger the bug]
Expected Behavior: [What should happen]
Actual Behavior: [What's happening]
Impact: [Critical/High/Medium/Low]

Please help me create a plan to:
- Investigate and identify root cause
- Implement the fix
- Prevent similar issues
- Add regression tests""",
        "category": "Maintenance",
    },
    "refactoring": {
        "title": "Code Refactoring",
        "prompt": """I want to refactor part of my codebase:

Component to Refactor: [Name/path]
Current Issues: [What's wrong with current implementation]
Goals: [What should the refactored code achieve]

Please help me plan:
- Refactoring approach and strategy
- Backward compatibility considerations
- Testing to ensure no regressions
- Rollout plan""",
        "category": "Development",
    },
    "api_integration": {
        "title": "API Integration",
        "prompt": """I need to integrate a new API:

API Name: [API name]
Purpose: [Why we need this integration]
Documentation: [Link to API docs]
Expected Usage: [How it will be used]

Please help me plan:
- Integration architecture
- Authentication and security
- Error handling and retries
- Testing strategy
- Rate limiting considerations""",
        "category": "Integration",
    },
    "database_migration": {
        "title": "Database Migration",
        "prompt": """I need to plan a database migration:

Current State: [Current database structure]
Target State: [Desired database structure]
Data Volume: [Approximate size]
Downtime Tolerance: [Acceptable downtime]

Please help me plan:
- Migration strategy (online/offline)
- Data transformation approach
- Rollback plan
- Testing and validation
- Performance considerations""",
        "category": "Infrastructure",
    },
    "performance_optimization": {
        "title": "Performance Optimization",
        "prompt": """I need to optimize performance:

Component: [What needs optimization]
Current Performance: [Metrics]
Target Performance: [Goals]
Constraints: [Budget, time, resources]

Please help me plan:
- Performance analysis approach
- Optimization strategies
- Benchmarking methodology
- Implementation priorities
- Validation criteria""",
        "category": "Optimization",
    },
    "security_enhancement": {
        "title": "Security Enhancement",
        "prompt": """I want to improve security:

Area of Concern: [What needs securing]
Current Security Measures: [What's in place]
Compliance Requirements: [Any regulatory requirements]
Threat Model: [Expected threats]

Please help me plan:
- Security assessment
- Implementation of security controls
- Security testing approach
- Documentation and training
- Incident response preparation""",
        "category": "Security",
    },
    "testing_strategy": {
        "title": "Testing Strategy",
        "prompt": """I need to develop a testing strategy:

Project Type: [Web app, API, etc.]
Current Test Coverage: [%]
Target Coverage: [%]
Testing Goals: [What needs testing]

Please help me plan:
- Test pyramid strategy (unit, integration, E2E)
- Test automation approach
- CI/CD integration
- Performance and load testing
- Test data management""",
        "category": "Testing",
    },
    "documentation": {
        "title": "Documentation Project",
        "prompt": """I need to create/update documentation:

Documentation Type: [User docs, API docs, internal docs]
Audience: [Who will read this]
Scope: [What needs documenting]
Current State: [What exists]

Please help me plan:
- Documentation structure
- Content creation approach
- Review and approval process
- Publishing and distribution
- Maintenance strategy""",
        "category": "Documentation",
    },
}


def get_template(template_id: str) -> Dict[str, str]:
    """Get a specific prompt template by ID."""
    return PROMPT_TEMPLATES.get(template_id, {})


def get_all_templates() -> Dict[str, Dict[str, str]]:
    """Get all available prompt templates."""
    return PROMPT_TEMPLATES


def get_templates_by_category(category: str) -> Dict[str, Dict[str, str]]:
    """Get all templates for a specific category."""
    return {
        template_id: template
        for template_id, template in PROMPT_TEMPLATES.items()
        if template.get("category") == category
    }


def get_categories() -> List[str]:
    """Get all unique template categories."""
    return sorted(set(template.get("category", "Other") for template in PROMPT_TEMPLATES.values()))
