# tests/unit/test_user.py

import pytest
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from app.hashing import hash_password, verify_password
from app.schemas import UserCreate, UserRead
from app.database import get_db
from datetime import datetime, timezone


class TestHashing:
    def test_hash_returns_string(self):
        result = hash_password("secret")
        assert isinstance(result, str)

    def test_hash_contains_salt_and_digest(self):
        result = hash_password("secret")
        parts = result.split("$")
        assert len(parts) == 2
        salt, digest = parts
        assert len(salt) == 32   # 16 bytes as hex
        assert len(digest) == 64  # sha3_256 hex digest

    def test_same_password_produces_different_hashes(self):
        h1 = hash_password("password")
        h2 = hash_password("password")
        assert h1 != h2

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


class TestUserCreateSchema:
    def test_valid_user_create(self):
        user = UserCreate(username="alice", email="alice@example.com", password="secret123")
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.password == "secret123"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="bob", email="not-an-email", password="secret123")

    def test_missing_username_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(email="alice@example.com", password="secret123")

    def test_missing_password_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="alice@example.com")

    def test_missing_email_raises(self):
        with pytest.raises(ValidationError):
            UserCreate(username="alice", password="secret123")


class TestUserReadSchema:
    def test_valid_user_read(self):
        now = datetime.now(timezone.utc)
        user = UserRead(id=1, username="alice", email="alice@example.com", created_at=now)
        assert user.id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.created_at == now

    def test_user_read_from_orm(self):
        class FakeUser:
            id = 42
            username = "bob"
            email = "bob@example.com"
            created_at = datetime.now(timezone.utc)

        user = UserRead.model_validate(FakeUser())
        assert user.id == 42
        assert user.username == "bob"


class TestGetDb:
    def test_get_db_yields_session_and_closes(self):
        mock_session = MagicMock()
        with patch("app.database.SessionLocal", return_value=mock_session):
            gen = get_db()
            db = next(gen)
            assert db is mock_session
            with pytest.raises(StopIteration):
                next(gen)
            mock_session.close.assert_called_once()
