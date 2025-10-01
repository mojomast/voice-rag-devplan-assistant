"""Streamlit page for interacting with the Planning Agent."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st

from components.native_audio_recorder import native_audio_recorder
from frontend.utils.api_client import api_request, parse_response_json
from frontend.utils.telemetry import telemetry

PAGE_TITLE = "🗺️ Development Planning Assistant"


def _toast(message: str, icon: str = "ℹ️") -> None:
    if hasattr(st, "toast"):
        st.toast(message, icon=icon)
    else:  # pragma: no cover - compatibility fallback
        st.info(f"{icon} {message}")


def _latest_plan_version(plan: Dict) -> Optional[Dict]:
    versions = plan.get("versions") or []
    current_version = plan.get("current_version")
    for version in versions:
        if version.get("version_number") == current_version:
            return version
    return versions[0] if versions else None


def _init_session_state() -> None:
    defaults = {
        "planning_selected_project_id": None,
        "planning_session_id": None,
        "planning_chat_history": [],
        "planning_generated_plans": {},
        "planning_pending_message": None,
        "planning_auto_refresh": True,
        "planning_last_refresh": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _fetch_projects() -> List[Dict]:
    response, error = api_request("GET", "/projects/")
    if error:
        st.error(f"Failed to load projects: {error}")
        return []
    if response is None or response.status_code != 200:
        detail = response.text if response is not None else "No response"
        st.error(f"Failed to load projects (HTTP {response.status_code if response else 'n/a'}): {detail}")
        return []
    data = parse_response_json(response)
    return data or []


def _create_project(name: str, description: str, tags: List[str], repository_path: Optional[str]) -> Optional[Dict]:
    payload = {
        "name": name,
        "description": description or "",
        "tags": [tag.strip() for tag in tags if tag.strip()],
        "repository_path": repository_path or None,
    }
    response, error = api_request("POST", "/projects/", json=payload)
    if error:
        st.error(f"Project creation failed: {error}")
        return None
    if response is None or response.status_code != 201:
        message = "Unknown error"
        if response is not None:
            try:
                detail = response.json()
                message = detail.get("detail", response.text)
            except ValueError:
                message = response.text
        st.error(f"Project creation failed: {message}")
        return None
    return parse_response_json(response)


def _fetch_sessions(project_id: Optional[str] = None) -> List[Dict]:
    response, error = api_request("GET", "/planning/sessions")
    if error:
        st.error(f"Failed to load sessions: {error}")
        return []
    if response is None or response.status_code != 200:
        st.error("Unable to fetch planning sessions")
        return []
    sessions = parse_response_json(response) or []
    if project_id:
        sessions = [session for session in sessions if session.get("project_id") == project_id]
    return sessions


def _load_session(session_id: str) -> None:
    response, error = api_request("GET", f"/planning/sessions/{session_id}")
    if error:
        st.error(f"Failed to load session: {error}")
        return
    if response is None or response.status_code != 200:
        st.error("Unable to load session details")
        return
    detail = parse_response_json(response) or {}
    messages = detail.get("messages", [])
    formatted_history: List[Dict] = []
    for message in messages:
        formatted_history.append(
            {
                "role": message.get("role", "assistant"),
                "content": message.get("content", ""),
                "timestamp": message.get("timestamp"),
                "modality": message.get("modality", "text"),
            }
        )
    st.session_state.planning_chat_history = formatted_history
    st.session_state.planning_session_id = detail.get("id")
    generated_plan_ids = detail.get("generated_plans") or []
    plan_map: Dict[str, Dict] = {}
    for plan_id in generated_plan_ids:
        plan = _fetch_plan(plan_id)
        if plan:
            plan_map[plan_id] = plan
    st.session_state.planning_generated_plans = plan_map


def _send_message(message: str, project_id: Optional[str], session_id: Optional[str]) -> Optional[Dict]:
    payload = {
        "message": message,
        "project_id": project_id,
        "session_id": session_id,
        "modality": "text",
    }
    response, error = api_request("POST", "/planning/chat", json=payload)
    if error:
        st.error(f"Failed to send message: {error}")
        return None
    if response is None or response.status_code != 200:
        try:
            detail = response.json()
            message_text = detail.get("detail", response.text)
        except Exception:  # pragma: no cover - fallback path
            message_text = response.text if response is not None else "No response"
        st.error(f"Planning agent error: {message_text}")
        return None
    return parse_response_json(response)


def _fetch_plan(plan_id: str) -> Optional[Dict]:
    response, error = api_request("GET", f"/devplans/{plan_id}")
    if error:
        st.warning(f"Unable to retrieve generated plan ({plan_id}): {error}")
        return None
    if response is None or response.status_code != 200:
        st.warning(f"Plan {plan_id} preview unavailable (HTTP {response.status_code if response else 'n/a'})")
        return None
    return parse_response_json(response)


def _transcribe_audio(audio_payload: Dict[str, str]) -> Optional[str]:
    request_payload = {
        "audio_data": audio_payload.get("audio_data"),
        "mime_type": audio_payload.get("mime_type", "audio/webm"),
    }
    response, error = api_request("POST", "/voice/transcribe-base64", json=request_payload)
    if error:
        st.error(f"Transcription failed: {error}")
        return None
    if response is None or response.status_code != 200:
        st.error("Audio transcription failed")
        return None
    data = parse_response_json(response) or {}
    return data.get("text")


def _update_plan_status(plan_id: str, new_status: str) -> Optional[Dict]:
    """Update plan status via API."""
    response, error = api_request("PATCH", f"/devplans/{plan_id}/status?status={new_status}")
    if error:
        st.error(f"Failed to update plan status: {error}")
        return None
    if response is None or response.status_code != 200:
        st.error(f"Status update failed (HTTP {response.status_code if response else 'n/a'})")
        return None
    return parse_response_json(response)


def _search_plans(query: str, project_id: Optional[str] = None, limit: int = 5) -> List[Dict]:
    """Search plans using semantic search API."""
    payload = {
        "query": query,
        "project_id": project_id,
        "limit": limit,
    }
    response, error = api_request("POST", "/search/plans", json=payload)
    if error:
        st.warning(f"Search failed: {error}")
        return []
    if response is None or response.status_code != 200:
        return []
    data = parse_response_json(response) or {}
    return data.get("results", [])


def _render_plan_preview(plan: Dict) -> None:
    latest_version = _latest_plan_version(plan)
    content = latest_version.get("content", "") if latest_version else "No content"
    current_status = plan.get("status", "draft")
    
    # Status badge with color
    status_colors = {
        "draft": "🟡",
        "approved": "🟢",
        "in_progress": "🔵",
        "completed": "✅",
        "archived": "⚫"
    }
    status_icon = status_colors.get(current_status, "⚪")
    
    with st.expander(
        f"📋 Generated Plan — {plan.get('title', 'Untitled')} (v{plan.get('current_version', 1)}) {status_icon} {current_status}",
        expanded=True
    ):
        st.markdown(content or "No content available.")
        meta = plan.get("metadata", {})
        if meta:
            st.markdown("**Metadata:**")
            for key, value in meta.items():
                st.write(f"- **{key}**: {value}")
        
        st.divider()
        st.markdown("**Quick Actions:**")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📋 View", key=f"open_{plan['id']}", use_container_width=True):
                st.session_state["devplan_viewer.selected_plan_id"] = plan["id"]
                _toast("Plan selected. Open the DevPlan Viewer page to inspect it.", icon="📋")
        
        with col2:
            if current_status != "approved" and st.button("✅ Approve", key=f"approve_{plan['id']}", use_container_width=True):
                telemetry.log_action("plan_approved", {"plan_id": plan["id"]})
                updated = _update_plan_status(plan["id"], "approved")
                if updated:
                    st.session_state.planning_generated_plans[plan["id"]] = updated
                    _toast(f"Plan '{plan.get('title')}' approved!", icon="✅")
                    st.rerun()
        
        with col3:
            if current_status != "in_progress" and st.button("🚀 Start", key=f"start_{plan['id']}", use_container_width=True):
                updated = _update_plan_status(plan["id"], "in_progress")
                if updated:
                    st.session_state.planning_generated_plans[plan["id"]] = updated
                    _toast(f"Plan '{plan.get('title')}' is now in progress!", icon="🚀")
                    st.rerun()
        
        with col4:
            if current_status != "completed" and st.button("✔️ Complete", key=f"complete_{plan['id']}", use_container_width=True):
                updated = _update_plan_status(plan["id"], "completed")
                if updated:
                    st.session_state.planning_generated_plans[plan["id"]] = updated
                    _toast(f"Plan '{plan.get('title')}' marked complete!", icon="✔️")
                    st.rerun()
        
        with col5:
            if current_status != "archived" and st.button("📦 Archive", key=f"archive_{plan['id']}", use_container_width=True):
                updated = _update_plan_status(plan["id"], "archived")
                if updated:
                    st.session_state.planning_generated_plans[plan["id"]] = updated
                    _toast(f"Plan '{plan.get('title')}' archived.", icon="📦")
                    st.rerun()
        
        st.caption(f"Created: {plan.get('created_at', '-')} | Updated: {plan.get('updated_at', '-')}")


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🗺️", layout="wide")
    _init_session_state()
    
    # Log page view
    telemetry.log_page_view("planning_chat", {"project_id": st.session_state.get("planning_selected_project_id")})

    # Sidebar for semantic search
    with st.sidebar:
        st.markdown("### 🔍 Search Past Plans")
        st.caption("Find relevant plans using semantic search")
        
        search_query = st.text_input(
            "Search",
            placeholder="e.g., authentication system",
            key="plan_search_query"
        )
        
        search_scope = st.radio(
            "Search Scope",
            ["Current Project", "All Projects"],
            key="plan_search_scope"
        )
        
        if search_query and st.button("🔍 Search", use_container_width=True):
            project_filter = st.session_state.get("planning_selected_project_id") if search_scope == "Current Project" else None
            
            with st.spinner("Searching..."):
                results = _search_plans(search_query, project_id=project_filter, limit=5)
            
            if not results:
                st.info("No matching plans found.")
            else:
                st.success(f"Found {len(results)} relevant plan(s)")
                
                for result in results:
                    score_pct = result.get('score', 0) * 100
                    with st.expander(f"📋 {result['title']} ({score_pct:.0f}%)", expanded=False):
                        st.caption(f"**ID:** `{result['id']}`")
                        metadata = result.get('metadata', {})
                        st.caption(f"**Status:** {metadata.get('status', 'unknown')}")
                        st.caption(f"**Project:** {metadata.get('project_id', 'N/A')[:16]}...")
                        
                        # Preview
                        preview = result.get('content_preview', '')[:200]
                        if preview:
                            with st.container():
                                st.markdown("**Preview:**")
                                st.text(preview + "...")
                        
                        # Actions
                        action_cols = st.columns(2)
                        with action_cols[0]:
                            if st.button("View Full Plan", key=f"view_{result['id']}", use_container_width=True):
                                plan = _fetch_plan(result['id'])
                                if plan:
                                    st.session_state.planning_generated_plans[result['id']] = plan
                                    _toast(f"Added '{result['title']}' to current view", icon="📋")
                                    st.rerun()
                        with action_cols[1]:
                            if st.button("Use as Context", key=f"ctx_{result['id']}", use_container_width=True):
                                context_msg = f"Please reference this plan: {result['title']} (ID: {result['id']})"
                                st.session_state.planning_chat_history.append({
                                    "role": "user",
                                    "content": context_msg,
                                })
                                st.session_state.planning_pending_message = context_msg
                                _toast("Context added to conversation", icon="💬")
                                st.rerun()
        
        st.markdown("---")
        st.caption("💡 **Tip:** Search is powered by semantic RAG—it understands concepts, not just keywords!")

    st.title(PAGE_TITLE)
    st.caption("Chat with the planning agent to create and iterate on development plans.")

    projects = _fetch_projects()

    col_selector, col_actions = st.columns([2, 1])

    with col_selector:
        options = [
            {"label": "🌱 Unassigned Session", "id": None},
            *(
                {
                    "label": f"{project['name']} ({project.get('status', 'active')})",
                    "id": project["id"],
                }
                for project in projects
            ),
        ]
        option_labels = [opt["label"] for opt in options]
        selected_label = option_labels[0]
        if st.session_state.planning_selected_project_id is not None:
            for opt in options:
                if opt["id"] == st.session_state.planning_selected_project_id:
                    selected_label = opt["label"]
                    break
        selected_label = st.selectbox("Project", option_labels, index=option_labels.index(selected_label))
        selected_project = next(opt for opt in options if opt["label"] == selected_label)
        st.session_state.planning_selected_project_id = selected_project["id"]

    with col_actions:
        with st.expander("➕ Create Project", expanded=False):
            with st.form("create_project_form"):
                name = st.text_input("Project Name", placeholder="e.g. Voice Planning Assistant")
                description = st.text_area("Description", height=80)
                tags_raw = st.text_input("Tags", placeholder="comma,separated,tags")
                repo = st.text_input("Repository Path", placeholder="/path/to/repo")
                submitted = st.form_submit_button("Create Project", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.warning("Project name is required")
                else:
                    tags = [tag.strip() for tag in tags_raw.split(",")] if tags_raw else []
                    project = _create_project(name.strip(), description, tags, repo)
                    if project:
                        st.success(f"Project '{project['name']}' created")
                        st.session_state.planning_selected_project_id = project["id"]
                        st.session_state.planning_session_id = None
                        st.session_state.planning_chat_history = []
                        st.experimental_rerun()

    project_id = st.session_state.planning_selected_project_id
    sessions = _fetch_sessions(project_id)
    session_options = [
        {"label": "🆕 Start New Session", "id": None},
        *(
            {
                "label": f"Session {session['id'][:8]} — {session.get('started_at', '')[:16]}",
                "id": session["id"],
            }
            for session in sessions
        ),
    ]

    current_session_label = session_options[0]["label"]
    if st.session_state.planning_session_id:
        for opt in session_options:
            if opt["id"] == st.session_state.planning_session_id:
                current_session_label = opt["label"]
                break

    selected_session_label = st.selectbox(
        "Planning Session",
        [opt["label"] for opt in session_options],
        index=[opt["label"] for opt in session_options].index(current_session_label),
    )
    selected_session = next(opt for opt in session_options if opt["label"] == selected_session_label)

    if selected_session["id"] and selected_session["id"] != st.session_state.planning_session_id:
        _load_session(selected_session["id"])

    st.divider()
    st.subheader("Conversation")

    for message in st.session_state.planning_chat_history:
        role = message.get("role", "assistant")
        with st.chat_message(role):
            st.markdown(message.get("content", ""))
            if message.get("timestamp"):
                st.caption(f"{message['timestamp']}")

    tab_text, tab_voice = st.tabs(["✍️ Text", "🎙️ Voice"])

    with tab_text:
        # Prompt templates
        with st.expander("📝 Use a Prompt Template", expanded=False):
            st.caption("Start with a pre-built template for common planning scenarios")
            templates_response, templates_error = api_request("GET", "/templates/")
            if templates_response and templates_response.status_code == 200:
                templates = parse_response_json(templates_response) or {}
                if templates:
                    template_options = ["Select a template..."] + [
                        f"{template['title']} ({template['category']})"
                        for tid, template in templates.items()
                    ]
                    selected_template = st.selectbox("Choose template", template_options)
                    
                    if selected_template != "Select a template...":
                        # Find the selected template
                        for tid, template in templates.items():
                            if f"{template['title']} ({template['category']})" == selected_template:
                                st.markdown(f"**{template['title']}**")
                                st.caption(f"Category: {template['category']}")
                                if st.button("⬇️ Load Template", use_container_width=True):
                                    # Pre-fill the chat input by adding to pending message
                                    st.session_state.planning_pending_message = template['prompt']
                                    st.session_state.planning_chat_history.append({
                                        "role": "user",
                                        "content": f"📝 Using template: {template['title']}\n\n{template['prompt']}"
                                    })
                                    st.experimental_rerun()
                                with st.expander("Preview", expanded=False):
                                    st.code(template['prompt'], language=None)
                                break
        
        prompt = st.chat_input("Describe what you want to build or ask the planning agent...")
        if prompt:
            st.session_state.planning_chat_history.append({"role": "user", "content": prompt})
            st.session_state.planning_pending_message = prompt
            st.experimental_rerun()

    with tab_voice:
        st.info("Record a voice note to send to the planning agent. We'll transcribe it before sending.")
        audio_payload = native_audio_recorder(height=320)
        if audio_payload:
            cols = st.columns([1, 1])
            with cols[0]:
                st.metric("Duration", audio_payload.get("duration", "--"))
            with cols[1]:
                st.metric("Size", f"{audio_payload.get('size', 0) / 1024:.1f} KB")
            if st.button("📝 Transcribe & Send", use_container_width=True):
                transcription = _transcribe_audio(audio_payload)
                if transcription:
                    telemetry.log_voice_usage("transcribe", audio_payload.get("duration"))
                    st.session_state.planning_chat_history.append({
                        "role": "user",
                        "content": f"🎙️ {transcription}",
                        "modality": "voice",
                    })
                    st.session_state.planning_pending_message = transcription
                    st.experimental_rerun()

    pending_message = st.session_state.pop("planning_pending_message", None)
    if pending_message:
        with st.chat_message("assistant"):
            with st.spinner("Planning agent is thinking..."):
                result = _send_message(pending_message, project_id, st.session_state.planning_session_id)
        if result:
            session_id = result.get("session_id")
            if session_id:
                st.session_state.planning_session_id = session_id
            reply = result.get("response", "No response")
            st.session_state.planning_chat_history.append({
                "role": "assistant",
                "content": reply,
            })
            plan_id = result.get("generated_plan_id")
            if plan_id and plan_id not in st.session_state.planning_generated_plans:
                plan = _fetch_plan(plan_id)
                if plan:
                    st.session_state.planning_generated_plans[plan_id] = plan
                    # Log plan creation
                    telemetry.log_plan_created(plan_id, project_id)
                    # Show notification for new plan generation
                    _toast(
                        f"🎉 New development plan created: '{plan.get('title', 'Untitled')}'",
                        icon="🎉"
                    )

        st.experimental_rerun()

    if st.session_state.planning_generated_plans:
        st.divider()
        st.subheader("Latest Generated Plans")
        for plan in st.session_state.planning_generated_plans.values():
            _render_plan_preview(plan)
    
    # Auto-refresh functionality
    st.divider()
    col_refresh1, col_refresh2 = st.columns([3, 1])
    with col_refresh1:
        auto_refresh = st.checkbox(
            "🔄 Auto-refresh conversation",
            value=st.session_state.planning_auto_refresh,
            help="Automatically refresh messages and plans every 10 seconds"
        )
        st.session_state.planning_auto_refresh = auto_refresh
    
    with col_refresh2:
        if st.button("🔄 Refresh Now", use_container_width=True):
            if st.session_state.planning_session_id:
                _load_session(st.session_state.planning_session_id)
                _toast("Conversation refreshed!", icon="🔄")
                st.rerun()
    
    # Auto-refresh timer
    if st.session_state.planning_auto_refresh and st.session_state.planning_session_id:
        current_time = time.time()
        if current_time - st.session_state.planning_last_refresh > 10:  # 10 seconds
            st.session_state.planning_last_refresh = current_time
            _load_session(st.session_state.planning_session_id)
            st.rerun()


if __name__ == "__main__":
    main()
