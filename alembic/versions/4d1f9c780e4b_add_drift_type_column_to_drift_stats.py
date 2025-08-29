"""add drift_type column to drift_stats"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d1f9c780e4b"
down_revision = "adaed955754a"  # update if different
branch_labels = None
depends_on = None


def upgrade():
    # Add drift_type column
    op.add_column("drift_stats", sa.Column("drift_type", sa.String(), nullable=True))

    # Backfill: set "schema" if rule_id is NULL, else "rule"
    op.execute("""
        UPDATE drift_stats
        SET drift_type = CASE
            WHEN rule_id IS NULL THEN 'schema'
            ELSE 'rule'
        END
    """)

    # Make column NOT NULL
    op.alter_column("drift_stats", "drift_type", nullable=False)


def downgrade():
    op.drop_column("drift_stats", "drift_type")
