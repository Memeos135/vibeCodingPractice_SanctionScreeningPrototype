import datetime

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Sanction(Base):
    __tablename__ = "sanctions"

    id = Column(String, primary_key=True)
    caption = Column(String, nullable=False)
    schema_type = Column(String, nullable=False)
    target = Column(Boolean, default=True, nullable=False)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    last_change = Column(DateTime, nullable=True)
    country = Column(String, nullable=True)
    program_id = Column(String, nullable=True)
    topics = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    names = relationship(
        "SanctionName", back_populates="sanction", cascade="all, delete-orphan",
    )
    referents = relationship(
        "SanctionReferent", back_populates="sanction", cascade="all, delete-orphan",
    )


Index("ix_sanctions_schema_type", Sanction.schema_type)


class SanctionName(Base):
    __tablename__ = "sanction_names"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sanction_id = Column(
        String, ForeignKey("sanctions.id", ondelete="CASCADE"), nullable=False,
    )
    name = Column(String, nullable=False)
    name_type = Column(String, nullable=False)

    sanction = relationship("Sanction", back_populates="names")


Index("ix_sanction_names_name", SanctionName.name)


class SanctionReferent(Base):
    __tablename__ = "sanction_referents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sanction_id = Column(
        String, ForeignKey("sanctions.id", ondelete="CASCADE"), nullable=False,
    )
    referent = Column(String, nullable=False)
    source = Column(String, nullable=True)

    sanction = relationship("Sanction", back_populates="referents")


Index("ix_sanction_referents_referent", SanctionReferent.referent)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    entity_count = Column(Integer, default=0)


from app.models.case import Case

__all__ = [
    "Sanction",
    "SanctionName",
    "SanctionReferent",
    "Dataset",
    "Case",
]
