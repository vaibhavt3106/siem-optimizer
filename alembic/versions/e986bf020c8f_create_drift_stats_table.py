"""create drift_stats table

Revision ID: create_drift_stats
Revises: 
Create Date: 2025-08-28

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifiers, used by Alembic
revision = "create_drift_stats"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "drift_stats",
        sa.Column("id", sa.Integer, primary_key=True, index=True, autoincrement=True),
        sa.Column("rule_id", sa.String, index=True),
        sa.Column("fp_rate", sa.Float),
        sa.Column("tp_rate", sa.Float),
        sa.Column("alert_volume", sa.Integer),
        sa.Column("drift_score", sa.Float),
        sa.Column("last_checked", sa.DateTime, default=datetime.utcnow),
        sa.Column("drift_type", sa.String, nullable=False),  # "schema" or "rule"
    )


def downgrade():
    op.drop_table("drift_stats")
