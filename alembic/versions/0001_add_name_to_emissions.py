"""Add name column to emissions_calculations

Revision ID: 0001_add_name_to_emissions
Revises: None
Create Date: 2025-10-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_name_to_emissions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add an optional name column for saved calculations
    op.add_column('emissions_calculations', sa.Column('name', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('emissions_calculations', 'name')
