"""Drop old antigen_rules table

Revision ID: drop_old_antigen_rules
Revises: create_pandas_storage_tables
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'drop_old_antigen_rules'
down_revision = 'create_pandas_storage_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Drop the old antigen_rules table."""
    op.drop_table('antigen_rules')


def downgrade():
    """Recreate the old antigen_rules table (if needed for rollback)."""
    op.create_table('antigen_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target_antigen', sa.String(length=50), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('rule_conditions', sa.String(length=500), nullable=False),
        sa.Column('rule_antigens', sa.String(length=255), nullable=False),
        sa.Column('required_count', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    ) 