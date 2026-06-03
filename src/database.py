from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, User # Assuming User model is imported

def create_engine_and_session():
    # Replace with actual database connection string
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

def create_tables(engine):
    """
    Creates all defined tables in the database.
    This function handles schema creation/migration logic.
    """
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == '__main__':
    engine, SessionLocal = create_engine_and_session()
    try:
        create_tables(engine)
    except Exception as e:
        print(f"Error creating tables: {e}")
