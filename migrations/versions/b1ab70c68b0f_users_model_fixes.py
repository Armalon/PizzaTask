"""Users model fixes

Revision ID: b1ab70c68b0f
Revises: d7d78fc8c876
Create Date: 2020-07-21 17:12:31.092465

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1ab70c68b0f'
down_revision = 'd7d78fc8c876'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_user_address', table_name='user')
    op.create_index(op.f('ix_user_address'), 'user', ['address'], unique=False)
    op.drop_index('ix_user_username', table_name='user')
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.create_index('ix_user_username', 'user', ['username'], unique=1)
    op.drop_index(op.f('ix_user_address'), table_name='user')
    op.create_index('ix_user_address', 'user', ['address'], unique=1)
    # ### end Alembic commands ###
