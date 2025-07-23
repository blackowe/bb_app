"""merge heads

Revision ID: a5242d456a2e
Revises: add_cell_range_to_templates, drop_old_antigen_rules
Create Date: 2025-07-18 08:09:37.350092

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5242d456a2e'
down_revision = ('add_cell_range_to_templates', 'drop_old_antigen_rules')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
