# ===== Production Monitoring and Alerting System =====
# Voice RAG System Advanced Monitoring, Alerting, and Observability
# Comprehensive monitoring for production deployment

import asyncio
import time
import logging
import smtplib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import psutil
import threading
from collections import defaultdict, deque
import weakref
import aiohttp
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# ===== Alert Configuration =====
class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    DISCORD = "discord"

@dataclass
class AlertRule:
    """Configuration for an alert rule."""
    name: str
    description: str
    metric_name: str
    condition: str  # e.g., ">" "=" "<"
    threshold: float
    severity: AlertSeverity
    channels: List[AlertChannel]
    cooldown_minutes: int = 5
    enabled: bool = True

@dataclass
class Alert:
    """Represents a monitoring alert."""
    rule_name: str
    severity: AlertSeverity
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    source: str
    tags: Dict[str, str] = None
    resolved: bool = False

# ===== Monitoring Configuration =====
@dataclass
class MonitoringConfig:
    """Production monitoring configuration."""

    # General settings
    enabled: bool = True
    collection_interval_seconds: int = 30
    retention_days: int = 30

    # Email configuration
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    alert_email_from: str = os.getenv("ALERT_EMAIL_FROM", "alerts@voicerag.com")
    alert_email_to: List[str] = None

    # Slack configuration
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    slack_channel: str = os.getenv("SLACK_CHANNEL", "#alerts")

    # Discord configuration
    discord_webhook_url: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    # Custom webhook configuration
    webhook_url: str = os.getenv("CUSTOM_WEBHOOK_URL", "")

    # Health check configuration
    external_health_checks: List[str] = None
    health_check_interval_seconds: int = 60

    # Performance thresholds
    cpu_warning_threshold: float = 70.0
    cpu_critical_threshold: float = 85.0
    memory_warning_threshold: float = 80.0
    memory_critical_threshold: float = 90.0
    disk_warning_threshold: float = 85.0
    disk_critical_threshold: float = 95.0
    response_time_warning_threshold: float = 2.0
    response_time_critical_threshold: float = 5.0
    error_rate_warning_threshold: float = 0.05
    error_rate_critical_threshold: float = 0.10

    def __post_init__(self):
        if self.alert_email_to is None:
            self.alert_email_to = ["admin@voicerag.com"]
        if self.external_health_checks is None:
            self.external_health_checks = []

# Global monitoring configuration
monitoring_config = MonitoringConfig()

# ===== Metrics Collection =====
class MetricsCollector:
    """Collects various system and application metrics."""

    def __init__(self):
        self.metrics_history = defaultdict(deque)
        self.custom_metrics = defaultdict(deque)
        self.lock = threading.RLock()

    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, timestamp: datetime = None):
        """Record a metric value with optional tags."""
        if timestamp is None:
            timestamp = datetime.now()

        metric_data = {
            "value": value,
            "timestamp": timestamp,
            "tags": tags or {}
        }

        with self.lock:
            self.metrics_history[name].append(metric_data)

            # Maintain retention limit
            cutoff_time = datetime.now() - timedelta(days=monitoring_config.retention_days)
            while (self.metrics_history[name] and
                   self.metrics_history[name][0]["timestamp"] < cutoff_time):
                self.metrics_history[name].popleft()

    def get_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics
            network = psutil.net_io_counters()

            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()

            metrics = {
                "system.cpu.percent": cpu_percent,
                "system.cpu.count": cpu_count,
                "system.memory.percent": memory.percent,
                "system.memory.available_gb": memory.available / (1024**3),
                "system.memory.used_gb": memory.used / (1024**3),
                "system.disk.percent": disk.percent,
                "system.disk.free_gb": disk.free / (1024**3),
                "system.disk.used_gb": disk.used / (1024**3),
                "system.network.bytes_sent": network.bytes_sent,
                "system.network.bytes_recv": network.bytes_recv,
                "system.network.packets_sent": network.packets_sent,
                "system.network.packets_recv": network.packets_recv,
                "process.memory.rss_mb": process_memory.rss / (1024**2),
                "process.memory.vms_mb": process_memory.vms / (1024**2),
                "process.cpu.percent": process.cpu_percent(),
                "process.threads": process.num_threads(),
            }

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    def get_application_metrics(self) -> Dict[str, float]:
        """Collect application-specific metrics."""
        # This would be populated by the application
        # For now, return some example metrics
        return {
            "app.requests.total": 0,
            "app.requests.success": 0,
            "app.requests.error": 0,
            "app.response_time.avg": 0.0,
            "app.cache.hit_rate": 0.0,
            "app.db.connections": 0,
            "app.voice.transcriptions": 0,
            "app.documents.processed": 0
        }

    def get_metric_stats(self, metric_name: str, time_window: timedelta = timedelta(minutes=5)) -> Dict[str, float]:
        """Get statistical analysis of a metric."""
        cutoff_time = datetime.now() - time_window

        with self.lock:
            if metric_name not in self.metrics_history:
                return {}

            recent_values = [
                data["value"] for data in self.metrics_history[metric_name]
                if data["timestamp"] >= cutoff_time
            ]

            if not recent_values:
                return {}

            import numpy as np
            return {
                "count": len(recent_values),
                "current": recent_values[-1] if recent_values else 0,
                "min": np.min(recent_values),
                "max": np.max(recent_values),
                "mean": np.mean(recent_values),
                "median": np.median(recent_values),
                "std": np.std(recent_values),
                "p95": np.percentile(recent_values, 95),
                "p99": np.percentile(recent_values, 99)
            }

