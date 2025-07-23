from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, Text
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


class AntibodyRule(Base):
    """
    New antibody rule model to replace the old AntigenRule.
    Supports all rule types: ABSpecificRO, Homo, Hetero, SingleAG, LowF
    """
    __tablename__ = 'antibody_rules'
    
    id = Column(Integer, primary_key=True)
    rule_type = Column(String(50), nullable=False)  # 'abspecific', 'homo', 'hetero', 'single', 'lowf'
    target_antigen = Column(String(50), nullable=False)  # The antigen that can be ruled out
    rule_data = Column(Text, nullable=False)  # JSON string with rule-specific data
    description = Column(String(255))  # Optional description
    enabled = Column(Boolean, default=True)  # Whether the rule is active

    def to_dict(self):
        return {
            "id": self.id,
            "rule_type": self.rule_type,
            "target_antigen": self.target_antigen,
            "rule_data": json.loads(self.rule_data),
            "description": self.description,
            "enabled": self.enabled
        }

    @property
    def data(self):
        """Helper property to get rule_data as a dict"""
        return json.loads(self.rule_data)


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
