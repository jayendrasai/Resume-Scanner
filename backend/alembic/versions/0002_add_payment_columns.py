"""add payment columns to users
Revision ID: 0002
Revises: 0001
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('razorpay_customer_id', sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('razorpay_order_id', sa.String(), nullable=True)
        )

    op.create_index(
        'ix_users_razorpay_order_id',
        'users', ['razorpay_order_id'], unique=True
    )

def downgrade() -> None:
    op.drop_index('ix_users_razorpay_order_id', table_name='users')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('razorpay_order_id')
        batch_op.drop_column('razorpay_customer_id')