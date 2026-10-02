"""seed premium plans and star packages"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    plans = sa.table(
        "premium_plans",
        sa.column("months", sa.Integer),
        sa.column("is_enabled", sa.Boolean),
        sa.column("provider_supported", sa.Boolean),
        sa.column("price_stars", sa.Integer),
        sa.column("badge", sa.String),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        plans,
        [
            {"months": 1, "is_enabled": False, "provider_supported": False,
             "price_stars": None, "badge": None, "sort_order": 0},
            {"months": 3, "is_enabled": True, "provider_supported": True,
             "price_stars": 1100, "badge": None, "sort_order": 1},
            {"months": 6, "is_enabled": True, "provider_supported": True,
             "price_stars": 1650, "badge": None, "sort_order": 2},
            {"months": 12, "is_enabled": True, "provider_supported": True,
             "price_stars": 2750, "badge": "🔥", "sort_order": 3},
        ],
    )
    pk = sa.table(
        "star_packages",
        sa.column("amount", sa.Integer),
        sa.column("is_popular", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    amounts = [50, 100, 250, 500, 1000, 2500, 5000, 10000]
    op.bulk_insert(
        pk,
        [{"amount": a, "is_popular": a == 500, "sort_order": i} for i, a in enumerate(amounts)],
    )


def downgrade() -> None:
    op.execute("DELETE FROM star_packages")
    op.execute("DELETE FROM premium_plans")
