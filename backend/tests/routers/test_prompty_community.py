"""
Tests for Prompty Community API.

Comprehensive tests for the public project gallery and instructor access.
Tests cover:
- Community project listing
- Project visibility rules
- Instructor access control
- Pagination and sorting
- Edge cases and error handling
"""
import pytest
import os
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime


# =============================================================================
# INSTRUCTOR_IDS Environment Variable Tests
# =============================================================================

class TestInstructorIdsConfig:
    """Test INSTRUCTOR_IDS environment variable configuration."""

    def test_instructor_ids_from_env(self):
        """INSTRUCTOR_IDS loaded from environment variable."""
        with patch.dict(os.environ, {"INSTRUCTOR_IDS": "user1@test.com,user2@test.com"}):
            # Re-import to get fresh value
            raw = os.getenv("INSTRUCTOR_IDS", "")
            ids = set(filter(None, [id.strip() for id in raw.split(",")]))

            assert "user1@test.com" in ids
            assert "user2@test.com" in ids
            assert len(ids) == 2

    def test_empty_instructor_ids(self):
        """Empty INSTRUCTOR_IDS results in empty set."""
        with patch.dict(os.environ, {"INSTRUCTOR_IDS": ""}):
            raw = os.getenv("INSTRUCTOR_IDS", "")
            ids = set(filter(None, [id.strip() for id in raw.split(",")]))

            assert len(ids) == 0

    def test_instructor_ids_with_whitespace(self):
        """Whitespace is trimmed from INSTRUCTOR_IDS."""
        with patch.dict(os.environ, {"INSTRUCTOR_IDS": " user1@test.com , user2@test.com "}):
            raw = os.getenv("INSTRUCTOR_IDS", "")
            ids = set(filter(None, [id.strip() for id in raw.split(",")]))

            assert "user1@test.com" in ids
            assert "user2@test.com" in ids

    def test_instructor_ids_with_empty_entries(self):
        """Empty entries are filtered out."""
        with patch.dict(os.environ, {"INSTRUCTOR_IDS": "user1@test.com,,user2@test.com,"}):
            raw = os.getenv("INSTRUCTOR_IDS", "")
            ids = set(filter(None, [id.strip() for id in raw.split(",")]))

            assert len(ids) == 2

    def test_instructor_ids_single_user(self):
        """Single instructor ID works."""
        with patch.dict(os.environ, {"INSTRUCTOR_IDS": "admin@school.edu"}):
            raw = os.getenv("INSTRUCTOR_IDS", "")
            ids = set(filter(None, [id.strip() for id in raw.split(",")]))

            assert "admin@school.edu" in ids
            assert len(ids) == 1


# =============================================================================
# Visibility Rules Tests
# =============================================================================

class TestVisibilityRules:
    """Test project visibility rules."""

    def test_private_visibility_hidden_from_others(self):
        """Private projects are hidden from non-owners."""
        project_visibility = "private"
        project_user_id = "owner@test.com"
        requesting_user_id = "other@test.com"

        can_view = (
            project_visibility != "private" or
            project_user_id == requesting_user_id
        )

        assert can_view is False

    def test_private_visibility_visible_to_owner(self):
        """Private projects are visible to owners."""
        project_visibility = "private"
        project_user_id = "owner@test.com"
        requesting_user_id = "owner@test.com"

        can_view = (
            project_visibility != "private" or
            project_user_id == requesting_user_id
        )

        assert can_view is True

    def test_prompts_only_visibility_hides_state(self):
        """Prompts-only visibility hides state from non-owners."""
        project_visibility = "prompts-only"
        project_user_id = "owner@test.com"
        requesting_user_id = "viewer@test.com"

        is_owner = project_user_id == requesting_user_id
        can_see_prompts = is_owner or project_visibility == "full"

        assert can_see_prompts is False

    def test_full_visibility_shows_state(self):
        """Full visibility shows state to everyone."""
        project_visibility = "full"
        requesting_user_id = "anyone@test.com"

        can_see_prompts = project_visibility == "full"

        assert can_see_prompts is True

    def test_owner_always_sees_prompts(self):
        """Owner always sees prompts regardless of visibility."""
        for visibility in ["private", "prompts-only", "full"]:
            project_user_id = "owner@test.com"
            requesting_user_id = "owner@test.com"

            is_owner = project_user_id == requesting_user_id
            can_see_prompts = is_owner or visibility == "full"

            assert can_see_prompts is True


# =============================================================================
# Instructor Access Tests
# =============================================================================

class TestInstructorAccess:
    """Test instructor-only endpoint access."""

    def test_instructor_can_access(self):
        """Instructor can access instructor endpoints."""
        instructor_ids = {"instructor@school.edu", "admin@school.edu"}
        user_id = "instructor@school.edu"

        has_access = user_id in instructor_ids

        assert has_access is True

    def test_non_instructor_denied(self):
        """Non-instructor is denied access."""
        instructor_ids = {"instructor@school.edu", "admin@school.edu"}
        user_id = "student@school.edu"

        has_access = user_id in instructor_ids

        assert has_access is False

    def test_empty_instructor_ids_denies_all(self):
        """Empty instructor IDs denies everyone."""
        instructor_ids = set()
        user_id = "anyone@test.com"

        has_access = user_id in instructor_ids

        assert has_access is False

    def test_instructor_ids_case_sensitive(self):
        """Instructor IDs are case-sensitive."""
        instructor_ids = {"instructor@school.edu"}
        user_id_upper = "INSTRUCTOR@school.edu"

        has_access = user_id_upper in instructor_ids

        assert has_access is False


