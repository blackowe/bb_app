from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

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

    # Relationships
    cell = relationship("Cell", back_populates="patient_reactions")

    def to_dict(self):
        return {
            "id": self.id,
            "cell_id": self.cell_id,
            "cell_number": self.cell.cell_number,
            "lot_number": self.cell.antigram.lot_number,
            "patient_rxn": self.patient_rxn,
        }

class AntigenPair(Base):
    __tablename__ = 'antigen_pairs'
    id = Column(Integer, primary_key=True)
    antigen1 = Column(String(50), nullable=False)
    antigen2 = Column(String(50), nullable=True)  # Made nullable for single antigen rules
    rule_type = Column(String(20), nullable=False)  # 'homozygous', 'heterozygous', or 'single'
    required_count = Column(Integer, nullable=False, default=3)  # Number of cells needed for rule-out

    def to_dict(self):
        return {
            "id": self.id,
            "antigen1": self.antigen1,
            "antigen2": self.antigen2,
            "rule_type": self.rule_type,
            "required_count": self.required_count
        }

class AntigenRuleOut(Base):
    __tablename__ = 'antigen_rule_outs'
    id = Column(Integer, primary_key=True)
    antigen = Column(String(50), nullable=False)
    cell_id = Column(Integer, ForeignKey('cells.id'), nullable=False)
    rule_type = Column(String(20), nullable=False)  # 'homozygous' or 'heterozygous'
    paired_antigen = Column(String(50))  # The paired antigen if this is part of a pair
    patient_reaction = Column(String(10), nullable=False)
    cell_reaction = Column(String(10), nullable=False)
    paired_reaction = Column(String(10))  # The reaction of the paired antigen
    
    # Relationships
    cell = relationship("Cell", backref="rule_outs")

    def to_dict(self):
        return {
            "id": self.id,
            "antigen": self.antigen,
            "cell_id": self.cell_id,
            "rule_type": self.rule_type,
            "paired_antigen": self.paired_antigen,
            "patient_reaction": self.patient_reaction,
            "cell_reaction": self.cell_reaction,
            "paired_reaction": self.paired_reaction,
            "cell": {
                "cell_number": self.cell.cell_number,
                "lot_number": self.cell.antigram.lot_number if self.cell.antigram else None
            }
        }
