"""nullable in vertex build

Revision ID: e5a65ecff2cd
Revises: 4522eb831f5c
Create Date: 2024-09-02 14:55:19.707355

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.reflection import Inspector

from langflow.utils import migration

# revision identifiers, used by Alembic.
revision: str = "e5a65ecff2cd"
down_revision: str | None = "4522eb831f5c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    # ### commands auto generated by Alembic - please adjust! ###
    inspector = Inspector.from_engine(conn)  # type: ignore
    with op.batch_alter_table("vertex_build", schema=None) as batch_op:
        if migration.column_exists(table_name="vertex_build", column_name="id", conn=conn):
            columns = inspector.get_columns("vertex_build")
            id_column = next((column for column in columns if column["name"] == "id"), None)
            if id_column is not None and id_column["nullable"]:
                batch_op.alter_column("id", existing_type=sa.VARCHAR(), nullable=False)

    # ### end Alembic commands ###


def downgrade() -> None:
    conn = op.get_bind()
    # ### commands auto generated by Alembic - please adjust! ###
    inspector = Inspector.from_engine(conn)  # type: ignore
    with op.batch_alter_table("vertex_build", schema=None) as batch_op:
        if migration.column_exists(table_name="vertex_build", column_name="id", conn=conn):
            columns = inspector.get_columns("vertex_build")
            id_column = next((column for column in columns if column["name"] == "id"), None)
            if id_column is not None and not id_column["nullable"]:
                batch_op.alter_column("id", existing_type=sa.VARCHAR(), nullable=True)

    # ### end Alembic commands ###
