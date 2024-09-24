"""Add default_fields column

Revision ID: 1f4d6df60295
Revises: 6e7b581b5648
Create Date: 2024-04-29 09:49:46.864145

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "1f4d6df60295"
down_revision: str | None = "6e7b581b5648"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)  # type: ignore
    # ### commands auto generated by Alembic - please adjust! ###
    column_names = [column["name"] for column in inspector.get_columns("variable")]
    with op.batch_alter_table("variable", schema=None) as batch_op:
        if "default_fields" not in column_names:
            batch_op.add_column(sa.Column("default_fields", sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)  # type: ignore
    # ### commands auto generated by Alembic - please adjust! ###
    column_names = [column["name"] for column in inspector.get_columns("variable")]
    with op.batch_alter_table("variable", schema=None) as batch_op:
        if "default_fields" in column_names:
            batch_op.drop_column("default_fields")

    # ### end Alembic commands ###
