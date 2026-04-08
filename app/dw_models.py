import os
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, create_engine

load_dotenv()

dw_engine = create_engine(os.getenv("DATABASE_URL_DW"))

dw_metadata = MetaData(schema="dw")
