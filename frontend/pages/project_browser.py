"""Streamlit page for browsing planning projects and related artifacts."""

from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st

from frontend.utils.api_client import api_request, parse_response_json

PAGE_TITLE = "📁 Project Browser"


def _toast(message: str, icon: str = "ℹ️") -> None:
    if hasattr(st, "toast"):
        st.toast(message, icon=icon)
    else:  # pragma: no cover - compatibility fallback
        st.info(f"{icon} {message}")


def _fetch_projects() -> List[Dict]:
    response, error = api_request("GET", "/projects/")
    if error:
        st.error(f"Unable to load projects: {error}")
        return []
    if response is None or response.status_code != 200:
        st.error("Failed to load projects from backend")
        return []
    return parse_response_json(response) or []


def _fetch_project(project_id: str) -> Optional[Dict]:
    response, error = api_request("GET", f"/projects/{project_id}")
    if error:
        st.error(f"Failed to load project details: {error}")
        return None
    if response is None or response.status_code != 200:
        st.error("Project details unavailable")
        return None
    return parse_response_json(response)


def _fetch_plans(project_id: str) -> List[Dict]:
    response, error = api_request("GET", f"/projects/{project_id}/plans")
    if error:
        st.warning(f"Could not load plans: {error}")
        return []
    if response is None or response.status_code != 200:
        st.warning("Plan list unavailable")
        return []
    return parse_response_json(response) or []


def _fetch_conversations(project_id: str) -> List[Dict]:
    response, error = api_request("GET", f"/projects/{project_id}/conversations")
    if error:
        st.warning(f"Could not load conversations: {error}")
        return []
    if response is None or response.status_code != 200:
        st.warning("Conversation history unavailable")
        return []
    return parse_response_json(response) or []


def _fetch_related_projects(project_id: str, limit: int = 5) -> List[Dict]:
    """Fetch semantically similar projects using RAG."""
    response, error = api_request("GET", f"/search/similar-projects/{project_id}", params={"limit": limit})
    if error:
        st.warning(f"Could not load related projects: {error}")
        return []
    if response is None or response.status_code != 200:
        return []
    return parse_response_json(response) or []


def _get_project_health(project_id: str) -> Dict:
    """Calculate project health metrics."""
    plans = _fetch_plans(project_id)
    
    if not plans:
        return {"status": "No plans", "health_score": 0, "icon": "⚪", "latest_plan_status": None}
    
    # Count plan statuses
    status_counts = {}
    for plan in plans:
        status = plan.get("status", "draft")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    latest_plan = plans[0]  # Assuming sorted by updated_at
    latest_status = latest_plan.get("status", "draft")
    
    # Calculate health score
    completed = status_counts.get("completed", 0)
    in_progress = status_counts.get("in_progress", 0)
    approved = status_counts.get("approved", 0)
    total = len(plans)
    
    health_score = ((completed * 3 + in_progress * 2 + approved * 1) / (total * 3)) * 100 if total > 0 else 0
    
    # Determine health status
    if health_score >= 70:
        health_status = "Excellent"
        health_icon = "🟢"
    elif health_score >= 40:
        health_status = "Good"
        health_icon = "🟡"
    else:
        health_status = "Needs Attention"
        health_icon = "🔴"
    
    return {
        "status": health_status,
        "health_score": int(health_score),
        "icon": health_icon,
        "latest_plan_status": latest_status,
        "completed": completed,
        "in_progress": in_progress,
        "total": total,
    }


def _render_project_card(project: Dict) -> None:
    with st.container():
        header_cols = st.columns([4, 1])
        with header_cols[0]:
            st.subheader(project["name"])
            if project.get("description"):
                st.caption(project["description"])
            tag_list = project.get("tags") or []
            if tag_list:
                st.write(" ".join(f"`{tag}`" for tag in tag_list))
        with header_cols[1]:
            st.metric("Plans", project.get("plan_count", 0))
            st.metric("Convos", project.get("conversation_count", 0))

        footer_cols = st.columns([1, 1, 1])
        with footer_cols[0]:
            status_icons = {
                "active": "🟢",
                "paused": "🟡",
                "completed": "✅",
                "archived": "⚫"
            }
            status = project.get('status', 'active')
            st.caption(f"{status_icons.get(status, '⚪')} {status.title()}")
        with footer_cols[1]:
            st.caption(f"Updated: {project.get('updated_at', '-')[:19]}")
        with footer_cols[2]:
            if st.button("View Details", key=f"view_{project['id']}", use_container_width=True):
                st.session_state["project_browser.selected_project_id"] = project["id"]
                st.experimental_rerun()

        st.markdown("---")


