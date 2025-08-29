from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers
revision = "create_rules_and_history"
down_revision = "9d7a31c90a42"  # ← your current head (check `alembic current`)
branch_labels = None
depends_on = None


def upgrade():
    # Create rules table
    op.create_table(
        "rules",
        sa.Column("id", sa.String(), primary_key=True, index=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), default=datetime.utcnow),
        sa.Column("updated_at", sa.DateTime(), default=datetime.utcnow),
    )

    # Create rule_history table
    op.create_table(
        "rule_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_id", sa.String(), sa.ForeignKey("rules.id"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),  # created, autofix, apply_fix, rollback
        sa.Column("timestamp", sa.DateTime(), default=datetime.utcnow),
    )


def downgrade():
    op.drop_table("rule_history")
    op.drop_table("rules")

