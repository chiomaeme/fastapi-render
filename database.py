"""This module contains database configuration"""
import os
from sqlmodel import Session, SQLModel, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    """This function initializes the database"""
    SQLModel.metadata.create_all(bind=engine)


def get_session():
    """This function is used to create a sqlmodel session"""
    with Session(engine) as session:
        yield session
