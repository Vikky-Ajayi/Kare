from app.database import engine, Base
from sqlalchemy import text

# Drop all tables
with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.commit()

print("Database reset complete")