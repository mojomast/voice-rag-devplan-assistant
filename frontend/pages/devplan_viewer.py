"""Streamlit page for viewing and editing development plans."""

from __future__ import annotations

import json
from difflib import unified_diff
from typing import Dict, List, Optional

import streamlit as st

from frontend.utils.api_client import api_request, parse_response_json

PAGE_TITLE = "📋 DevPlan Viewer"


def _latest_version(plan: Dict, versions: List[Dict]) -> Optional[Dict]:
    current_version = plan.get("current_version")
    for version in versions:
        if version.get("version_number") == current_version:
            return version
    return versions[0] if versions else None


def _fetch_projects() -> List[Dict]:
    response, error = api_request("GET", "/projects/")
    if error:
        st.error(f"Unable to load projects: {error}")
        return []
    if response is None or response.status_code != 200:
        st.error("Failed to load projects")
        return []
    return parse_response_json(response) or []


def _fetch_plan(plan_id: str) -> Optional[Dict]:
    response, error = api_request("GET", f"/devplans/{plan_id}")
    if error:
        st.error(f"Failed to load plan: {error}")
        return None
    if response is None or response.status_code != 200:
        st.error("Plan details unavailable")
        return None
    return parse_response_json(response)


def _fetch_plan_versions(plan_id: str) -> List[Dict]:
    response, error = api_request("GET", f"/devplans/{plan_id}/versions")
    if error:
        st.warning(f"Unable to load version history: {error}")
        return []
    if response is None or response.status_code != 200:
        st.warning("Version history unavailable")
        return []
    return parse_response_json(response) or []


def _fetch_plans_for_project(project_id: str) -> List[Dict]:
    response, error = api_request("GET", f"/projects/{project_id}/plans")
    if error:
        st.warning(f"Could not load plans: {error}")
        return []
    if response is None or response.status_code != 200:
        st.warning("Plan list unavailable")
        return []
    return parse_response_json(response) or []


def _update_plan(plan_id: str, title: str, status: str, metadata: Dict) -> bool:
    payload = {
        "title": title,
        "status": status,
        "metadata": metadata,
    }
    response, error = api_request("PUT", f"/devplans/{plan_id}", json=payload)
    if error:
        st.error(f"Failed to update plan: {error}")
        return False
    if response is None or response.status_code != 200:
        st.error("Plan update failed")
        return False
    return True


def _create_version(plan_id: str, content: str, change_summary: Optional[str], metadata: Optional[Dict]) -> bool:
    payload = {
        "content": content,
        "change_summary": change_summary or None,
        "metadata": metadata or None,
    }
    response, error = api_request("POST", f"/devplans/{plan_id}/versions", json=payload)
    if error:
        st.error(f"Failed to create new version: {error}")
        return False
    if response is None or response.status_code != 201:
        st.error("Version creation failed")
        return False
    return True


def _export_plan(plan_id: str, fmt: str) -> Optional[Dict]:
    response, error = api_request("GET", f"/devplans/{plan_id}/export", params={"format": fmt})
    if error:
        st.error(f"Export failed: {error}")
        return None
    if response is None or response.status_code != 200:
        st.error("Unable to export plan")
        return None
    return parse_response_json(response)


def _render_metadata_sidebar(plan: Dict) -> None:
    with st.sidebar:
        st.header("Plan Metadata")
        st.metric("Version", plan.get("current_version", 1))
        st.metric("Status", plan.get("status", "draft"))
        st.metric("Project", plan.get("project_id", "-"))
        st.caption(f"Created: {plan.get('created_at', '-')}")
        st.caption(f"Updated: {plan.get('updated_at', '-')}")

        metadata = plan.get("metadata", {})
        if metadata:
            st.subheader("Details")
            for key, value in metadata.items():
                st.write(f"- **{key}**: {value}")
        else:
            st.info("No additional metadata recorded.")


