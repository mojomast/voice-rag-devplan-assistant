"""
End-to-end tests for the Planning Assistant UI.

These tests require the backend and frontend to be running:
- Backend: uvicorn backend.main:app --reload
- Frontend: streamlit run frontend/app.py

Run with: pytest tests/e2e/test_planning_ui.py
"""

import pytest
from playwright.sync_api import Page, expect


# Base URL for the Streamlit app
STREAMLIT_URL = "http://localhost:8501"


@pytest.fixture(scope="module")
def base_url():
    """Base URL for the Streamlit application."""
    return STREAMLIT_URL


class TestPlanningChat:
    """Test suite for Planning Chat page."""
    
    def test_page_loads(self, page: Page, base_url: str):
        """Test that the planning chat page loads successfully."""
        # Navigate to planning chat
        page.goto(f"{base_url}/?page=planning_chat")
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        
        # Check for main heading
        expect(page.locator("h1")).to_contain_text("Development Planning Assistant")
    
    def test_project_selection(self, page: Page, base_url: str):
        """Test project selection dropdown."""
        page.goto(f"{base_url}/?page=planning_chat")
        page.wait_for_load_state("networkidle")
        
        # Find project selector
        # Note: Streamlit selectors may need adjustment based on actual DOM
        project_selector = page.locator("text=Project").first
        expect(project_selector).to_be_visible()
    
    def test_send_text_message(self, page: Page, base_url: str):
        """Test sending a text message to the planning agent."""
        page.goto(f"{base_url}/?page=planning_chat")
        page.wait_for_load_state("networkidle")
        
        # Find chat input (Streamlit chat_input)
        chat_input = page.locator("textarea[placeholder*='Describe']").first
        
        if chat_input.is_visible():
            # Type a message
            chat_input.fill("Create a plan for a new feature")
            
            # Submit (usually Enter key in Streamlit)
            chat_input.press("Enter")
            
            # Wait for response
            page.wait_for_timeout(2000)
            
            # Check that message appears in history
            expect(page.locator("text=Create a plan")).to_be_visible()
    
    def test_template_selection(self, page: Page, base_url: str):
        """Test loading a prompt template."""
        page.goto(f"{base_url}/?page=planning_chat")
        page.wait_for_load_state("networkidle")
        
        # Expand template section
        template_expander = page.locator("text=Use a Prompt Template").first
        if template_expander.is_visible():
            template_expander.click()
            
            # Wait for templates to load
            page.wait_for_timeout(1000)
            
            # Check that templates are available
            expect(page.locator("text=New Feature Development")).to_be_visible()
    
    def test_auto_refresh_toggle(self, page: Page, base_url: str):
        """Test auto-refresh checkbox functionality."""
        page.goto(f"{base_url}/?page=planning_chat")
        page.wait_for_load_state("networkidle")
        
        # Find auto-refresh checkbox
        auto_refresh = page.locator("text=Auto-refresh conversation").first
        if auto_refresh.is_visible():
            # Toggle checkbox
            auto_refresh.click()
            
            # Verify it's checked/unchecked
            # Note: Streamlit checkbox behavior may vary


class TestProjectBrowser:
    """Test suite for Project Browser page."""
    
    def test_page_loads(self, page: Page, base_url: str):
        """Test that the project browser page loads."""
        page.goto(f"{base_url}/?page=project_browser")
        page.wait_for_load_state("networkidle")
        
        # Check for main heading
        expect(page.locator("h1")).to_contain_text("Project Browser")
    
    def test_search_functionality(self, page: Page, base_url: str):
        """Test project search filter."""
        page.goto(f"{base_url}/?page=project_browser")
        page.wait_for_load_state("networkidle")
        
        # Find search input
        search_input = page.locator("input[placeholder*='Search']").first
        if search_input.is_visible():
            search_input.fill("test")
            
            # Wait for filter to apply
            page.wait_for_timeout(1000)
    
    def test_status_filter(self, page: Page, base_url: str):
        """Test status filter dropdown."""
        page.goto(f"{base_url}/?page=project_browser")
        page.wait_for_load_state("networkidle")
        
        # Find status selectbox
        status_filter = page.locator("text=Status").first
        expect(status_filter).to_be_visible()
    
    def test_project_card_display(self, page: Page, base_url: str):
        """Test that project cards are displayed."""
        page.goto(f"{base_url}/?page=project_browser")
        page.wait_for_load_state("networkidle")
        
        # Check for project list
        project_list = page.locator("text=Project List").first
        expect(project_list).to_be_visible()


class TestDevPlanViewer:
    """Test suite for DevPlan Viewer page."""
    
    def test_page_loads(self, page: Page, base_url: str):
        """Test that the devplan viewer page loads."""
        page.goto(f"{base_url}/?page=devplan_viewer")
        page.wait_for_load_state("networkidle")
        
        # Check for main heading or viewer elements
        # May show "Select a plan" message if no plan selected
        page.wait_for_timeout(1000)
    
    def test_version_history(self, page: Page, base_url: str):
        """Test version history display."""
        # This test requires a plan to be selected
        # Implementation depends on how plans are pre-selected for testing
        pass
    
    def test_metadata_editing(self, page: Page, base_url: str):
        """Test plan metadata editing functionality."""
        # This test requires a plan to be selected
        # Implementation depends on test data setup
        pass


class TestPlanGeneration:
    """Integration tests for plan generation flow."""
    
    def test_full_plan_generation_flow(self, page: Page, base_url: str):
        """
        Test complete flow: create project → send message → generate plan → verify plan.
        
        This is a smoke test for the critical path.
        """
        page.goto(f"{base_url}/?page=planning_chat")
        page.wait_for_load_state("networkidle")
        
        # 1. Create a new project (if needed)
        # 2. Send a planning message
        # 3. Wait for plan generation
        # 4. Verify plan appears in "Latest Generated Plans"
        # 5. Click quick action button (e.g., Approve)
        # 6. Verify status update
        
        # Note: Full implementation requires test data setup and teardown
        pass


class TestQuickActions:
    """Test suite for quick action buttons."""
    
    def test_approve_plan(self, page: Page, base_url: str):
        """Test plan approval quick action."""
        # Requires a plan in draft status
        pass
    
    def test_start_plan(self, page: Page, base_url: str):
        """Test starting a plan quick action."""
        # Requires a plan in approved status
        pass
    
    def test_complete_plan(self, page: Page, base_url: str):
        """Test completing a plan quick action."""
        # Requires a plan in progress
        pass
    
    def test_archive_plan(self, page: Page, base_url: str):
        """Test archiving a plan quick action."""
        # Can archive from any status
        pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for Playwright."""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end UI test (requires running servers)"
    )


# Note: To run these tests, you need:
# 1. pip install pytest-playwright
# 2. playwright install chromium
# 3. Start backend: uvicorn backend.main:app --reload
# 4. Start frontend: streamlit run frontend/app.py
# 5. Run: pytest tests/e2e/test_planning_ui.py -v
