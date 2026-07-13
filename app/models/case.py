import datetime

from sqlalchemy import Column, String, DateTime, Text

from app.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True)
    query_name = Column(String, nullable=True)
    query_id_type = Column(String, nullable=True)
    query_id_value = Column(String, nullable=True)
    query_entity_type = Column(String, nullable=True)
    status = Column(String, default="open")
    matches_json = Column(Text, nullable=True)
    selected_match_id = Column(String, nullable=True)
    decision = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
