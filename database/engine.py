from sqlalchemy import create_engine
from database.models import Base

engine = create_engine('postgresql://postgres:admin123@localhost:5432/postgres', echo=True)

Base.metadata.drop_all(engine)