from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Antigram(Base):
    __tablename__ = 'antigrams'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    lot_number = Column(String(50), nullable=False, unique=True)
    expiration_date = Column(Date, nullable=False)
    cells = relationship("Cell", back_populates="antigram", cascade="all, delete-orphan")

class Cell(Base):
    __tablename__ = 'cells'
    id = Column(Integer, primary_key=True)
    antigram_id = Column(Integer, ForeignKey('antigrams.id'), nullable=False)
    cell_number = Column(Integer, nullable=False)
    antigram = relationship("Antigram", back_populates="cells")
    reactions = relationship("Reaction", back_populates="cell", cascade="all, delete-orphan")

class Reaction(Base):
    __tablename__ = 'reactions'
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cells.id'), nullable=False)
    antigen = Column(String(50), nullable=False)
    reaction_value = Column(String(10), nullable=False)
    cell = relationship("Cell", back_populates="reactions")
