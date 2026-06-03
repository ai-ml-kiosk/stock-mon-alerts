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
    # Base.metadata.create_all() will now include last_login_at because it's defined in User model
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == '__main__':
    engine, SessionLocal = create_engine_and_session()
    create_tables(engine)
