# create a connection to Postgres, and give the rest of the app a way to "borrow" that connection when needed.


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load variables from the .env file into the environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError(
        "DATABASE_URL is not set. Make sure you have a .env file in the "
        "backend folder with a DATABASE_URL line in it."
    )

# The "engine" is the actual connection to Postgres
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory that creates new database "conversations" (sessions)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class every database model (table) will inherit from
Base = declarative_base()


def get_db():
    """
    Gives a database session to a route, and guarantees it gets closed
    afterward, even if an error happens. FastAPI calls this automatically
    whenever a route depends on it.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()