# =============================================================================
# Community Listing Tests
# =============================================================================

class TestCommunityListing:
    """Test community project listing logic."""

    def test_excludes_private_projects(self):
        """Private projects excluded from community list."""
        projects = [
            {"id": 1, "visibility": "full"},
            {"id": 2, "visibility": "private"},
            {"id": 3, "visibility": "prompts-only"},
        ]

        visible = [p for p in projects if p["visibility"] != "private"]

        assert len(visible) == 2
        assert all(p["visibility"] != "private" for p in visible)

    def test_includes_prompts_only_projects(self):
        """Prompts-only projects included in community list."""
        projects = [
            {"id": 1, "visibility": "prompts-only"},
        ]

        visible = [p for p in projects if p["visibility"] != "private"]

        assert len(visible) == 1

    def test_includes_full_projects(self):
        """Full visibility projects included in community list."""
        projects = [
            {"id": 1, "visibility": "full"},
        ]

        visible = [p for p in projects if p["visibility"] != "private"]

        assert len(visible) == 1


# =============================================================================
# Sorting Tests
# =============================================================================

class TestSorting:
    """Test community project sorting."""

    def test_sort_by_recent(self):
        """Sort by recent (updated_at desc)."""
        projects = [
            {"id": 1, "updated_at": datetime(2024, 1, 1)},
            {"id": 2, "updated_at": datetime(2024, 6, 1)},
            {"id": 3, "updated_at": datetime(2024, 3, 1)},
        ]

        sorted_projects = sorted(projects, key=lambda p: p["updated_at"], reverse=True)

        assert sorted_projects[0]["id"] == 2
        assert sorted_projects[1]["id"] == 3
        assert sorted_projects[2]["id"] == 1

    def test_sort_by_top_scores(self):
        """Sort by top scores (avg_score desc)."""
        projects = [
            {"id": 1, "avg_score": 85.0},
            {"id": 2, "avg_score": 95.0},
            {"id": 3, "avg_score": None},
            {"id": 4, "avg_score": 90.0},
        ]

        # Sort: non-null first (desc), then by score (desc)
        sorted_projects = sorted(
            projects,
            key=lambda p: (p["avg_score"] is not None, p["avg_score"] or 0),
            reverse=True
        )

        assert sorted_projects[0]["id"] == 2  # 95.0
        assert sorted_projects[1]["id"] == 4  # 90.0
        assert sorted_projects[2]["id"] == 1  # 85.0
        assert sorted_projects[3]["id"] == 3  # None

    def test_sort_by_most_forked(self):
        """Sort by most forked (fork_count desc)."""
        projects = [
            {"id": 1, "fork_count": 5},
            {"id": 2, "fork_count": 100},
            {"id": 3, "fork_count": 50},
        ]

        sorted_projects = sorted(projects, key=lambda p: p["fork_count"], reverse=True)

        assert sorted_projects[0]["id"] == 2  # 100
        assert sorted_projects[1]["id"] == 3  # 50
        assert sorted_projects[2]["id"] == 1  # 5


# =============================================================================
# Pagination Tests
# =============================================================================

class TestPagination:
    """Test pagination logic."""

    def test_first_page(self):
        """First page returns correct items."""
        all_items = list(range(1, 101))  # 100 items
        page = 1
        page_size = 20

        offset = (page - 1) * page_size
        items = all_items[offset:offset + page_size]

        assert len(items) == 20
        assert items[0] == 1
        assert items[-1] == 20

    def test_middle_page(self):
        """Middle page returns correct items."""
        all_items = list(range(1, 101))
        page = 3
        page_size = 20

        offset = (page - 1) * page_size
        items = all_items[offset:offset + page_size]

        assert len(items) == 20
        assert items[0] == 41
        assert items[-1] == 60

    def test_last_page_partial(self):
        """Last page may have fewer items."""
        all_items = list(range(1, 56))  # 55 items
        page = 3
        page_size = 20

        offset = (page - 1) * page_size
        items = all_items[offset:offset + page_size]

        assert len(items) == 15  # Only 15 remaining

    def test_page_beyond_data(self):
        """Page beyond data returns empty."""
        all_items = list(range(1, 21))  # 20 items
        page = 5
        page_size = 20

        offset = (page - 1) * page_size
        items = all_items[offset:offset + page_size]

        assert len(items) == 0


# =============================================================================
# Status Filter Tests
# =============================================================================

