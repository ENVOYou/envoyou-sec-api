"""Initial database tables

Revision ID: 0001_initial_tables
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('job_title', sa.String(), nullable=True),
        sa.Column('avatar_url', sa.String(), nullable=True),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('email_verification_token', sa.String(), nullable=True),
        sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('two_factor_secret', sa.String(), nullable=True),
        sa.Column('two_factor_enabled', sa.Boolean(), nullable=True, default=False),
        sa.Column('auth_provider', sa.String(), nullable=True),
        sa.Column('auth_provider_id', sa.String(), nullable=True),
        sa.Column('plan', sa.String(), nullable=True),
        sa.Column('paddle_customer_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('prefix', sa.String(), nullable=False),
        sa.Column('permissions', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash'),
        sa.UniqueConstraint('prefix')
    )

    # Create emissions_calculations table
    op.create_table('emissions_calculations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('scope1_data', sa.JSON(), nullable=True),
        sa.Column('scope2_data', sa.JSON(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=False),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit_trail table
    op.create_table('audit_trail',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_file', sa.String(), nullable=False),
        sa.Column('calculation_version', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('company_cik', sa.String(), nullable=False),
        sa.Column('s3_path', sa.String(), nullable=True),
        sa.Column('gcs_path', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_trail_company_cik', 'audit_trail', ['company_cik'])


def downgrade() -> None:
    op.drop_index('ix_audit_trail_company_cik', 'audit_trail')
    op.drop_table('audit_trail')
    op.drop_table('emissions_calculations')
    op.drop_table('api_keys')
    op.drop_table('users')