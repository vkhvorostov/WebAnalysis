"""add domain_created to companies_data

Revision ID: f7e2a9b1c3d4
Revises: 0c09354fedd8
Create Date: 2026-04-20

"""
from alembic import op
import sqlalchemy as sa


revision = "f7e2a9b1c3d4"
down_revision = "0c09354fedd8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies_data",
        sa.Column("domain_created", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies_data", "domain_created")
