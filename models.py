from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base
import json

Base = declarative_base()


class AntigramTemplate(Base):
    __tablename__ = "antigram_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    antigen_order = Column(String(255), nullable=False)  # Comma-separated antigen groups
    cell_count = Column(Integer, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "antigen_order": self.antigen_order.split(","),  # Convert back to list
            "cell_count": self.cell_count,
        }

class Antigram(Base):
    __tablename__ = 'antigrams'
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("antigram_templates.id"), nullable=False)
    lot_number = Column(String(50), nullable=False, unique=True)
    expiration_date = Column(Date, nullable=False)
    
    template = relationship("AntigramTemplate")  # Relationship with Template
    cells = relationship("Cell", back_populates="antigram", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "lot_number": self.lot_number,
            "cell_number": self.cell_number,
            "antigen": self.antigen,
            # Add any other relevant fields
        }

class Cell(Base):
    __tablename__ = 'cells'
    id = Column(Integer, primary_key=True)
    antigram_id = Column(Integer, ForeignKey('antigrams.id'), nullable=False)
    cell_number = Column(Integer, nullable=False)
    antigram = relationship("Antigram", back_populates="cells")
    reactions = relationship("Reaction", back_populates="cell", cascade="all, delete-orphan")
    patient_reactions = relationship("PatientReactionProfile", back_populates="cell", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "antigram_id": self.antigram_id,
            "cell_number": self.cell_number,
            "reactions": [reaction.to_dict() for reaction in self.reactions],
        }


class Reaction(Base):
    __tablename__ = 'reactions'
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cells.id'), nullable=False)
    antigen = Column(String(50), nullable=False)
    reaction_value = Column(String(10), nullable=False)
    cell = relationship("Cell", back_populates="reactions")

class PatientReactionProfile(Base):
    __tablename__ = 'patient_reaction_profiles'
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cells.id'), nullable=False, unique=True)
    patient_rxn = Column(String(10), nullable=False)  # The reaction entered by the user
    is_ruled_out = Column(Boolean, default=False)  # Whether this reaction has been used to rule out an antigen
    antigen = Column(String(50))  # The antigen that was ruled out by this reaction

    # Relationships
    cell = relationship("Cell", back_populates="patient_reactions")

    def to_dict(self):
        return {
            "id": self.id,
            "cell_id": self.cell_id,
            "cell_number": self.cell.cell_number,
            "lot_number": self.cell.antigram.lot_number,
            "patient_rxn": self.patient_rxn,
            "is_ruled_out": self.is_ruled_out,
            "antigen": self.antigen
        }

class AntigenRule(Base):
    __tablename__ = 'antigen_rules'
    id = Column(Integer, primary_key=True)
    target_antigen = Column(String(50), nullable=False)  # The antigen that can be ruled out
    rule_type = Column(String(50), nullable=False)  # e.g., "standard", "composite"
    rule_conditions = Column(String(500), nullable=False)  # JSON string of conditions
    rule_antigens = Column(String(255), nullable=False)  # Comma-separated list of antigens involved in the rule
    required_count = Column(Integer, nullable=False, default=1)  # Number of cells needed for rule-out
    description = Column(String(255))  # Optional description of the rule

    def to_dict(self):
        return {
            "id": self.id,
            "target_antigen": self.target_antigen,
            "rule_type": self.rule_type,
            "rule_conditions": json.loads(self.rule_conditions),
            "rule_antigens": self.rule_antigens.split(",") if self.rule_antigens else [],
            "required_count": self.required_count,
            "description": self.description
        }

    @property
    def conditions(self):
        """Helper property to get rule_conditions as a dict"""
        return json.loads(self.rule_conditions)

class Antigen(Base):
    __tablename__ = "antigens"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    system = Column(String(50), nullable=False)  # e.g., "Rh", "Kell", "Duffy", etc.

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "system": self.system
        }
