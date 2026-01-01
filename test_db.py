from sqlalchemy import create_engine, text

# Replace with your actual password (URL-encoded if it has special characters)
DATABASE_URL = "postgresql://postgres.dzpphmfvlmbmcfnmjbks:gVrnTuz3vSy3imjY@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Test connection
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Connection successful:", result.fetchone())
except Exception as e:
    print("❌ Connection failed")
    print(e)
