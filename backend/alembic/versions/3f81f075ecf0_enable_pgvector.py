"""enable pgvector

Revision ID: 3f81f075ecf0
Revises: 
Create Date: 2026-11-19 01:59:03.851021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '3f81f075ecf0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # Alembic creates this table before the first migration runs; lock it from Supabase's public Data API right away.
    op.execute('ALTER TABLE "alembic_version" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('ALTER TABLE "alembic_version" DISABLE ROW LEVEL SECURITY')
    op.execute("DROP EXTENSION IF EXISTS vector")
