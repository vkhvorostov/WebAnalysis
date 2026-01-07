"""Initial company table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('city', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), nullable=False),
        sa.Column('cms', sa.Text(), nullable=True),
        sa.Column('language', sa.Text(), nullable=True),
        sa.Column('framework', sa.Text(), nullable=True),
        sa.Column('external_js', sa.Text(), nullable=True),
        sa.Column('social_links', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('companies')

