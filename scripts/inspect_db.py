from sqlalchemy import text

from app.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
    tables = [row[0] for row in result]
    print('Tables in database:', tables)

    # Check for patient_health_notes table
    if 'patient_health_notes' in tables:
        result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'patient_health_notes'"))
        columns = [(row[0], row[1]) for row in result]
        print('patient_health_notes columns:', columns)
