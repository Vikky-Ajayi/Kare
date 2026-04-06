"""Alembic migration environment."""

import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool, text
from alembic import context

from app.config import settings
from app.database import Base
from app.models import *  # noqa

# ── Build and validate DB URL ──────────────────────────────────
db_url = settings.DATABASE_URL

if not db_url or db_url == "sqlite:///./dev.db":
    print("\n❌  DATABASE_URL is not set in your .env file.\n")
    sys.exit(1)

# Normalize scheme
db_url = db_url.replace("postgres://", "postgresql://", 1)

# Force psycopg2 driver explicitly
if db_url.startswith("postgresql://") and "+psycopg2" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Ensure sslmode=require is in the URL
if "sslmode" not in db_url:
    separator = "&" if "?" in db_url else "?"
    db_url = db_url + separator + "sslmode=require"

# ── Alembic config ─────────────────────────────────────────────
config = context.config
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        db_url,
        poolclass=pool.NullPool,
        # No connect_args here — sslmode is in the URL
    )

    # Quick connectivity test with helpful error message
    try:
        with connectable.connect() as test_conn:
            test_conn.execute(text("SELECT 1"))
    except Exception as e:
        print(f"\n❌  Database connection failed: {e}")
        print(f"\n    URL used (password hidden): {db_url.split(':')[0]}://***@{db_url.split('@')[-1]}")
        print("    Check your DATABASE_URL in .env\n")
        sys.exit(1)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()