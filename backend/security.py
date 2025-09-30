# ===== Comprehensive Security Module =====
# Voice RAG System Security Framework
# Advanced security measures, authentication, authorization, and threat detection

import os
import hashlib
import secrets
import hmac
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from functools import wraps
from dataclasses import dataclass
from enum import Enum
import re
import ipaddress
import time
from collections import defaultdict, deque
import threading
import asyncio
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json

logger = logging.getLogger(__name__)

# ===== Security Configuration =====
class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityConfig:
    """Security configuration settings."""

    # Authentication settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    PASSWORD_MIN_LENGTH: int = 8
    REQUIRE_COMPLEX_PASSWORDS: bool = True

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 10

    # Input validation
    MAX_INPUT_LENGTH: int = 10000
    ALLOW_FILE_UPLOADS: bool = True
    ALLOWED_FILE_TYPES: List[str] = None
    MAX_FILE_SIZE_MB: int = 50

    # Security headers
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_CSRF_PROTECTION: bool = True
    ENABLE_XSS_PROTECTION: bool = True

    # Monitoring
    SECURITY_MONITORING_ENABLED: bool = True
    LOG_SECURITY_EVENTS: bool = True
    ALERT_ON_THREATS: bool = True

    # Encryption
    ENABLE_DATA_ENCRYPTION: bool = True
    ENCRYPTION_KEY: Optional[str] = None

    def __post_init__(self):
        if self.ALLOWED_FILE_TYPES is None:
            self.ALLOWED_FILE_TYPES = [
                ".txt", ".pdf", ".docx", ".doc", ".rtf", ".odt",
                ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
                ".mp3", ".wav", ".flac", ".ogg", ".m4a",
                ".csv", ".xlsx", ".xls", ".pptx", ".ppt"
            ]

# Global security configuration
security_config = SecurityConfig()

# ===== Threat Detection =====
class ThreatType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    BRUTE_FORCE = "brute_force"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_FILE_UPLOAD = "suspicious_file_upload"
    MALICIOUS_INPUT = "malicious_input"
    UNAUTHORIZED_ACCESS = "unauthorized_access"

@dataclass
class SecurityThreat:
    """Represents a detected security threat."""

    threat_type: ThreatType
    severity: SecurityLevel
    source_ip: str
    user_agent: str
    timestamp: datetime
    details: Dict[str, Any]
    blocked: bool = False