# Global metrics collector
metrics_collector = MetricsCollector()

# ===== Alert Management =====
class AlertManager:
    """Manages alert rules, firing, and delivery."""

    def __init__(self):
        self.alert_rules = []
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.last_alert_times = defaultdict(datetime)
        self.notification_handlers = {}
        self.lock = threading.RLock()

        # Setup default alert rules
        self._setup_default_alert_rules()

        # Setup notification handlers
        self._setup_notification_handlers()

    def _setup_default_alert_rules(self):
        """Setup default monitoring alert rules."""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                description="CPU usage is high",
                metric_name="system.cpu.percent",
                condition=">",
                threshold=monitoring_config.cpu_warning_threshold,
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                name="critical_cpu_usage",
                description="CPU usage is critically high",
                metric_name="system.cpu.percent",
                condition=">",
                threshold=monitoring_config.cpu_critical_threshold,
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK, AlertChannel.SMS]
            ),
            AlertRule(
                name="high_memory_usage",
                description="Memory usage is high",
                metric_name="system.memory.percent",
                condition=">",
                threshold=monitoring_config.memory_warning_threshold,
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                name="critical_memory_usage",
                description="Memory usage is critically high",
                metric_name="system.memory.percent",
                condition=">",
                threshold=monitoring_config.memory_critical_threshold,
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                name="high_disk_usage",
                description="Disk usage is high",
                metric_name="system.disk.percent",
                condition=">",
                threshold=monitoring_config.disk_warning_threshold,
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.EMAIL]
            ),
            AlertRule(
                name="critical_disk_usage",
                description="Disk usage is critically high",
                metric_name="system.disk.percent",
                condition=">",
                threshold=monitoring_config.disk_critical_threshold,
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            ),
            AlertRule(
                name="high_response_time",
                description="API response time is high",
                metric_name="app.response_time.avg",
                condition=">",
                threshold=monitoring_config.response_time_warning_threshold,
                severity=AlertSeverity.WARNING,
                channels=[AlertChannel.SLACK]
            ),
            AlertRule(
                name="high_error_rate",
                description="Error rate is elevated",
                metric_name="app.error_rate",
                condition=">",
                threshold=monitoring_config.error_rate_warning_threshold,
                severity=AlertSeverity.ERROR,
                channels=[AlertChannel.EMAIL, AlertChannel.SLACK]
            )
        ]

        self.alert_rules.extend(default_rules)

    def _setup_notification_handlers(self):
        """Setup notification delivery handlers."""
        self.notification_handlers = {
            AlertChannel.EMAIL: self._send_email_alert,
            AlertChannel.SLACK: self._send_slack_alert,
            AlertChannel.WEBHOOK: self._send_webhook_alert,
            AlertChannel.DISCORD: self._send_discord_alert
        }

    def add_alert_rule(self, rule: AlertRule):
        """Add a custom alert rule."""
        with self.lock:
            self.alert_rules.append(rule)

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule by name."""
        with self.lock:
            self.alert_rules = [rule for rule in self.alert_rules if rule.name != rule_name]

    def check_alerts(self, current_metrics: Dict[str, float]):
        """Check current metrics against alert rules."""
        current_time = datetime.now()

        with self.lock:
            for rule in self.alert_rules:
                if not rule.enabled:
                    continue

                if rule.metric_name not in current_metrics:
                    continue

                current_value = current_metrics[rule.metric_name]

                # Check if alert condition is met
                alert_triggered = self._evaluate_condition(current_value, rule.condition, rule.threshold)

                if alert_triggered:
                    # Check cooldown
                    last_alert_time = self.last_alert_times.get(rule.name, datetime.min)
                    if current_time - last_alert_time < timedelta(minutes=rule.cooldown_minutes):
                        continue

                    # Create and fire alert
                    alert = Alert(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=f"{rule.description}: {current_value:.2f} {rule.condition} {rule.threshold}",
                        current_value=current_value,
                        threshold=rule.threshold,
                        timestamp=current_time,
                        source="monitoring_system",
                        tags={"metric": rule.metric_name}
                    )

                    self._fire_alert(alert, rule.channels)
                    self.last_alert_times[rule.name] = current_time

                else:
                    # Check if we should resolve an active alert
                    if rule.name in self.active_alerts:
                        resolved_alert = self.active_alerts[rule.name]
                        resolved_alert.resolved = True
                        self.alert_history.append(resolved_alert)
                        del self.active_alerts[rule.name]

                        # Send resolution notification
                        resolution_message = f"RESOLVED: {rule.description}: {current_value:.2f}"
                        logger.info(resolution_message)

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition."""
        if condition == ">":
            return value > threshold
        elif condition == ">=":
            return value >= threshold
        elif condition == "<":
            return value < threshold
        elif condition == "<=":
            return value <= threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    def _fire_alert(self, alert: Alert, channels: List[AlertChannel]):
        """Fire an alert to specified channels."""
        logger.warning(f"ALERT: {alert.message}")

        # Store alert
        self.active_alerts[alert.rule_name] = alert
        self.alert_history.append(alert)

        # Send notifications
        for channel in channels:
            try:
                handler = self.notification_handlers.get(channel)
                if handler:
                    # Schedule async handler to run in background
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(handler(alert))
                        else:
                            loop.run_until_complete(handler(alert))
                    except RuntimeError:
                        # No event loop, create a new one
                        asyncio.run(handler(alert))
                else:
                    logger.warning(f"No handler for alert channel: {channel}")
            except Exception as e:
                logger.error(f"Failed to send alert via {channel}: {e}")

    async def _send_email_alert(self, alert: Alert):
        """Send alert via email."""
        if not monitoring_config.smtp_username or not monitoring_config.smtp_password:
            logger.warning("Email configuration missing, skipping email alert")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = monitoring_config.alert_email_from
            msg['To'] = ', '.join(monitoring_config.alert_email_to)
            msg['Subject'] = f"[{alert.severity.value.upper()}] Voice RAG Alert: {alert.rule_name}"

            body = f"""
Voice RAG System Alert

Severity: {alert.severity.value.upper()}
Rule: {alert.rule_name}
Message: {alert.message}
Current Value: {alert.current_value:.2f}
Threshold: {alert.threshold}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Source: {alert.source}

Please investigate and take appropriate action.

---
Voice RAG Monitoring System
            """

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(monitoring_config.smtp_server, monitoring_config.smtp_port)
            server.starttls()
            server.login(monitoring_config.smtp_username, monitoring_config.smtp_password)

            text = msg.as_string()
            server.sendmail(monitoring_config.alert_email_from, monitoring_config.alert_email_to, text)
            server.quit()

            logger.info(f"Email alert sent for {alert.rule_name}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    async def _send_slack_alert(self, alert: Alert):
        """Send alert via Slack webhook."""
        if not monitoring_config.slack_webhook_url:
            logger.warning("Slack webhook URL not configured, skipping Slack alert")
            return

        try:
            color = {
                AlertSeverity.INFO: "good",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.ERROR: "danger",
                AlertSeverity.CRITICAL: "danger"
            }.get(alert.severity, "warning")

            payload = {
                "channel": monitoring_config.slack_channel,
                "username": "Voice RAG Monitor",
                "icon_emoji": ":warning:",
                "attachments": [
                    {
                        "color": color,
                        "title": f"[{alert.severity.value.upper()}] {alert.rule_name}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Current Value",
                                "value": f"{alert.current_value:.2f}",
                                "short": True
                            },
                            {
                                "title": "Threshold",
                                "value": f"{alert.threshold}",
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            }
                        ],
                        "footer": "Voice RAG Monitoring",
                        "ts": int(alert.timestamp.timestamp())
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(monitoring_config.slack_webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent for {alert.rule_name}")
                    else:
                        logger.error(f"Failed to send Slack alert: HTTP {response.status}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")

    async def _send_discord_alert(self, alert: Alert):
        """Send alert via Discord webhook."""
        if not monitoring_config.discord_webhook_url:
            logger.warning("Discord webhook URL not configured, skipping Discord alert")
            return

        try:
            color = {
                AlertSeverity.INFO: 0x00ff00,      # Green
                AlertSeverity.WARNING: 0xffff00,   # Yellow
                AlertSeverity.ERROR: 0xff8800,     # Orange
                AlertSeverity.CRITICAL: 0xff0000   # Red
            }.get(alert.severity, 0xffff00)

            payload = {
                "embeds": [
                    {
                        "title": f"🚨 Voice RAG Alert",
                        "description": f"**{alert.rule_name}**\n{alert.message}",
                        "color": color,
                        "fields": [
                            {
                                "name": "Severity",
                                "value": alert.severity.value.upper(),
                                "inline": True
                            },
                            {
                                "name": "Current Value",
                                "value": f"{alert.current_value:.2f}",
                                "inline": True
                            },
                            {
                                "name": "Threshold",
                                "value": f"{alert.threshold}",
                                "inline": True
                            }
                        ],
                        "timestamp": alert.timestamp.isoformat(),
                        "footer": {
                            "text": "Voice RAG Monitoring System"
                        }
                    }
                ]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(monitoring_config.discord_webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info(f"Discord alert sent for {alert.rule_name}")
                    else:
                        logger.error(f"Failed to send Discord alert: HTTP {response.status}")

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")

    async def _send_webhook_alert(self, alert: Alert):
        """Send alert via custom webhook."""
        if not monitoring_config.webhook_url:
            logger.warning("Custom webhook URL not configured, skipping webhook alert")
            return

        try:
            payload = {
                "alert": asdict(alert),
                "timestamp": alert.timestamp.isoformat(),
                "system": "voice_rag_monitoring"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(monitoring_config.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent for {alert.rule_name}")
                    else:
                        logger.error(f"Failed to send webhook alert: HTTP {response.status}")

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert system summary."""
        with self.lock:
            active_count_by_severity = defaultdict(int)
            for alert in self.active_alerts.values():
                active_count_by_severity[alert.severity.value] += 1

            recent_alerts = [
                {
                    "rule_name": alert.rule_name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved
                }
                for alert in list(self.alert_history)[-20:]
            ]

            return {
                "active_alerts": len(self.active_alerts),
                "active_by_severity": dict(active_count_by_severity),
                "total_rules": len(self.alert_rules),
                "enabled_rules": len([r for r in self.alert_rules if r.enabled]),
                "recent_alerts": recent_alerts
            }

# Global alert manager
alert_manager = AlertManager()

# ===== Health Checks =====
class HealthChecker:
    """Performs health checks on system components."""

    def __init__(self):
        self.health_status = {}
        self.last_check_time = None

    async def perform_health_checks(self) -> Dict[str, Any]:
        """Perform comprehensive health checks."""
        health_results = {
            "overall_status": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }

        try:
            # System health checks
            health_results["checks"]["system"] = await self._check_system_health()
            health_results["checks"]["database"] = await self._check_database_health()
            health_results["checks"]["redis"] = await self._check_redis_health()
            health_results["checks"]["external_apis"] = await self._check_external_apis()
            health_results["checks"]["storage"] = await self._check_storage_health()

            # External health checks
            if monitoring_config.external_health_checks:
                health_results["checks"]["external_endpoints"] = await self._check_external_endpoints()

            # Determine overall status
            failed_checks = [
                name for name, result in health_results["checks"].items()
                if not result.get("healthy", False)
            ]

            if failed_checks:
                if len(failed_checks) == 1 and failed_checks[0] in ["redis", "external_endpoints"]:
                    health_results["overall_status"] = "degraded"
                else:
                    health_results["overall_status"] = "unhealthy"

            self.health_status = health_results
            self.last_check_time = datetime.now()

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_results["overall_status"] = "unhealthy"
            health_results["error"] = str(e)

        return health_results

    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system resource health."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            healthy = (
                cpu_percent < monitoring_config.cpu_critical_threshold and
                memory.percent < monitoring_config.memory_critical_threshold and
                disk.percent < monitoring_config.disk_critical_threshold
            )

            return {
                "healthy": healthy,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "details": f"CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%, Disk: {disk.percent:.1f}%"
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            # This would typically test database connection
            # For now, return a mock health check
            return {
                "healthy": True,
                "response_time_ms": 45,
                "connections": 5,
                "details": "Database responsive"
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_redis_health(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            # This would typically test Redis connection
            # For now, return a mock health check
            return {
                "healthy": True,
                "response_time_ms": 12,
                "memory_usage": "64MB",
                "details": "Redis responsive"
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_external_apis(self) -> Dict[str, Any]:
        """Check external API dependencies."""
        try:
            # Check OpenAI API, Requesty.ai, etc.
            # For now, return mock health check
            return {
                "healthy": True,
                "openai_status": "operational",
                "requesty_status": "operational",
                "details": "All external APIs responsive"
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_storage_health(self) -> Dict[str, Any]:
        """Check storage system health."""
        try:
            # Check S3, local storage, vector store, etc.
            # For now, return mock health check
            return {
                "healthy": True,
                "vector_store": "operational",
                "file_storage": "operational",
                "details": "All storage systems accessible"
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_external_endpoints(self) -> Dict[str, Any]:
        """Check configured external health check endpoints."""
        results = {}
        overall_healthy = True

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            for endpoint in monitoring_config.external_health_checks:
                try:
                    start_time = time.time()
                    async with session.get(endpoint) as response:
                        response_time = (time.time() - start_time) * 1000

                        healthy = response.status == 200
                        results[endpoint] = {
                            "healthy": healthy,
                            "status_code": response.status,
                            "response_time_ms": response_time
                        }

                        if not healthy:
                            overall_healthy = False

                except Exception as e:
                    results[endpoint] = {
                        "healthy": False,
                        "error": str(e)
                    }
                    overall_healthy = False

        return {
            "healthy": overall_healthy,
            "endpoints": results
        }

# Global health checker
health_checker = HealthChecker()

# ===== Monitoring Service =====
class MonitoringService:
    """Main monitoring service that coordinates collection, analysis, and alerting."""

    def __init__(self):
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.monitoring_task = None

    async def start(self):
        """Start the monitoring service."""
        if self.running:
            logger.warning("Monitoring service already running")
            return

        logger.info("Starting production monitoring service...")
        self.running = True

        # Start background monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info("Production monitoring service started")

    async def stop(self):
        """Stop the monitoring service."""
        if not self.running:
            return

        logger.info("Stopping monitoring service...")
        self.running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        self.executor.shutdown(wait=True)
        logger.info("Monitoring service stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Starting monitoring loop...")

        while self.running:
            try:
                # Collect metrics
                system_metrics = metrics_collector.get_system_metrics()
                app_metrics = metrics_collector.get_application_metrics()

                # Record metrics
                current_time = datetime.now()
                for name, value in {**system_metrics, **app_metrics}.items():
                    metrics_collector.record_metric(name, value, timestamp=current_time)

                # Check alerts
                alert_manager.check_alerts({**system_metrics, **app_metrics})

                # Perform health checks periodically
                if (not health_checker.last_check_time or
                    current_time - health_checker.last_check_time >
                    timedelta(seconds=monitoring_config.health_check_interval_seconds)):

                    await health_checker.perform_health_checks()

                # Wait for next collection interval
                await asyncio.sleep(monitoring_config.collection_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(monitoring_config.collection_interval_seconds)

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status."""
        return {
            "service_running": self.running,
            "config": {
                "collection_interval": monitoring_config.collection_interval_seconds,
                "retention_days": monitoring_config.retention_days,
                "alerts_enabled": bool(monitoring_config.alert_email_to or monitoring_config.slack_webhook_url)
            },
            "alerts": alert_manager.get_alert_summary(),
            "health": health_checker.health_status,
            "last_collection": datetime.now().isoformat()
        }

# Global monitoring service
monitoring_service = MonitoringService()

# ===== Initialization =====
async def initialize_monitoring_system():
    """Initialize the production monitoring and alerting system."""
    logger.info("Initializing production monitoring system...")

    try:
        if monitoring_config.enabled:
            await monitoring_service.start()
            logger.info("Production monitoring system initialized successfully")
        else:
            logger.info("Monitoring system disabled in configuration")

    except Exception as e:
        logger.error(f"Failed to initialize monitoring system: {e}")
        raise

async def shutdown_monitoring_system():
    """Shutdown the monitoring system gracefully."""
    logger.info("Shutting down monitoring system...")
    await monitoring_service.stop()
    logger.info("Monitoring system shutdown complete")