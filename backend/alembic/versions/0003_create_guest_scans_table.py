"""replace history.json with guest_scans table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'guest_scans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guest_id', sa.String(), nullable=False),
        sa.Column('ip', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=True),
        sa.Column(
            'scanned_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'), # Changed from NOW()
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id')
    )
    # Indexes on the exact columns used in rate limiting queries
    op.create_index('ix_guest_scans_guest_id', 'guest_scans', ['guest_id'])
    op.create_index('ix_guest_scans_ip', 'guest_scans', ['ip'])
    op.create_index('ix_guest_scans_scanned_at', 'guest_scans', ['scanned_at'])


def downgrade() -> None:
    op.drop_index('ix_guest_scans_scanned_at', table_name='guest_scans')
    op.drop_index('ix_guest_scans_ip', table_name='guest_scans')
    op.drop_index('ix_guest_scans_guest_id', table_name='guest_scans')
    op.drop_table('guest_scans')