# tests/integration/test_user_db.py

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from app.models import User
from app.hashing import hash_password, verify_password
from app.schemas import UserCreate, UserRead


def make_user(session, username="alice", email="alice@example.com", password="secret123"):
    data = UserCreate(username=username, email=email, password=password)
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    session.add(user)
    session.flush()
    return user


class TestUserCreation:
    def test_create_user_persists(self, db_session):
        user = make_user(db_session)
        fetched = db_session.query(User).filter_by(username="alice").first()
        assert fetched is not None
        assert fetched.email == "alice@example.com"

    def test_created_at_is_set(self, db_session):
        user = make_user(db_session)
        assert user.created_at is not None

    def test_password_hash_stored_not_plaintext(self, db_session):
        user = make_user(db_session, password="mypassword")
        assert user.password_hash != "mypassword"
        assert verify_password("mypassword", user.password_hash)

    def test_user_read_schema_from_orm(self, db_session):
        user = make_user(db_session)
        schema = UserRead.model_validate(user)
        assert schema.username == "alice"
        assert schema.email == "alice@example.com"
        assert schema.id is not None


class TestUserUniqueness:
    def test_duplicate_username_raises(self, db_session):
        make_user(db_session, username="dupuser", email="first@example.com")
        with pytest.raises(IntegrityError):
            make_user(db_session, username="dupuser", email="second@example.com")

    def test_duplicate_email_raises(self, db_session):
        make_user(db_session, username="user1", email="shared@example.com")
        with pytest.raises(IntegrityError):
            make_user(db_session, username="user2", email="shared@example.com")


class TestEmailValidation:
    def test_invalid_email_rejected_by_schema(self, db_session):
        with pytest.raises(ValidationError):
            UserCreate(username="baduser", email="not-valid", password="pass")

    def test_missing_at_sign_rejected(self, db_session):
        with pytest.raises(ValidationError):
            UserCreate(username="baduser", email="userexample.com", password="pass")

    def test_valid_email_accepted(self, db_session):
        data = UserCreate(username="gooduser", email="good@example.com", password="pass")
        assert data.email == "good@example.com"
