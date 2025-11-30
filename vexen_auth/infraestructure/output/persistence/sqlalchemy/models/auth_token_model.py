"""SQLAlchemy model for auth tokens."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AuthTokenModel(Base):
	"""Auth token model for database"""

	__tablename__ = "auth_tokens"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
	token: Mapped[str] = mapped_column(
		Text, nullable=False, unique=True, index=True
	)  # Hashed refresh token
	expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime, nullable=False, default=datetime.now
	)
	revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
