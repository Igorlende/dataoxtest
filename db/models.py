from sqlalchemy import Column, Integer, String, Text
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from db.config import DB_STRING_CONNECTION_TO_ALCHEMY


engine = create_engine(DB_STRING_CONNECTION_TO_ALCHEMY, echo=False)
Base = declarative_base()


class Ads(Base):

    __tablename__ = "ads"
    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    city = Column(String(300))
    date = Column(String(20))
    description = Column(Text)
    image = Column(String(300))
    beds = Column(String(50))
    price = Column(String(50))
    currency = Column(String(20))
    link = Column(String(500))

    def __repr__(self):
        return "Ads(id={0}, title={1}, city={2}, date={3}, description={4}, image={5}, beds={6}," \
               " price={7}, currency={8}), link={9}".format(self.id, self.title, self.city, self.date,
                                                  self.description, self.image, self.beds, self.price,
                                                  self.currency, self.link)

