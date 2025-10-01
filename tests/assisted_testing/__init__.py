"""
Assisted Testing Framework for Voice-RAG-System

Provides interactive testing scripts for components that cannot be fully automated,
such as voice input/output testing, user interaction testing, and manual validation.
"""

from .core import AssistedTestFramework, TestScenario, TestStep
from .voice_tester import VoiceInteractionTester
from .ui_tester import UserInterfaceTester
from .workflow_tester import WorkflowTester
from .validators import ValidationResult, TestValidator

__version__ = "1.0.0"
__all__ = [
    "AssistedTestFramework",
    "TestScenario", 
    "TestStep",
    "VoiceInteractionTester",
    "UserInterfaceTester",
    "WorkflowTester",
    "ValidationResult",
    "TestValidator",
]