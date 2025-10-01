import streamlit as st
import requests
import time
import traceback
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import json

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    NETWORK = "network"
    PERMISSION = "permission"
    AUDIO_FORMAT = "audio_format"
    API = "api"
    BROWSER = "browser"
    USER_INPUT = "user_input"
    SYSTEM = "system"

@dataclass
class VoiceError:
    """Structured error information"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    title: str
    message: str
    technical_details: Optional[str] = None
    user_action: Optional[str] = None
    retry_possible: bool = True
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class VoiceErrorHandler:
    """Comprehensive error handling and user feedback system"""
    
    def __init__(self):
        self.error_history: List[VoiceError] = []
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.retry_attempts: Dict[str, int] = {}
        self.max_retries = 3
        
    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        show_to_user: bool = True
    ) -> VoiceError:
        """
        Handle an error with appropriate user feedback
        
        Args:
            error: The exception that occurred
            category: Error category for classification
            severity: Error severity level
            context: Additional context information
            show_to_user: Whether to show the error to the user
            
        Returns:
            VoiceError object with structured error information
        """
        
        # Generate error ID
        error_id = f"ERR_{int(time.time())}_{len(self.error_history)}"
        
        # Create structured error
        voice_error = self._create_voice_error(error, error_id, category, severity, context)
        
        # Add to history
        self.error_history.append(voice_error)
        
        # Keep only last 50 errors
        if len(self.error_history) > 50:
            self.error_history = self.error_history[-50:]
        
        # Log error
        self._log_error(voice_error)
        
        # Show to user if requested
        if show_to_user:
            self._display_error_to_user(voice_error)
        
        # Trigger callbacks
        self._trigger_error_callbacks(voice_error)
        
        return voice_error
    
    def _create_voice_error(
        self,
        error: Exception,
        error_id: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Optional[Dict[str, Any]]
    ) -> VoiceError:
        """Create a structured VoiceError from an exception"""
        
        # Get error information
        error_type = type(error).__name__
        error_message = str(error)
        technical_details = traceback.format_exc()
        
        # Determine title and user action based on category and error type
        title, user_action, retry_possible = self._get_error_info(error, category, error_type)
        
        # Enhance with context
        if context:
            if 'operation' in context:
                title = f"Error in {context['operation']}: {title}"
            if 'user_action_suggestion' in context:
                user_action = context['user_action_suggestion']
        
        return VoiceError(
            error_id=error_id,
            category=category,
            severity=severity,
            title=title,
            message=error_message,
            technical_details=technical_details,
            user_action=user_action,
            retry_possible=retry_possible
        )
    
    def _get_error_info(self, error: Exception, category: ErrorCategory, error_type: str) -> tuple:
        """Get user-friendly error information based on error type and category"""
        
        if category == ErrorCategory.NETWORK:
            if "timeout" in error_type.lower() or "timeout" in str(error).lower():
                return "Network Timeout", "Check your internet connection and try again.", True
            elif "connection" in error_type.lower():
                return "Connection Error", "Unable to connect to the server. Please check your connection.", True
            else:
                return "Network Error", "A network error occurred. Please try again.", True
        
        elif category == ErrorCategory.PERMISSION:
            if "microphone" in str(error).lower():
                return "Microphone Access Denied", "Please allow microphone access in your browser settings and reload the page.", False
            elif "camera" in str(error).lower():
                return "Camera Access Denied", "Please allow camera access in your browser settings.", False
            else:
                return "Permission Denied", "Please check your browser permissions and try again.", False
        
        elif category == ErrorCategory.AUDIO_FORMAT:
            return "Audio Format Error", "The audio format is not supported. Please try a different format (MP3, WAV, WebM).", False
        
        elif category == ErrorCategory.API:
            if "401" in str(error) or "unauthorized" in str(error).lower():
                return "Authentication Error", "Please check your API credentials and try again.", False
            elif "429" in str(error) or "rate limit" in str(error).lower():
                return "Rate Limit Exceeded", "Too many requests. Please wait a moment and try again.", True
            elif "500" in str(error) or "internal server" in str(error).lower():
                return "Server Error", "The server encountered an error. Please try again later.", True
            else:
                return "API Error", "An API error occurred. Please try again.", True
        
        elif category == ErrorCategory.BROWSER:
            return "Browser Compatibility Error", "Your browser may not support this feature. Please try a modern browser.", False
        
        elif category == ErrorCategory.USER_INPUT:
            return "Invalid Input", "Please check your input and try again.", True
        
        else:  # SYSTEM
            return "System Error", "An unexpected error occurred. Please try again.", True
    
    def _log_error(self, error: VoiceError):
        """Log error for debugging"""
        
        log_message = f"[{error.severity.value.upper()}] {error.category.value}: {error.title}"
        
        if error.technical_details:
            log_message += f"\nTechnical Details: {error.technical_details}"
        
        # In a real implementation, this would log to a file or service
        print(f"VOICE_ERROR: {log_message}")
    
    def _display_error_to_user(self, error: VoiceError):
        """Display error to user with appropriate styling"""
        
        # Choose display method based on severity
        if error.severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 **{error.title}**\n\n{error.message}")
        elif error.severity == ErrorSeverity.HIGH:
            st.error(f"❌ **{error.title}**\n\n{error.message}")
        elif error.severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ **{error.title}**\n\n{error.message}")
        else:  # LOW
            st.info(f"ℹ️ **{error.title}**\n\n{error.message}")
        
        # Show user action if available
        if error.user_action:
            st.markdown(f"**💡 Suggested Action:** {error.user_action}")
        
        # Show retry option if possible
        if error.retry_possible:
            if st.button(f"🔄 Retry {error.title}", key=f"retry_{error.error_id}"):
                self._retry_operation(error.error_id)
        
        # Show technical details in expander for debugging
        if error.technical_details and st.checkbox("🔍 Show Technical Details", key=f"details_{error.error_id}"):
            st.code(error.technical_details, language="python")
    
    def _trigger_error_callbacks(self, error: VoiceError):
        """Trigger registered error callbacks"""
        
        if error.category in self.error_callbacks:
            for callback in self.error_callbacks[error.category]:
                try:
                    callback(error)
                except Exception as e:
                    print(f"Error in callback: {e}")
    
    def _retry_operation(self, error_id: str):
        """Retry the failed operation"""
        
        # Check retry count
        retry_count = self.retry_attempts.get(error_id, 0)
        if retry_count >= self.max_retries:
            st.warning("⚠️ Maximum retry attempts reached. Please try again later.")
            return
        
        # Increment retry count
        self.retry_attempts[error_id] = retry_count + 1
        
        # Show retry message
        st.info(f"🔄 Retrying operation (attempt {retry_count + 1}/{self.max_retries})...")
        
        # In a real implementation, this would trigger the actual retry
        # For now, we'll just wait a moment
        time.sleep(1)
        
        st.rerun()
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """Register a callback for specific error categories"""
        
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        
        self.error_callbacks[category].append(callback)
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.retry_attempts.clear()
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors"""
        
        if not self.error_history:
            return {"total_errors": 0, "by_category": {}, "by_severity": {}}
        
        by_category = {}
        by_severity = {}
        
        for error in self.error_history:
            # Count by category
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
            
            # Count by severity
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": self.error_history[-5:]  # Last 5 errors
        }

