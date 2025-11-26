import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "06516267ad45"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    pass # NO foreign keys aquí. Se añaden en la siguiente migración.


def downgrade():
    op.drop_table("dataset_version")