class ThreatDetector:
    """Advanced threat detection and prevention system."""

    def __init__(self):
        self.threat_patterns = self._load_threat_patterns()
        self.recent_threats = deque(maxlen=1000)
        self.blocked_ips = set()
        self.suspicious_ips = defaultdict(list)
        self.lock = threading.RLock()

    def _load_threat_patterns(self) -> Dict[ThreatType, List[str]]:
        """Load threat detection patterns."""
        return {
            ThreatType.SQL_INJECTION: [
                r"(\bUNION\b.*\bSELECT\b)",
                r"(\bDROP\b.*\bTABLE\b)",
                r"(\bINSERT\b.*\bINTO\b)",
                r"(\bDELETE\b.*\bFROM\b)",
                r"(\bUPDATE\b.*\bSET\b)",
                r"(\'\s*OR\s*\'\d+\'\s*=\s*\'\d+)",
                r"(\'\s*OR\s*\'\w+\'\s*=\s*\'\w+)",
                r"(\-\-|\#|\/\*|\*\/)",
                r"(\bEXEC\b|\bEXECUTE\b)",
                r"(\bSP_\w+)"
            ],
            ThreatType.XSS: [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
                r"vbscript:",
                r"expression\s*\(",
                r"@import",
                r"<link[^>]*stylesheet"
            ],
            ThreatType.COMMAND_INJECTION: [
                r"(\;|\||\&)\s*(ls|dir|cat|type|echo|ping|wget|curl)",
                r"(\$\(|\`|eval\()",
                r"(nc|netcat|telnet)\s+",
                r"(rm\s+\-rf|del\s+\/)",
                r"(\>\s*\/dev\/null|\>\s*nul)",
                r"(chmod|chown|sudo)",
                r"(\|\s*sh|\|\s*bash|\|\s*cmd)"
            ],
            ThreatType.PATH_TRAVERSAL: [
                r"\.\.\/",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e\\",
                r"\/etc\/passwd",
                r"\/windows\/system32",
                r"\.\.%2f",
                r"\.\.%5c"
            ]
        }

    def detect_threats(self, input_data: str, source_ip: str, user_agent: str = "") -> List[SecurityThreat]:
        """Detect security threats in input data."""
        threats = []

        with self.lock:
            for threat_type, patterns in self.threat_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, input_data, re.IGNORECASE):
                        threat = SecurityThreat(
                            threat_type=threat_type,
                            severity=self._get_threat_severity(threat_type),
                            source_ip=source_ip,
                            user_agent=user_agent,
                            timestamp=datetime.now(),
                            details={
                                "pattern_matched": pattern,
                                "input_sample": input_data[:100],
                                "full_input_length": len(input_data)
                            }
                        )
                        threats.append(threat)
                        self.recent_threats.append(threat)

                        # Track suspicious IPs
                        self.suspicious_ips[source_ip].append(threat)

                        logger.warning(f"Security threat detected: {threat_type.value} from {source_ip}")

        return threats

    def _get_threat_severity(self, threat_type: ThreatType) -> SecurityLevel:
        """Get severity level for threat type."""
        severity_map = {
            ThreatType.SQL_INJECTION: SecurityLevel.HIGH,
            ThreatType.XSS: SecurityLevel.HIGH,
            ThreatType.COMMAND_INJECTION: SecurityLevel.CRITICAL,
            ThreatType.PATH_TRAVERSAL: SecurityLevel.HIGH,
            ThreatType.BRUTE_FORCE: SecurityLevel.MEDIUM,
            ThreatType.RATE_LIMIT_EXCEEDED: SecurityLevel.LOW,
            ThreatType.SUSPICIOUS_FILE_UPLOAD: SecurityLevel.MEDIUM,
            ThreatType.MALICIOUS_INPUT: SecurityLevel.MEDIUM,
            ThreatType.UNAUTHORIZED_ACCESS: SecurityLevel.HIGH
        }
        return severity_map.get(threat_type, SecurityLevel.MEDIUM)

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        return ip in self.blocked_ips

    def block_ip(self, ip: str, reason: str = "Security threat detected"):
        """Block an IP address."""
        with self.lock:
            self.blocked_ips.add(ip)
            logger.warning(f"Blocked IP {ip}: {reason}")

    def get_threat_summary(self) -> Dict[str, Any]:
        """Get summary of recent threats."""
        with self.lock:
            threat_counts = defaultdict(int)
            severity_counts = defaultdict(int)

            for threat in self.recent_threats:
                threat_counts[threat.threat_type.value] += 1
                severity_counts[threat.severity.value] += 1

            return {
                "total_threats": len(self.recent_threats),
                "threat_types": dict(threat_counts),
                "severity_levels": dict(severity_counts),
                "blocked_ips": list(self.blocked_ips),
                "suspicious_ip_count": len(self.suspicious_ips)
            }

# Global threat detector
threat_detector = ThreatDetector()

# ===== Rate Limiting =====
class RateLimiter:
    """Advanced rate limiting with burst protection."""

    def __init__(self):
        self.request_history = defaultdict(deque)
        self.burst_history = defaultdict(deque)
        self.lock = threading.RLock()

    def is_rate_limited(self, identifier: str, window_minutes: int = 1, max_requests: int = None) -> bool:
        """Check if identifier is rate limited."""
        if not security_config.RATE_LIMIT_ENABLED:
            return False

        max_requests = max_requests or security_config.RATE_LIMIT_REQUESTS_PER_MINUTE
        window_seconds = window_minutes * 60
        cutoff_time = time.time() - window_seconds

        with self.lock:
            # Clean old requests
            requests = self.request_history[identifier]
            while requests and requests[0] < cutoff_time:
                requests.popleft()

            # Check if rate limited
            if len(requests) >= max_requests:
                # Log rate limit violation
                threat = SecurityThreat(
                    threat_type=ThreatType.RATE_LIMIT_EXCEEDED,
                    severity=SecurityLevel.LOW,
                    source_ip=identifier,
                    user_agent="",
                    timestamp=datetime.now(),
                    details={
                        "requests_in_window": len(requests),
                        "window_minutes": window_minutes,
                        "max_requests": max_requests
                    }
                )
                threat_detector.recent_threats.append(threat)
                return True

            # Record current request
            requests.append(time.time())
            return False

    def check_burst_protection(self, identifier: str, burst_size: int = None) -> bool:
        """Check burst protection (requests in very short time)."""
        burst_size = burst_size or security_config.RATE_LIMIT_BURST_SIZE
        burst_window = 10  # 10 seconds
        cutoff_time = time.time() - burst_window

        with self.lock:
            bursts = self.burst_history[identifier]
            while bursts and bursts[0] < cutoff_time:
                bursts.popleft()

            if len(bursts) >= burst_size:
                return True

            bursts.append(time.time())
            return False

# Global rate limiter
rate_limiter = RateLimiter()

