"""Create pandas storage tables

Revision ID: create_pandas_storage_tables
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'create_pandas_storage_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create tables for storing pandas data."""
    # Create antigram_matrix_storage table
    op.create_table('antigram_matrix_storage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('antigram_id', sa.Integer(), nullable=False),
        sa.Column('matrix_data', sa.Text(), nullable=False),
        sa.Column('matrix_metadata', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('antigram_id')
    )
    
    # Create patient_reaction_storage table
    op.create_table('patient_reaction_storage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('antigram_id', sa.Integer(), nullable=False),
        sa.Column('cell_number', sa.Integer(), nullable=False),
        sa.Column('patient_reaction', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    """Drop the pandas storage tables."""
    op.drop_table('patient_reaction_storage')
    op.drop_table('antigram_matrix_storage') 