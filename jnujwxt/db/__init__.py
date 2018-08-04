from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..config import config

_db_engine = create_engine(config['jnujwxt']['database_url'])
DBSession = sessionmaker(bind=_db_engine)
