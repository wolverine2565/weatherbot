from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import select
from database.engine import engine

Session = sessionmaker(bind=engine)
session = Session()