class VoiceUserFeedback:
    """User feedback and notification system"""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
        self.feedback_history: List[Dict[str, Any]] = []
        
    def show_success(self, message: str, details: Optional[str] = None, duration: int = 3):
        """Show success notification"""
        
        notification = {
            "type": "success",
            "message": message,
            "details": details,
            "timestamp": time.time(),
            "duration": duration
        }
        
        self._display_notification(notification)
        self.notifications.append(notification)
    
    def show_info(self, message: str, details: Optional[str] = None, duration: int = 5):
        """Show info notification"""
        
        notification = {
            "type": "info",
            "message": message,
            "details": details,
            "timestamp": time.time(),
            "duration": duration
        }
        
        self._display_notification(notification)
        self.notifications.append(notification)
    
    def show_warning(self, message: str, details: Optional[str] = None, duration: int = 7):
        """Show warning notification"""
        
        notification = {
            "type": "warning",
            "message": message,
            "details": details,
            "timestamp": time.time(),
            "duration": duration
        }
        
        self._display_notification(notification)
        self.notifications.append(notification)
    
    def show_progress(self, message: str, steps: Optional[List[str]] = None):
        """Show progress indicator"""
        
        progress_html = f"""
        <div style="
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            text-align: center;
        ">
            <div style="display: flex; align-items: center; justify-content: center;">
                <div class="spinner" style="
                    border: 3px solid rgba(255,255,255,0.3);
                    border-radius: 50%;
                    border-top: 3px solid white;
                    width: 20px;
                    height: 20px;
                    animation: spin 1s linear infinite;
                    margin-right: 10px;
                "></div>
                <strong>{message}</strong>
            </div>
        </div>
        <style>
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """
        
        st.markdown(progress_html, unsafe_allow_html=True)
        
        if steps:
            for i, step in enumerate(steps):
                st.markdown(f"{'✅' if i < len(steps) - 1 else '⏳'} {step}")
    
    def _display_notification(self, notification: Dict[str, Any]):
        """Display notification to user"""
        
        icons = {
            "success": "✅",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌"
        }
        
        icon = icons.get(notification["type"], "📢")
        
        if notification["type"] == "success":
            st.success(f"{icon} **{notification['message']}**")
        elif notification["type"] == "info":
            st.info(f"{icon} **{notification['message']}**")
        elif notification["type"] == "warning":
            st.warning(f"{icon} **{notification['message']}**")
        elif notification["type"] == "error":
            st.error(f"{icon} **{notification['message']}**")
        
        if notification["details"]:
            st.caption(notification["details"])
    
    def collect_feedback(self, feature: str, rating: int, comment: str = ""):
        """Collect user feedback"""
        
        feedback = {
            "feature": feature,
            "rating": rating,
            "comment": comment,
            "timestamp": time.time(),
            "user_agent": st.experimental_get_query_params().get("user_agent", ["Unknown"])[0]
        }
        
        self.feedback_history.append(feedback)
        
        # In a real implementation, this would send to a feedback service
        print(f"FEEDBACK: {feedback}")
    
    def show_feedback_form(self, feature: str):
        """Show feedback form for a feature"""
        
        st.markdown(f"### 📝 Feedback for {feature}")
        
        rating = st.slider(
            "Rate your experience:",
            min_value=1,
            max_value=5,
            value=5,
            help="1 = Poor, 5 = Excellent"
        )
        
        comment = st.text_area(
            "Additional comments (optional):",
            placeholder="Tell us about your experience...",
            height=100
        )
        
        if st.button("Submit Feedback", type="primary"):
            self.collect_feedback(feature, rating, comment)
            st.success("✅ Thank you for your feedback!")
            time.sleep(1)
            st.rerun()

