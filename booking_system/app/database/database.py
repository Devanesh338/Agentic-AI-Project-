import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path

# Force absolute path to booking.db in project root using pathlib
current_dir = Path(__file__).parent.resolve()
project_root = current_dir.parent.parent.parent
db_path = (project_root / "booking.db").as_posix()

# Convert Windows path to SQLAlchemy URL format
db_url = f"sqlite:///{db_path}"
SQLALCHEMY_DATABASE_URL = os.getenv("BOOKING_DATABASE_URL", db_url)

# For SQLite, we need connect_args={"check_same_thread": False}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