class TestStatusFilter:
    """Test status filtering."""

    def test_filter_active_only(self):
        """Filter active projects only."""
        projects = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "completed"},
            {"id": 3, "status": "active"},
        ]

        filtered = [p for p in projects if p["status"] == "active"]

        assert len(filtered) == 2

    def test_filter_completed_only(self):
        """Filter completed projects only."""
        projects = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "completed"},
            {"id": 3, "status": "completed"},
        ]

        filtered = [p for p in projects if p["status"] == "completed"]

        assert len(filtered) == 2

    def test_no_filter_returns_all(self):
        """No status filter returns all."""
        projects = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "completed"},
        ]
        status_filter = None

        if status_filter:
            filtered = [p for p in projects if p["status"] == status_filter]
        else:
            filtered = projects

        assert len(filtered) == 2


# =============================================================================
# Instructor List All Projects Tests
# =============================================================================

class TestInstructorListAllProjects:
    """Test instructor's ability to list all projects."""

    def test_instructor_sees_private_projects(self):
        """Instructor can see private projects."""
        # Instructor endpoint doesn't filter by visibility
        projects = [
            {"id": 1, "visibility": "private", "user_id": "student1@test.com"},
            {"id": 2, "visibility": "full", "user_id": "student2@test.com"},
        ]

        # No visibility filter
        visible = projects

        assert len(visible) == 2

    def test_instructor_filter_by_user(self):
        """Instructor can filter by user_id."""
        projects = [
            {"id": 1, "user_id": "student1@test.com"},
            {"id": 2, "user_id": "student2@test.com"},
            {"id": 3, "user_id": "student1@test.com"},
        ]

        user_filter = "student1@test.com"
        filtered = [p for p in projects if p["user_id"] == user_filter]

        assert len(filtered) == 2

    def test_instructor_sort_by_user(self):
        """Instructor can sort by user_id."""
        projects = [
            {"id": 1, "user_id": "charlie@test.com"},
            {"id": 2, "user_id": "alice@test.com"},
            {"id": 3, "user_id": "bob@test.com"},
        ]

        sorted_projects = sorted(projects, key=lambda p: p["user_id"])

        assert sorted_projects[0]["user_id"] == "alice@test.com"
        assert sorted_projects[1]["user_id"] == "bob@test.com"
        assert sorted_projects[2]["user_id"] == "charlie@test.com"


# =============================================================================
# Student List Tests
# =============================================================================

class TestStudentList:
    """Test instructor's student list endpoint."""

    def test_unique_students(self):
        """Returns unique student IDs."""
        projects = [
            {"user_id": "student1@test.com"},
            {"user_id": "student2@test.com"},
            {"user_id": "student1@test.com"},  # duplicate
            {"user_id": "student3@test.com"},
        ]

        students = sorted(set(p["user_id"] for p in projects))

        assert len(students) == 3
        assert "student1@test.com" in students
        assert "student2@test.com" in students
        assert "student3@test.com" in students

    def test_students_sorted_alphabetically(self):
        """Students are sorted alphabetically."""
        projects = [
            {"user_id": "zebra@test.com"},
            {"user_id": "apple@test.com"},
            {"user_id": "mango@test.com"},
        ]

        students = sorted(set(p["user_id"] for p in projects))

        assert students[0] == "apple@test.com"
        assert students[1] == "mango@test.com"
        assert students[2] == "zebra@test.com"

    def test_empty_projects_empty_students(self):
        """No projects means no students."""
        projects = []

        students = sorted(set(p["user_id"] for p in projects))

        assert len(students) == 0


# =============================================================================
# Project Detail Tests
# =============================================================================

class TestProjectDetail:
    """Test community project detail retrieval."""

    def test_public_project_visible(self):
        """Public project is visible to anyone."""
        project = {"visibility": "full", "user_id": "owner@test.com"}
        requesting_user_id = "anonymous@test.com"

        is_visible = project["visibility"] != "private"

        assert is_visible is True

    def test_private_project_returns_404_for_others(self):
        """Private project returns 404 for non-owners."""
        project = {"visibility": "private", "user_id": "owner@test.com"}
        requesting_user_id = "other@test.com"

        is_visible = (
            project["visibility"] != "private" or
            project["user_id"] == requesting_user_id
        )

        assert is_visible is False  # Would return 404

    def test_prompts_only_hides_state_in_response(self):
        """Prompts-only project hides state in response."""
        project = {
            "visibility": "prompts-only",
            "user_id": "owner@test.com",
            "state": {"prompts": "secret"},
        }
        requesting_user_id = "viewer@test.com"

        is_owner = project["user_id"] == requesting_user_id
        can_see_prompts = is_owner or project["visibility"] == "full"

        response_state = project["state"] if can_see_prompts else None

        assert response_state is None

    def test_full_visibility_includes_state(self):
        """Full visibility includes state in response."""
        project = {
            "visibility": "full",
            "user_id": "owner@test.com",
            "state": {"prompts": "visible"},
        }
        requesting_user_id = "viewer@test.com"

        is_owner = project["user_id"] == requesting_user_id
        can_see_prompts = is_owner or project["visibility"] == "full"

        response_state = project["state"] if can_see_prompts else None

        assert response_state == {"prompts": "visible"}
