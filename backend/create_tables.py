from backend.database import engine
from backend.models import Base

def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()
