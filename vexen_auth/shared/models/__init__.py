"""
Shared database models for vexen-auth.

This module re-exports all SQLAlchemy models from their original locations
for centralized import. This facilitates future migration management with
tools like Alembic.

Usage:
    from vexen_auth.shared.models import Base, UserCredentialModel, AuthTokenModel
"""

from vexen_auth.infraestructure.output.persistence.sqlalchemy.models.auth_token_model import (
	AuthTokenModel,
)
from vexen_auth.infraestructure.output.persistence.sqlalchemy.models.base import Base
from vexen_auth.infraestructure.output.persistence.sqlalchemy.models.user_credential_model import (
	UserCredentialModel,
)

__all__ = ["Base", "UserCredentialModel", "AuthTokenModel"]
