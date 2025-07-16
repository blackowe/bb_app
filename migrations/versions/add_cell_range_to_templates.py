"""Add cell_range column to antigram_templates

Revision ID: add_cell_range_to_templates
Revises: create_pandas_storage_tables
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_cell_range_to_templates'
down_revision = 'create_pandas_storage_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Add cell_range column to antigram_templates table."""
    op.add_column('antigram_templates', sa.Column('cell_range', sa.String(50), nullable=True))


def downgrade():
    """Remove cell_range column from antigram_templates table."""
    op.drop_column('antigram_templates', 'cell_range') 