def _render_export_controls(plan: Dict) -> None:
    st.subheader("Export")
    col_md, col_json = st.columns(2)
    with col_md:
        export = _export_plan(plan["id"], "markdown")
        if export:
            st.download_button(
                "⬇️ Download Markdown",
                data=export.get("content", ""),
                file_name=f"{plan['title'].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )
    with col_json:
        export = _export_plan(plan["id"], "json")
        if export:
            content = json.dumps(export, indent=2)
            st.download_button(
                "⬇️ Download JSON",
                data=content,
                file_name=f"{plan['title'].replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )


def _render_version_history(plan_id: str, versions: List[Dict]) -> None:
    if not versions:
        st.info("No version history yet. Create a new version from the Edit tab.")
        return

    version_map = {version["version_number"]: version for version in versions}
    ordered_numbers = sorted(version_map.keys(), reverse=True)

    col_from, col_to = st.columns(2)
    with col_from:
        from_version = st.selectbox("Compare from", ordered_numbers, index=0)
    with col_to:
        to_version = st.selectbox("Compare to", ordered_numbers, index=min(1, len(ordered_numbers) - 1))

    if from_version == to_version:
        st.warning("Select two different versions to compare.")
        return

    from_content = version_map[from_version].get("content", "").splitlines()
    to_content = version_map[to_version].get("content", "").splitlines()

    diff = unified_diff(
        from_content,
        to_content,
        fromfile=f"v{from_version}",
        tofile=f"v{to_version}",
        lineterm="",
    )
    diff_text = "\n".join(diff)
    if not diff_text.strip():
        st.success("No changes between the selected versions.")
    else:
        st.code(diff_text or "No differences", language="diff")

    st.markdown("---")
    for version in versions:
        with st.expander(f"Version {version['version_number']} — {version.get('created_at', '-')}"):
            st.markdown(version.get("content", ""))
            if version.get("change_summary"):
                st.caption(f"Change summary: {version['change_summary']}")
            metadata = version.get("metadata", {})
            if metadata:
                st.caption("Metadata:")
                st.json(metadata)


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="📋", layout="wide")

    if "devplan_viewer.selected_plan_id" not in st.session_state:
        st.session_state["devplan_viewer.selected_plan_id"] = None

    st.title(PAGE_TITLE)
    st.caption("Inspect, edit, and export development plans generated by the planning agent.")

    projects = _fetch_projects()
    if not projects:
        st.stop()

    project_options = {project["name"]: project["id"] for project in projects}
    project_names = list(project_options.keys())
    default_project = project_names[0]

    if st.session_state["devplan_viewer.selected_plan_id"]:
        # Pre-select the project for the selected plan if possible
        for project in projects:
            plans = _fetch_plans_for_project(project["id"])
            if any(plan["id"] == st.session_state["devplan_viewer.selected_plan_id"] for plan in plans):
                default_project = project["name"]
                break

    selected_project_name = st.selectbox("Project", project_names, index=project_names.index(default_project))
    selected_project_id = project_options[selected_project_name]

    plans = _fetch_plans_for_project(selected_project_id)
    if not plans:
        st.info("No plans yet. Generate one from the Planning Chat page.")
        st.stop()

    plan_titles = {f"{plan['title']} (v{plan.get('current_version', 1)})": plan["id"] for plan in plans}
    default_plan_title = list(plan_titles.keys())[0]

    if st.session_state["devplan_viewer.selected_plan_id"]:
        for title, plan_id in plan_titles.items():
            if plan_id == st.session_state["devplan_viewer.selected_plan_id"]:
                default_plan_title = title
                break

    selected_plan_title = st.selectbox("Development Plan", list(plan_titles.keys()), index=list(plan_titles.keys()).index(default_plan_title))
    selected_plan_id = plan_titles[selected_plan_title]
    st.session_state["devplan_viewer.selected_plan_id"] = selected_plan_id

    plan = _fetch_plan(selected_plan_id)
    if not plan:
        st.stop()

    versions = _fetch_plan_versions(selected_plan_id)
    _render_metadata_sidebar(plan)

    tab_view, tab_edit, tab_history = st.tabs(["📄 View", "✏️ Edit", "🕐 History"])

    with tab_view:
        latest_version = _latest_version(plan, versions)
        st.markdown(latest_version.get("content", "No content available.") if latest_version else "No content available.")
        _render_export_controls(plan)

    with tab_edit:
        st.subheader("Update Plan Metadata")
        with st.form("update_plan_form"):
            new_title = st.text_input("Title", value=plan.get("title", ""))
            status_options = ["draft", "in_progress", "approved", "completed", "archived"]
            new_status = st.selectbox("Status", status_options, index=status_options.index(plan.get("status", "draft")))
            metadata_text = st.text_area(
                "Metadata (JSON)",
                value=json.dumps(plan.get("metadata", {}), indent=2),
                height=180,
                help="Optional structured metadata stored with the plan.",
            )
            submitted = st.form_submit_button("Save Plan Metadata", use_container_width=True)
        if submitted:
            try:
                metadata = json.loads(metadata_text) if metadata_text.strip() else {}
            except json.JSONDecodeError as exc:
                st.error(f"Invalid metadata JSON: {exc}")
            else:
                if _update_plan(selected_plan_id, new_title, new_status, metadata):
                    st.success("Plan metadata updated")
                    st.experimental_rerun()

        st.markdown("---")
        st.subheader("Create New Version")
        latest_version = _latest_version(plan, versions) or {"content": ""}
        version_form = st.form("new_version_form")
        with version_form:
            new_content = st.text_area("Plan Content", value=latest_version.get("content", ""), height=400)
            change_summary = st.text_input("Change Summary", placeholder="What changed in this version?")
            metadata_override = st.text_area(
                "Version Metadata (JSON)",
                value=json.dumps(latest_version.get("metadata", {}), indent=2) if latest_version.get("metadata") else "",
                height=150,
                help="Optional metadata specific to this version.",
            )
            create_version = st.form_submit_button("Create Version", use_container_width=True)
        if create_version:
            try:
                version_metadata = json.loads(metadata_override) if metadata_override.strip() else None
            except json.JSONDecodeError as exc:
                st.error(f"Invalid version metadata JSON: {exc}")
                version_metadata = None
            if new_content.strip() and _create_version(selected_plan_id, new_content, change_summary, version_metadata):
                st.success("New version created")
                st.experimental_rerun()
            elif not new_content.strip():
                st.warning("Plan content cannot be empty.")

    with tab_history:
        _render_version_history(selected_plan_id, versions)


if __name__ == "__main__":
    main()
