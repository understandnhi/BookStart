from alembic import op
import sqlalchemy as sa

revision = '78252adf85a6'
down_revision = 'b862b2b3f510'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.alter_column('is_deleted',
                             existing_type=sa.BOOLEAN(),
                             type_=sa.Integer(),
                             existing_nullable=False,
                             existing_server_default='0')

    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.alter_column('is_deleted',
                             existing_type=sa.BOOLEAN(),
                             type_=sa.Integer(),
                             existing_nullable=False,
                             existing_server_default='0')

def downgrade():
    with op.batch_alter_table('customer', schema=None) as batch_op:
        batch_op.alter_column('is_deleted',
                             existing_type=sa.Integer(),
                             type_=sa.BOOLEAN(),
                             existing_nullable=False,
                             existing_server_default='0')

    with op.batch_alter_table('book', schema=None) as batch_op:
        batch_op.alter_column('is_deleted',
                             existing_type=sa.Integer(),
                             type_=sa.BOOLEAN(),
                             existing_nullable=False,
                             existing_server_default='0')