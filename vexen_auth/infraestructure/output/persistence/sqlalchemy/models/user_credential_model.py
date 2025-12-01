"""SQLAlchemy model for user credentials."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserCredentialModel(Base):
	"""User credential model for database"""

	__tablename__ = "user_credentials"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	user_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
	password_hash: Mapped[str] = mapped_column(Text, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
	updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
