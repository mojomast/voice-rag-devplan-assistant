"""
Real API Test Framework for Voice-RAG-System

This framework provides real API testing capabilities with proper security,
cost controls, and error handling for external API dependencies.
"""

from .core import RealAPITestFramework, APITestConfig
from .security import APIKeyManager, SecureCredentialsStore
from .monitors import CostMonitor, UsageTracker, RateLimitMonitor
from .fixtures import RealAPIFixtureProvider
from .utils import TestDataGenerator, APIResponseValidator

__version__ = "1.0.0"
__all__ = [
    "RealAPITestFramework",
    "APITestConfig", 
    "APIKeyManager",
    "SecureCredentialsStore",
    "CostMonitor",
    "UsageTracker", 
    "RateLimitMonitor",
    "RealAPIFixtureProvider",
    "TestDataGenerator",
    "APIResponseValidator",
]