"""Thêm cột is_deleted vào Customer và Book

Revision ID: b862b2b3f510
Revises: 
Create Date: 2025-05-07 07:00:05.713006
"""
from alembic import op
import sqlalchemy as sa

revision = 'b862b2b3f510'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Thêm cột is_deleted với nullable=False và server_default='False'
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='False'))

    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='False'))

def downgrade():
    # Xóa cột is_deleted
    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.drop_column('is_deleted')

    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.drop_column('is_deleted')