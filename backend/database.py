import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import tcc_ensure_database_guards

# Retrieves the PostgreSQL connection string injected by Docker Compose
# Default fallback is provided for local development/testing out of Docker
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin_tcc:SecurePassword123!@localhost:5432/travel_crm"
)

# pool_pre_ping=True checks the health of the connection before running queries,
# preventing "Server closed connection unexpectedly" errors after periods of inactivity.
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

# SessionLocal instances will be the transactional handles used by the API routes
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Called on system startup.
    Runs relational structural guards and verifies table alignments.
    """
    try:
        print("[DATABASE] Running automatic structural validation guards...")
        tcc_ensure_database_guards(engine)
        print("[DATABASE] Table verification and schema guards executed successfully.")
    except Exception as e:
        print(f"[DATABASE] CRITICAL: Schema migration guard failed initialization: {e}")
        raise e
