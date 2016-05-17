from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///local_db.sqlite', echo=False)
Session = sessionmaker(bind=engine)


class AlbumRequestLog(Base):

    __tablename__ = 'AlbumRequestLogs'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    bounty = Column(String)
    filled = Column(Boolean)
    created_date = Column(String)

    def __repr__(self):
        return"""
id: {}
name: {}
bounty: {}
filled: {}""".format(self.id, self.name, self.bounty, self.filled)


def add_to_db(entry):
    session = Session()
    existing_request = session.query(AlbumRequestLog).filter_by(id=entry.id).first()
    if existing_request:
        existing_request.filled = entry.filled
        existing_request.bounty = entry.bounty
    else:
        session.add(entry)
    session.commit()
    return bool(existing_request)


def query_all_requests():
    session = Session()
    return session.query(AlbumRequestLog)


def organize_data_model(results):
    for album_request in results:
        name = album_request.name
        _id = album_request.id
        bounty = album_request.bounty
        filled = album_request.filled
        created = album_request.created_date

        new_log = AlbumRequestLog(id=_id, name=name, bounty=bounty, filled=filled,
                                  created_date=created)
        existing = add_to_db(new_log)  # Returns True if entry exists
        if existing:
            return existing

# Initialize SQL Tables and make connection to database
Base.metadata.create_all(engine)