# ===== Input Validation and Sanitization =====
class InputValidator:
    """Comprehensive input validation and sanitization."""

    @staticmethod
    def validate_text_input(text: str, max_length: int = None) -> Tuple[bool, List[str]]:
        """Validate text input for security issues."""
        max_length = max_length or security_config.MAX_INPUT_LENGTH
        errors = []

        # Check length
        if len(text) > max_length:
            errors.append(f"Input exceeds maximum length of {max_length} characters")

        # Check for null bytes
        if '\x00' in text:
            errors.append("Input contains null bytes")

        # Check for control characters (except common ones)
        control_chars = [chr(i) for i in range(32) if i not in [9, 10, 13]]  # Allow tab, LF, CR
        for char in control_chars:
            if char in text:
                errors.append("Input contains invalid control characters")
                break

        return len(errors) == 0, errors

    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input by removing/escaping dangerous content."""
        # Remove null bytes
        text = text.replace('\x00', '')

        # Remove control characters (except tab, LF, CR)
        sanitized = ''
        for char in text:
            if ord(char) >= 32 or char in ['\t', '\n', '\r']:
                sanitized += char

        return sanitized.strip()

    @staticmethod
    def validate_file_upload(filename: str, content: bytes, content_type: str) -> Tuple[bool, List[str]]:
        """Validate file uploads for security."""
        errors = []

        # Check file extension
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext not in security_config.ALLOWED_FILE_TYPES:
            errors.append(f"File type {file_ext} not allowed")

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > security_config.MAX_FILE_SIZE_MB:
            errors.append(f"File size {size_mb:.1f}MB exceeds limit of {security_config.MAX_FILE_SIZE_MB}MB")

        # Check for embedded executables in common file types
        if file_ext in ['.pdf', '.docx', '.xlsx', '.pptx']:
            if b'application/x-msdownload' in content[:1024]:
                errors.append("File contains embedded executable content")

        # Check for script content in text files
        if file_ext in ['.txt', '.csv']:
            content_str = content[:1024].decode('utf-8', errors='ignore').lower()
            dangerous_patterns = ['<script', 'javascript:', 'vbscript:', 'on\w+\s*=']
            for pattern in dangerous_patterns:
                if re.search(pattern, content_str):
                    errors.append("File contains potentially malicious script content")
                    break

        return len(errors) == 0, errors

# ===== Authentication and Authorization =====
class SecurityManager:
    """Central security management system."""

    def __init__(self):
        self.active_sessions = {}
        self.failed_logins = defaultdict(list)
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key) if security_config.ENABLE_DATA_ENCRYPTION else None

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key."""
        if security_config.ENCRYPTION_KEY:
            return security_config.ENCRYPTION_KEY.encode()

        # Generate key from environment or create new one
        password = os.getenv("ENCRYPTION_PASSWORD", "default-password").encode()
        salt = os.getenv("ENCRYPTION_SALT", "default-salt").encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def generate_api_key(self, user_id: str, permissions: List[str] = None) -> str:
        """Generate secure API key for user."""
        payload = {
            "user_id": user_id,
            "permissions": permissions or ["read"],
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=security_config.JWT_EXPIRATION_HOURS)).isoformat()
        }

        token = jwt.encode(payload, security_config.JWT_SECRET_KEY, algorithm=security_config.JWT_ALGORITHM)
        return token

    def validate_api_key(self, token: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate API key and return user info."""
        try:
            payload = jwt.decode(token, security_config.JWT_SECRET_KEY, algorithms=[security_config.JWT_ALGORITHM])

            # Check expiration
            expires_at = datetime.fromisoformat(payload["expires_at"])
            if datetime.utcnow() > expires_at:
                return False, {"error": "Token expired"}

            return True, payload

        except jwt.InvalidTokenError as e:
            return False, {"error": f"Invalid token: {str(e)}"}

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self.fernet:
            return data

        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self.fernet:
            return encrypted_data

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data

    def record_failed_login(self, identifier: str, ip: str):
        """Record failed login attempt."""
        self.failed_logins[identifier].append({
            "timestamp": datetime.now(),
            "ip": ip
        })

        # Check for brute force attacks
        recent_failures = [
            attempt for attempt in self.failed_logins[identifier]
            if datetime.now() - attempt["timestamp"] < timedelta(minutes=15)
        ]

        if len(recent_failures) >= 5:
            threat = SecurityThreat(
                threat_type=ThreatType.BRUTE_FORCE,
                severity=SecurityLevel.MEDIUM,
                source_ip=ip,
                user_agent="",
                timestamp=datetime.now(),
                details={
                    "identifier": identifier,
                    "failed_attempts": len(recent_failures)
                }
            )
            threat_detector.recent_threats.append(threat)
            threat_detector.block_ip(ip, "Brute force attack detected")

# Global security manager
security_manager = SecurityManager()

# ===== Security Decorators =====
def require_authentication(f):
    """Decorator to require authentication."""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # Implementation would depend on your authentication system
        # This is a placeholder for the authentication check
        return await f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests: int = None, window_minutes: int = 1):
    """Decorator for rate limiting."""
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # Extract IP from request (implementation specific)
            ip = "127.0.0.1"  # Placeholder

            if rate_limiter.is_rate_limited(ip, window_minutes, max_requests):
                raise Exception("Rate limit exceeded")

            return await f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(max_length: int = None):
    """Decorator for input validation."""
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            # Validate all string arguments
            for arg in args:
                if isinstance(arg, str):
                    valid, errors = InputValidator.validate_text_input(arg, max_length)
                    if not valid:
                        raise Exception(f"Input validation failed: {errors}")

            return await f(*args, **kwargs)
        return decorated_function
    return decorator

# ===== Security Monitoring =====
class SecurityMonitor:
    """Real-time security monitoring and alerting."""

    def __init__(self):
        self.alert_handlers = []
        self.metrics = defaultdict(int)

    def add_alert_handler(self, handler):
        """Add alert handler function."""
        self.alert_handlers.append(handler)

    def trigger_alert(self, threat: SecurityThreat):
        """Trigger security alert."""
        if not security_config.ALERT_ON_THREATS:
            return

        alert_data = {
            "threat_type": threat.threat_type.value,
            "severity": threat.severity.value,
            "source_ip": threat.source_ip,
            "timestamp": threat.timestamp.isoformat(),
            "details": threat.details
        }

        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    def get_security_dashboard(self) -> Dict[str, Any]:
        """Get security dashboard data."""
        threat_summary = threat_detector.get_threat_summary()

        return {
            "threat_summary": threat_summary,
            "blocked_ips": list(threat_detector.blocked_ips),
            "recent_threats": [
                {
                    "type": threat.threat_type.value,
                    "severity": threat.severity.value,
                    "source_ip": threat.source_ip,
                    "timestamp": threat.timestamp.isoformat()
                }
                for threat in list(threat_detector.recent_threats)[-10:]
            ],
            "security_config": {
                "rate_limiting": security_config.RATE_LIMIT_ENABLED,
                "threat_detection": security_config.SECURITY_MONITORING_ENABLED,
                "encryption": security_config.ENABLE_DATA_ENCRYPTION,
                "file_uploads": security_config.ALLOW_FILE_UPLOADS
            }
        }

# Global security monitor
security_monitor = SecurityMonitor()

# ===== Security Utilities =====
def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure random token."""
    return secrets.token_urlsafe(length)

def hash_password(password: str) -> str:
    """Hash password securely."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
    """Validate password strength."""
    errors = []

    if len(password) < security_config.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {security_config.PASSWORD_MIN_LENGTH} characters")

    if security_config.REQUIRE_COMPLEX_PASSWORDS:
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors

def get_client_ip(request) -> str:
    """Extract client IP from request headers."""
    # Check for forwarded IP headers
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()

    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip

    return request.client.host if hasattr(request, 'client') else '127.0.0.1'

async def security_check_input(input_data: str, source_ip: str, user_agent: str = "") -> bool:
    """Perform comprehensive security check on input."""
    # Validate input
    valid, errors = InputValidator.validate_text_input(input_data)
    if not valid:
        logger.warning(f"Input validation failed from {source_ip}: {errors}")
        return False

    # Check for threats
    threats = threat_detector.detect_threats(input_data, source_ip, user_agent)
    if threats:
        for threat in threats:
            security_monitor.trigger_alert(threat)
            if threat.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                threat_detector.block_ip(source_ip, f"Security threat: {threat.threat_type.value}")
                return False

    return True

# Initialize security system
def initialize_security_system():
    """Initialize the security system."""
    logger.info("Initializing Voice RAG security system...")

    try:
        # Setup security monitoring
        if security_config.SECURITY_MONITORING_ENABLED:
            logger.info("Security monitoring enabled")

        # Setup encryption
        if security_config.ENABLE_DATA_ENCRYPTION:
            logger.info("Data encryption enabled")

        # Setup rate limiting
        if security_config.RATE_LIMIT_ENABLED:
            logger.info(f"Rate limiting enabled: {security_config.RATE_LIMIT_REQUESTS_PER_MINUTE} req/min")

        logger.info("Security system initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize security system: {e}")
        raise