"""User id can be null in Flow

Revision ID: f5ee9749d1a6
Revises: 7843803a87b5
Create Date: 2023-10-18 23:12:27.297016

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5ee9749d1a6"
down_revision: str | None = "7843803a87b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    try:
        with op.batch_alter_table("flow", schema=None) as batch_op:
            batch_op.alter_column("user_id", existing_type=sa.CHAR(length=32), nullable=True)
    except Exception as e:
        print(e)
        pass

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    try:
        with op.batch_alter_table("flow", schema=None) as batch_op:
            batch_op.alter_column("user_id", existing_type=sa.CHAR(length=32), nullable=False)
    except Exception as e:
        print(e)
        pass

    # ### end Alembic commands ###
