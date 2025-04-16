"""create patient_reaction_profiles table

Revision ID: create_patient_reaction_profiles
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_patient_reaction_profiles'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create patient_reaction_profiles table
    op.create_table(
        'patient_reaction_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cell_id', sa.Integer(), nullable=False),
        sa.Column('patient_rxn', sa.String(10), nullable=False),
        sa.Column('is_ruled_out', sa.Boolean(), default=False),
        sa.Column('antigen', sa.String(50)),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['cell_id'], ['cells.id']),
        sa.UniqueConstraint('cell_id')
    )


def downgrade():
    # Drop patient_reaction_profiles table
    op.drop_table('patient_reaction_profiles') 