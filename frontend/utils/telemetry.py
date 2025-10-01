"""Frontend telemetry logging utilities."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

from loguru import logger


class FrontendTelemetry:
    """Simple telemetry tracker for frontend events."""
    
    @staticmethod
    def log_event(
        event_type: str,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Log a frontend telemetry event.
        
        Args:
            event_type: Type of event (page_view, action, error, etc.)
            event_name: Specific event name
            properties: Additional event properties
            user_id: Optional user identifier
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "event_name": event_name,
            "properties": properties or {},
            "user_id": user_id,
        }
        
        logger.info(f"TELEMETRY: {json.dumps(event_data)}")
    
    @staticmethod
    def log_page_view(page_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Log a page view event."""
        FrontendTelemetry.log_event("page_view", page_name, properties)
    
    @staticmethod
    def log_action(action_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Log a user action event."""
        FrontendTelemetry.log_event("action", action_name, properties)
    
    @staticmethod
    def log_plan_created(plan_id: str, project_id: Optional[str] = None, template_used: Optional[str] = None) -> None:
        """Log plan creation event."""
        FrontendTelemetry.log_event(
            "plan_created",
            "devplan_generated",
            {
                "plan_id": plan_id,
                "project_id": project_id,
                "template_used": template_used,
            }
        )
    
    @staticmethod
    def log_voice_usage(action: str, duration: Optional[float] = None) -> None:
        """Log voice feature usage."""
        FrontendTelemetry.log_event(
            "voice_usage",
            action,
            {"duration_seconds": duration}
        )
    
    @staticmethod
    def log_error(error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log frontend error."""
        FrontendTelemetry.log_event(
            "error",
            error_type,
            {
                "error_message": error_message,
                "context": context or {}
            }
        )


# Convenience instance
telemetry = FrontendTelemetry()
