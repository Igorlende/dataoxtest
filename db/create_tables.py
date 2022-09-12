from sqlalchemy import Column, Integer, String, MetaData, Table, Text
from sqlalchemy import create_engine
from config import DB_STRING_CONNECTION_TO_ALCHEMY


engine = create_engine(DB_STRING_CONNECTION_TO_ALCHEMY, echo=False)
meta = MetaData()
ads = Table("ads", meta, Column("id", Integer, primary_key=True),
            Column("title", String(500)), Column("city", String(300)),
            Column("date", String(20)), Column("description", Text),
            Column("image", String(300)), Column("beds", String(50)),
            Column("price", String(50)), Column("currency", String(20)),
            Column("link", String(500)))

meta.create_all(engine)