"""
One-off script to create all database tables.
Run this from the `backend` folder with:

    python create_tables.py

This imports Base (from database.py) and all the model classes
(from models.py), then tells SQLAlchemy to create any tables
that don't exist yet in Postgres.
"""

from app.database import Base, engine
from app import models  # noqa: F401  (imported so the models register with Base)

print("Connecting to the database and creating tables...")

Base.metadata.create_all(bind=engine)

print("Done! Tables created (or already existed).")