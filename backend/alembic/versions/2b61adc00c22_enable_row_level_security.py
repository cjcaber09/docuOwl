"""enable row level security

Revision ID: 2b61adc00c22
Revises: 83380c96823e
Create Date: 2026-11-19 02:01:54.414902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '2b61adc00c22'
down_revision: Union[str, Sequence[str], None] = '83380c96823e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The seven Owl tables. (alembic_version was already locked by the "enable pgvector" migration.)
TABLES = [
    "users",
    "password_resets",
    "documents",
    "chunks",
    "conversations",
    "messages",
    "usage",
]


def upgrade() -> None:
    """Upgrade schema."""
    # With RLS on and no policies, Supabase's public Data API can't see these tables.
    # The backend owns the tables, so RLS does not restrict it.
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