# Global error handler and feedback instances
global_error_handler = VoiceErrorHandler()
global_feedback = VoiceUserFeedback()

def handle_voice_error(
    error: Exception,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None,
    show_to_user: bool = True
) -> VoiceError:
    """Global function to handle voice errors"""
    return global_error_handler.handle_error(error, category, severity, context, show_to_user)

def show_voice_success(message: str, details: Optional[str] = None):
    """Global function to show success messages"""
    global_feedback.show_success(message, details)

def show_voice_info(message: str, details: Optional[str] = None):
    """Global function to show info messages"""
    global_feedback.show_info(message, details)

def show_voice_warning(message: str, details: Optional[str] = None):
    """Global function to show warning messages"""
    global_feedback.show_warning(message, details)

def show_voice_progress(message: str, steps: Optional[List[str]] = None):
    """Global function to show progress"""
    global_feedback.show_progress(message, steps)

def safe_api_call(
    func: Callable,
    *args,
    error_category: ErrorCategory = ErrorCategory.API,
    error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Any:
    """
    Safely execute an API call with error handling
    
    Args:
        func: Function to call
        *args: Function arguments
        error_category: Category for potential errors
        error_severity: Severity for potential errors
        context: Additional context
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or None if error occurred
    """
    
    try:
        return func(*args, **kwargs)
    except requests.RequestException as e:
        handle_voice_error(e, error_category, error_severity, context)
        return None
    except Exception as e:
        handle_voice_error(e, ErrorCategory.SYSTEM, error_severity, context)
        return None

# Example usage and testing
def test_error_handling():
    """Test the error handling system"""
    
    st.title("🧪 Voice Error Handling Test")
    
    # Test different error types
    st.markdown("### Test Error Categories")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test Network Error"):
            try:
                raise requests.ConnectionError("Failed to connect to server")
            except Exception as e:
                handle_voice_error(e, ErrorCategory.NETWORK, ErrorSeverity.HIGH)
    
    with col2:
        if st.button("Test Permission Error"):
            try:
                raise PermissionError("Microphone access denied")
            except Exception as e:
                handle_voice_error(e, ErrorCategory.PERMISSION, ErrorSeverity.HIGH)
    
    with col3:
        if st.button("Test API Error"):
            try:
                raise ValueError("Invalid API response")
            except Exception as e:
                handle_voice_error(e, ErrorCategory.API, ErrorSeverity.MEDIUM)
    
    # Test feedback system
    st.markdown("### Test Feedback System")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Test Success"):
            show_voice_success("Operation completed successfully!", "All systems working properly")
    
    with col2:
        if st.button("Test Warning"):
            show_voice_warning("This is a warning message", "Please be aware of this issue")
    
    with col3:
        if st.button("Test Progress"):
            show_voice_progress("Processing your request...", ["Step 1: Validating input", "Step 2: Processing data", "Step 3: Generating response"])
    
    # Show error summary
    st.markdown("### Error Summary")
    summary = global_error_handler.get_error_summary()
    
    if summary["total_errors"] > 0:
        st.json(summary)
    else:
        st.info("No errors recorded yet")
    
    # Show feedback form
    global_feedback.show_feedback_form("Voice Interface")

if __name__ == "__main__":
    test_error_handling()