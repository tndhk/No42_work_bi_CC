"""Tests for GroupMemberRepository."""
import pytest
import asyncio

from app.repositories.group_member_repository import GroupMemberRepository


class TestGroupMemberRepository:
    """Test GroupMemberRepository operations."""

    @pytest.fixture
    def repo(self):
        return GroupMemberRepository()

    @pytest.fixture
    def dynamodb_with_table(self, dynamodb_tables):
        tables, dynamodb = dynamodb_tables
        return dynamodb

    def test_add_member(self, repo, dynamodb_with_table):
        """Test adding a member to a group."""
        member = asyncio.get_event_loop().run_until_complete(
            repo.add_member("group_1", "user_1", dynamodb_with_table)
        )
        assert member.group_id == "group_1"
        assert member.user_id == "user_1"
        assert member.added_at is not None

    def test_is_member_true(self, repo, dynamodb_with_table):
        """Test is_member returns True for existing member."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repo.add_member("group_1", "user_1", dynamodb_with_table))
        result = loop.run_until_complete(repo.is_member("group_1", "user_1", dynamodb_with_table))
        assert result is True

    def test_is_member_false(self, repo, dynamodb_with_table):
        """Test is_member returns False for non-member."""
        result = asyncio.get_event_loop().run_until_complete(
            repo.is_member("group_1", "user_999", dynamodb_with_table)
        )
        assert result is False

    def test_list_members(self, repo, dynamodb_with_table):
        """Test listing members of a group."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repo.add_member("group_1", "user_1", dynamodb_with_table))
        loop.run_until_complete(repo.add_member("group_1", "user_2", dynamodb_with_table))
        members = loop.run_until_complete(repo.list_members("group_1", dynamodb_with_table))
        assert len(members) == 2
        user_ids = {m.user_id for m in members}
        assert user_ids == {"user_1", "user_2"}

    def test_list_members_empty(self, repo, dynamodb_with_table):
        """Test listing members of empty group."""
        members = asyncio.get_event_loop().run_until_complete(
            repo.list_members("group_empty", dynamodb_with_table)
        )
        assert len(members) == 0

    def test_remove_member(self, repo, dynamodb_with_table):
        """Test removing a member from a group."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repo.add_member("group_1", "user_1", dynamodb_with_table))
        loop.run_until_complete(repo.remove_member("group_1", "user_1", dynamodb_with_table))
        result = loop.run_until_complete(repo.is_member("group_1", "user_1", dynamodb_with_table))
        assert result is False

    def test_list_groups_for_user(self, repo, dynamodb_with_table):
        """Test listing groups a user belongs to."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repo.add_member("group_1", "user_1", dynamodb_with_table))
        loop.run_until_complete(repo.add_member("group_2", "user_1", dynamodb_with_table))
        loop.run_until_complete(repo.add_member("group_3", "user_2", dynamodb_with_table))
        groups = loop.run_until_complete(repo.list_groups_for_user("user_1", dynamodb_with_table))
        assert len(groups) == 2
        assert set(groups) == {"group_1", "group_2"}

    def test_list_groups_for_user_empty(self, repo, dynamodb_with_table):
        """Test listing groups for user with no groups."""
        groups = asyncio.get_event_loop().run_until_complete(
            repo.list_groups_for_user("user_nobody", dynamodb_with_table)
        )
        assert len(groups) == 0

    def test_add_duplicate_member(self, repo, dynamodb_with_table):
        """Test adding same member twice doesn't create duplicates."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(repo.add_member("group_1", "user_1", dynamodb_with_table))
        loop.run_until_complete(repo.add_member("group_1", "user_1", dynamodb_with_table))
        members = loop.run_until_complete(repo.list_members("group_1", dynamodb_with_table))
        assert len(members) == 1
