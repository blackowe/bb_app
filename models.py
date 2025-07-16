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
    cell_range = Column(String(50), nullable=True)  # JSON string of [start, end] cell numbers

    def to_dict(self):
        cell_range_list = None
        if self.cell_range:
            try:
                cell_range_list = json.loads(self.cell_range)
            except (json.JSONDecodeError, TypeError):
                cell_range_list = None
        
        return {
            "id": self.id,
            "name": self.name,
            "antigen_order": self.antigen_order.split(","),  # Convert back to list
            "cell_count": self.cell_count,
            "cell_range": cell_range_list,
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
