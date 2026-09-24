
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./real_estate.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Property(Base):
    __tablename__ = "properties"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    price_eur = Column(Float)
    location = Column(String)
    meta = Column(String)
    is_off_market = Column(Boolean, default=False)
    description = Column(String)

class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True)
    name = Column(String, nullable=True)
    budget = Column(String, nullable=True)
    goal = Column(String, nullable=True)
    is_qualified = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)
