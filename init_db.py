from db import engine, Base
from models import Attempt

Base.metadata.create_all(bind=engine)
print("Tables created!")