def _render_project_details(project_id: str) -> None:
    project = _fetch_project(project_id)
    if not project:
        return

    st.markdown(f"### {project['name']}")
    st.caption(project.get("description") or "No description provided")

    # Project Health Dashboard
    st.markdown("#### 📊 Project Health")
    health = _get_project_health(project_id)
    
    health_cols = st.columns(4)
    health_cols[0].metric(
        "Health Score",
        f"{health['health_score']}%",
        delta=health['status'],
        delta_color="normal" if health['health_score'] >= 40 else "inverse"
    )
    health_cols[1].metric("Completed Plans", f"{health.get('completed', 0)}/{health.get('total', 0)}")
    health_cols[2].metric("In Progress", health.get('in_progress', 0))
    if health['latest_plan_status']:
        status_chips = {
            "draft": "🟡 Draft",
            "approved": "🟢 Approved",
            "in_progress": "🔵 In Progress",
            "completed": "✅ Completed",
            "archived": "⚫ Archived"
        }
        health_cols[3].metric(
            "Latest Plan",
            status_chips.get(health['latest_plan_status'], health['latest_plan_status'])
        )
    
    st.markdown("---")

    with st.container():
        metric_cols = st.columns(3)
        metric_cols[0].metric("Project Status", project.get("status", "active"))
        metric_cols[1].metric("Total Plans", project.get("plan_count", 0))
        metric_cols[2].metric("Conversations", project.get("conversation_count", 0))

    quick_actions = st.columns(2)
    with quick_actions[0]:
        if st.button("Open in Planning Chat", use_container_width=True):
            st.session_state["planning_selected_project_id"] = project_id
            _toast("Project pinned for planning chat.", icon="🗺️")
    with quick_actions[1]:
        if st.button("Open DevPlan Viewer", use_container_width=True):
            plans = _fetch_plans(project_id)
            if plans:
                st.session_state["devplan_viewer.selected_plan_id"] = plans[0]["id"]
                _toast("First plan selected for the DevPlan Viewer.", icon="📋")
            else:
                st.info("No plans yet. Generate one via the planning chat.")

    st.markdown("---")
    st.subheader("Development Plans")
    plans = _fetch_plans(project_id)
    if not plans:
        st.info("No development plans available for this project yet.")
    else:
        for plan in plans:
            with st.expander(f"{plan['title']} (Status: {plan.get('status', 'draft')}, v{plan.get('current_version', 1)})"):
                cols = st.columns([2, 1, 1])
                with cols[0]:
                    st.write(f"Plan ID: `{plan['id']}`")
                    st.caption(f"Updated: {plan.get('updated_at', '-')}")
                with cols[1]:
                    if st.button("View Plan", key=f"detail_{plan['id']}"):
                        st.session_state["devplan_viewer.selected_plan_id"] = plan["id"]
                        _toast("Plan selected. Visit the DevPlan Viewer page to inspect it.", icon="📋")
                with cols[2]:
                    st.caption(f"Project: {plan.get('project_id', '-')}")

    st.markdown("---")
    st.subheader("🔗 Related Projects")
    st.caption("Semantically similar projects found via RAG analysis")
    related = _fetch_related_projects(project_id, limit=5)
    if not related:
        st.info("No related projects found. Create more projects to see similarities!")
    else:
        for item in related:
            score_pct = item.get('similarity_score', 0) * 100
            metadata = item.get('metadata', {})
            with st.expander(f"📁 {item['title']} — Similarity: {score_pct:.0f}%"):
                tags = metadata.get('tags', [])
                if tags:
                    st.write("Tags:", " ".join(f"`{tag}`" for tag in tags))
                st.metric("Plans", metadata.get('plan_count', 0))
                st.metric("Status", metadata.get('status', 'unknown'))
                if st.button("View This Project", key=f"related_{item['id']}"):
                    st.session_state["project_browser.selected_project_id"] = item["id"]
                    _toast(f"Switched to project: {item['title']}", icon="🔗")
                    st.rerun()
    
    st.markdown("---")
    st.subheader("Recent Conversations")
    conversations = _fetch_conversations(project_id)
    if not conversations:
        st.info("No planning conversations yet.")
    else:
        for convo in conversations:
            with st.expander(f"Session {convo['id'][:8]} — {convo.get('started_at', '')[:19]}"):
                st.write(convo.get("summary") or "No summary available.")
                generated = convo.get("generated_plans") or []
                if generated:
                    st.caption("Generated plans:")
                    st.write(", ".join(generated))


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="📁", layout="wide")

    st.title(PAGE_TITLE)
    st.caption("Browse projects, review generated plans, and jump into planning conversations.")

    if "project_browser.selected_project_id" not in st.session_state:
        st.session_state["project_browser.selected_project_id"] = None

    projects = _fetch_projects()
    if not projects:
        st.stop()

    tags = sorted({tag for project in projects for tag in project.get("tags", []) if tag})
    statuses = sorted({project.get("status", "active") for project in projects})

    filter_cols = st.columns([2, 1, 1])
    with filter_cols[0]:
        search_term = st.text_input("Search", placeholder="Search projects by name or description...")
    with filter_cols[1]:
        status_filter = st.selectbox("Status", ["All"] + statuses)
    with filter_cols[2]:
        selected_tags = st.multiselect("Tags", tags)

    filtered_projects = []
    for project in projects:
        matches_search = True
        if search_term:
            term = search_term.lower()
            matches_search = term in (project.get("name", "").lower()) or term in (project.get("description", "").lower())

        matches_status = status_filter == "All" or project.get("status", "active") == status_filter

        matches_tags = True
        if selected_tags:
            project_tags = set(project.get("tags", []))
            matches_tags = set(selected_tags).issubset(project_tags)

        if matches_search and matches_status and matches_tags:
            filtered_projects.append(project)

    if not filtered_projects:
        st.warning("No projects match the current filters.")

    list_col, detail_col = st.columns([2.5, 1.5])

    with list_col:
        st.markdown("### Project List")
        for project in filtered_projects:
            _render_project_card(project)

    with detail_col:
        selected_project_id = st.session_state["project_browser.selected_project_id"]
        if selected_project_id:
            _render_project_details(selected_project_id)
        else:
            st.info("Select a project to see details, plans, and recent conversations.")


if __name__ == "__main__":
    main()
