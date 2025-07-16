import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime
import json
import logging
from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.orm import declarative_base
from models import Base

# Set up logging
logger = logging.getLogger(__name__)

class PandasAntigramManager:
    """
    Manages antigram data using pandas DataFrames for matrix-style storage.
    Provides efficient operations for antibody identification and cell finding.
    Now includes database persistence for data durability.
    """
    
    def __init__(self, db_session=None):
        self.antigram_matrices: Dict[int, pd.DataFrame] = {}
        self.antigram_metadata: Dict[int, Dict] = {}
        self.patient_reactions: pd.DataFrame = pd.DataFrame()
        self.db_session = db_session
        
    def create_antigram_matrix(self, antigram_id: int, lot_number: str, 
                              template_name: str, antigens: List[str], 
                              cells_data: List[Dict], expiration_date: date) -> pd.DataFrame:
        """
        Create a pandas DataFrame matrix from antigram data.
        
        Args:
            antigram_id: Unique identifier for the antigram
            lot_number: Lot number string
            template_name: Name of the template used
            antigens: List of antigen names in order
            cells_data: List of cell data with reactions
            expiration_date: Expiration date
            
        Returns:
            pandas.DataFrame: Matrix with cells as index and antigens as columns
        """
        # Create matrix data
        matrix_data = []
        cell_numbers = []
        
        for cell in cells_data:
            cell_number = cell['cell_number']
            cell_numbers.append(cell_number)
            
            # Create row for this cell
            row_data = {}
            for antigen in antigens:
                reaction = cell['reactions'].get(antigen, '-')
                row_data[antigen] = reaction
            
            matrix_data.append(row_data)
        
        # Create DataFrame
        df = pd.DataFrame(matrix_data, index=cell_numbers)
        df.index.name = 'cell_number'
        
        # Store metadata
        self.antigram_metadata[antigram_id] = {
            'lot_number': lot_number,
            'template_name': template_name,
            'antigens': antigens,
            'expiration_date': expiration_date,
            'cell_count': len(cells_data)
        }
        
        # Store matrix
        self.antigram_matrices[antigram_id] = df
        
        # Persist to database if session is available
        if self.db_session:
            self._save_antigram_to_db(antigram_id, df, self.antigram_metadata[antigram_id])
        
        return df
    
    def _save_antigram_to_db(self, antigram_id: int, matrix: pd.DataFrame, metadata: Dict):
        """Save antigram matrix and metadata to database."""
        try:
            # Check if antigram already exists
            existing = self.db_session.query(AntigramMatrixStorage).filter_by(antigram_id=antigram_id).first()
            
            # Prepare data for storage
            matrix_json = json.dumps(matrix.to_dict())
            metadata_json = json.dumps(metadata, default=str)
            current_time = datetime.now().date()
            
            if existing:
                # Update existing record
                existing.matrix_data = matrix_json
                existing.matrix_metadata = metadata_json
                existing.updated_at = current_time
            else:
                # Create new record
                storage = AntigramMatrixStorage(
                    antigram_id=antigram_id,
                    matrix_data=matrix_json,
                    matrix_metadata=metadata_json,
                    created_at=current_time,
                    updated_at=current_time
                )
                self.db_session.add(storage)
            
            # Don't commit immediately - let the caller handle batching
            # self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving antigram to database: {e}")
            raise
    
    def load_from_database(self, db_session):
        """Load all antigram data from database."""
        self.db_session = db_session
        try:
            # Load all stored antigrams
            stored_antigrams = db_session.query(AntigramMatrixStorage).all()
            
            for stored in stored_antigrams:
                # Load matrix
                matrix_dict = json.loads(stored.matrix_data)
                matrix_df = pd.DataFrame.from_dict(matrix_dict, orient='index')
                matrix_df.index.name = 'cell_number'
                
                # Load metadata
                metadata = json.loads(stored.matrix_metadata)
                
                # Store in memory
                self.antigram_matrices[stored.antigram_id] = matrix_df
                self.antigram_metadata[stored.antigram_id] = metadata
            
            logger.info(f"Loaded {len(stored_antigrams)} antigrams from database")
            
        except Exception as e:
            logger.error(f"Error loading antigrams from database: {e}")
    
    def load_antigram_lazy(self, antigram_id: int) -> Optional[pd.DataFrame]:
        """Lazy load a specific antigram from database."""
        if antigram_id in self.antigram_matrices:
            return self.antigram_matrices[antigram_id]
        
        if not self.db_session:
            return None
        
        try:
            stored = self.db_session.query(AntigramMatrixStorage).filter_by(antigram_id=antigram_id).first()
            if stored:
                # Load matrix
                matrix_dict = json.loads(stored.matrix_data)
                matrix_df = pd.DataFrame.from_dict(matrix_dict, orient='index')
                matrix_df.index.name = 'cell_number'
                
                # Load metadata
                metadata = json.loads(stored.matrix_metadata)
                
                # Store in memory
                self.antigram_matrices[antigram_id] = matrix_df
                self.antigram_metadata[antigram_id] = metadata
                
                return matrix_df
        except Exception as e:
            logger.error(f"Error lazy loading antigram {antigram_id}: {e}")
        
        return None
    
    def save_all_to_database(self):
        """Save all current antigram data to database."""
        if not self.db_session:
            logger.warning("No database session available")
            return
        
        try:
            for antigram_id, matrix in self.antigram_matrices.items():
                metadata = self.antigram_metadata.get(antigram_id, {})
                self._save_antigram_to_db(antigram_id, matrix, metadata)
            
            # Batch commit all changes
            self.db_session.commit()
            logger.info(f"Saved {len(self.antigram_matrices)} antigrams to database")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving antigrams to database: {e}")
    
    def commit_changes(self):
        """Commit pending database changes."""
        if self.db_session:
            try:
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                logger.error(f"Error committing changes: {e}")
                raise
    
    def get_antigram_matrix(self, antigram_id: int) -> Optional[pd.DataFrame]:
        """Get antigram matrix by ID."""
        return self.antigram_matrices.get(antigram_id)
    
    def get_antigram_metadata(self, antigram_id: int) -> Optional[Dict]:
        """Get antigram metadata by ID."""
        return self.antigram_metadata.get(antigram_id)
    
    def get_all_antigrams(self) -> List[Dict]:
        """Get all antigram metadata."""
        return [
            {'id': antigram_id, **metadata}
            for antigram_id, metadata in self.antigram_metadata.items()
        ]
    
    def find_cells_by_pattern(self, antigen_pattern: Dict[str, str]) -> List[Dict]:
        """
        Find cells matching a specific antigen pattern across all antigrams.
        
        Args:
            antigen_pattern: Dict of {antigen: reaction_value}
            
        Returns:
            List of matching cells with antigram info
        """
        matches = []
        
        for antigram_id, matrix in self.antigram_matrices.items():
            metadata = self.antigram_metadata[antigram_id]
            
            # Check if matrix has all required antigens
            if not all(antigen in matrix.columns for antigen in antigen_pattern.keys()):
                continue
            
            # Find matching cells
            mask = pd.Series(True, index=matrix.index)
            for antigen, expected_reaction in antigen_pattern.items():
                mask &= (matrix[antigen] == expected_reaction)
            
            matching_cells = matrix[mask]
            
            for cell_number in matching_cells.index:
                matches.append({
                    'antigram_id': antigram_id,
                    'lot_number': metadata['lot_number'],
                    'template_name': metadata['template_name'],
                    'cell_number': cell_number,
                    'reactions': matching_cells.loc[cell_number].to_dict(),
                    'expiration_date': metadata['expiration_date']
                })
        
        return matches
    
    def get_antigen_reactions(self, antigen: str) -> Dict[int, Dict[int, str]]:
        """
        Get all reactions for a specific antigen across all antigrams.
        
        Args:
            antigen: Antigen name
            
        Returns:
            Dict of {antigram_id: {cell_number: reaction_value}}
        """
        antigen_reactions = {}
        
        for antigram_id, matrix in self.antigram_matrices.items():
            if antigen in matrix.columns:
                antigen_reactions[antigram_id] = matrix[antigen].to_dict()
        
        return antigen_reactions
    
    def update_antigram_matrix(self, antigram_id: int, lot_number: str, 
                              cells_data: List[Dict], expiration_date: date) -> pd.DataFrame:
        """
        Update an existing antigram matrix with new data.
        
        Args:
            antigram_id: Unique identifier for the antigram
            lot_number: Updated lot number string
            cells_data: List of cell data with reactions
            expiration_date: Updated expiration date
            
        Returns:
            pandas.DataFrame: Updated matrix with cells as index and antigens as columns
        """
        if antigram_id not in self.antigram_matrices:
            raise ValueError(f"Antigram with ID {antigram_id} not found")
        
        # Get existing metadata to preserve template info
        existing_metadata = self.antigram_metadata[antigram_id]
        template_name = existing_metadata['template_name']
        antigens = existing_metadata['antigens']
        
        # Create updated matrix data
        matrix_data = []
        cell_numbers = []
        
        for cell in cells_data:
            cell_number = cell['cell_number']
            cell_numbers.append(cell_number)
            
            # Create row for this cell
            row_data = {}
            for antigen in antigens:
                reaction = cell['reactions'].get(antigen, '-')
                row_data[antigen] = reaction
            
            matrix_data.append(row_data)
        
        # Create updated DataFrame
        df = pd.DataFrame(matrix_data, index=cell_numbers)
        df.index.name = 'cell_number'
        
        # Update metadata
        self.antigram_metadata[antigram_id] = {
            'lot_number': lot_number,
            'template_name': template_name,
            'antigens': antigens,
            'expiration_date': expiration_date,
            'cell_count': len(cells_data)
        }
        
        # Update matrix
        self.antigram_matrices[antigram_id] = df
        
        # Persist to database if session is available
        if self.db_session:
            self._save_antigram_to_db(antigram_id, df, self.antigram_metadata[antigram_id])
        
        return df

    def delete_antigram(self, antigram_id: int) -> bool:
        """Delete an antigram and its matrix."""
        if antigram_id in self.antigram_matrices:
            del self.antigram_matrices[antigram_id]
            del self.antigram_metadata[antigram_id]
            
            # Delete from database if session is available
            if self.db_session:
                try:
                    stored = self.db_session.query(AntigramMatrixStorage).filter_by(antigram_id=antigram_id).first()
                    if stored:
                        self.db_session.delete(stored)
                        self.db_session.commit()
                except Exception as e:
                    self.db_session.rollback()
                    logger.error(f"Error deleting antigram from database: {e}")
            
            return True
        return False
    
    def to_json(self) -> Dict:
        """Convert all data to JSON-serializable format."""
        return {
            'antigram_matrices': {
                str(antigram_id): {
                    'matrix': matrix.to_dict(),
                    'metadata': self.antigram_metadata[antigram_id]
                }
                for antigram_id, matrix in self.antigram_matrices.items()
            },
            'patient_reactions': self.patient_reactions.to_dict() if not self.patient_reactions.empty else {}
        }
    
    def from_json(self, data: Dict):
        """Load data from JSON format."""
        # Load antigram matrices
        for antigram_id_str, antigram_data in data.get('antigram_matrices', {}).items():
            antigram_id = int(antigram_id_str)
            matrix_df = pd.DataFrame.from_dict(antigram_data['matrix'], orient='index')
            matrix_df.index.name = 'cell_number'
            self.antigram_matrices[antigram_id] = matrix_df
            self.antigram_metadata[antigram_id] = antigram_data['metadata']
        
        # Load patient reactions
        if data.get('patient_reactions'):
            self.patient_reactions = pd.DataFrame.from_dict(data['patient_reactions'], orient='index')


class PandasPatientReactionManager:
    """
    Manages patient reaction data using pandas for efficient operations.
    Now includes database persistence for data durability.
    """
    
    def __init__(self, db_session=None):
        # Always initialize with a MultiIndex, even if empty
        self.reactions_df = pd.DataFrame(columns=['patient_reaction'])
        self.reactions_df.index = pd.MultiIndex.from_tuples([], names=['antigram_id', 'cell_number'])
        self.db_session = db_session
    
    def add_reaction(self, antigram_id: int, cell_number: int, reaction: str):
        """Add or update a patient reaction."""
        index = (antigram_id, cell_number)
        # If not MultiIndex, convert
        if not isinstance(self.reactions_df.index, pd.MultiIndex):
            self.reactions_df.index = pd.MultiIndex.from_tuples(self.reactions_df.index, names=['antigram_id', 'cell_number'])
        # Add or update
        self.reactions_df.loc[index, 'patient_reaction'] = reaction
        # Ensure MultiIndex after assignment
        if not isinstance(self.reactions_df.index, pd.MultiIndex):
            self.reactions_df.index = pd.MultiIndex.from_tuples(self.reactions_df.index, names=['antigram_id', 'cell_number'])
        
        # Persist to database if session is available
        if self.db_session:
            self._save_reaction_to_db(antigram_id, cell_number, reaction)
    
    def _save_reaction_to_db(self, antigram_id: int, cell_number: int, reaction: str):
        """Save patient reaction to database."""
        try:
            # Check if reaction already exists
            existing = self.db_session.query(PatientReactionStorage).filter_by(
                antigram_id=antigram_id, 
                cell_number=cell_number
            ).first()
            
            current_time = datetime.now().date()
            
            if existing:
                # Update existing record
                existing.patient_reaction = reaction
                existing.updated_at = current_time
            else:
                # Create new record
                storage = PatientReactionStorage(
                    antigram_id=antigram_id,
                    cell_number=cell_number,
                    patient_reaction=reaction,
                    created_at=current_time,
                    updated_at=current_time
                )
                self.db_session.add(storage)
            
            # Don't commit immediately - let the caller handle batching
            # self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving patient reaction to database: {e}")
            raise
    
    def load_from_database(self, db_session):
        """Load all patient reaction data from database."""
        self.db_session = db_session
        try:
            # Load all stored reactions
            stored_reactions = db_session.query(PatientReactionStorage).all()
            
            if stored_reactions:
                # Prepare data for DataFrame
                tuples = []
                reactions = []
                
                for stored in stored_reactions:
                    tuples.append((stored.antigram_id, stored.cell_number))
                    reactions.append({'patient_reaction': stored.patient_reaction})
                
                # Create DataFrame
                self.reactions_df = pd.DataFrame(reactions, index=pd.MultiIndex.from_tuples(tuples, names=['antigram_id', 'cell_number']))
            
            logger.info(f"Loaded {len(stored_reactions)} patient reactions from database")
            
        except Exception as e:
            logger.error(f"Error loading patient reactions from database: {e}")
    
    def save_all_to_database(self):
        """Save all current patient reaction data to database."""
        if not self.db_session:
            logger.warning("No database session available")
            return
        
        try:
            # Clear existing reactions in database
            self.db_session.query(PatientReactionStorage).delete()
            
            # Save all current reactions
            for (antigram_id, cell_number), row in self.reactions_df.iterrows():
                self._save_reaction_to_db(antigram_id, cell_number, row['patient_reaction'])
            
            # Batch commit all changes
            self.db_session.commit()
            logger.info(f"Saved {len(self.reactions_df)} patient reactions to database")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving patient reactions to database: {e}")
    
    def commit_changes(self):
        """Commit pending database changes."""
        if self.db_session:
            try:
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                logger.error(f"Error committing changes: {e}")
                raise
    
    def get_reactions_for_antigram(self, antigram_id: int) -> Dict[int, str]:
        """Get all patient reactions for a specific antigram."""
        if self.reactions_df.empty:
            return {}
        if not isinstance(self.reactions_df.index, pd.MultiIndex):
            self.reactions_df.index = pd.MultiIndex.from_tuples(self.reactions_df.index, names=['antigram_id', 'cell_number'])
        try:
            mask = self.reactions_df.index.get_level_values(0) == antigram_id
            reactions = self.reactions_df[mask]
            return {cell_number: val for (_, cell_number), val in reactions['patient_reaction'].items()}
        except Exception as e:
            logger.error(f"Error in get_reactions_for_antigram: {e}")
            return {}
    
    def get_reactions_for_antigen(self, antigen: str, antigram_manager: PandasAntigramManager) -> List[Dict]:
        """
        Get all patient reactions for a specific antigen across all antigrams.
        
        Args:
            antigen: Antigen name
            antigram_manager: PandasAntigramManager instance
            
        Returns:
            List of reaction data with cell and antigram info
        """
        antigen_reactions = []
        
        for antigram_id, matrix in antigram_manager.antigram_matrices.items():
            if antigen not in matrix.columns:
                continue
            
            # Get cell reactions for this antigen
            cell_reactions = matrix[antigen]
            
            # Get patient reactions for this antigram
            patient_reactions = self.get_reactions_for_antigram(antigram_id)
            
            for cell_number, cell_reaction in cell_reactions.items():
                if cell_reaction == '+':  # Only include cells that express the antigen
                    patient_reaction = patient_reactions.get(cell_number, None)
                    if patient_reaction is not None:
                        metadata = antigram_manager.get_antigram_metadata(antigram_id)
                        antigen_reactions.append({
                            'antigram_id': antigram_id,
                            'lot_number': metadata['lot_number'],
                            'cell_number': cell_number,
                            'cell_reaction': cell_reaction,
                            'patient_reaction': patient_reaction
                        })
        
        return antigen_reactions
    
    def clear_reactions(self):
        """Clear all patient reactions."""
        self.reactions_df = pd.DataFrame(columns=['patient_reaction'])
        self.reactions_df.index = pd.MultiIndex.from_tuples([], names=['antigram_id', 'cell_number'])
    
    def delete_reaction(self, antigram_id: int, cell_number: int):
        """Delete a specific patient reaction."""
        index = (antigram_id, cell_number)
        if index in self.reactions_df.index:
            self.reactions_df = self.reactions_df.drop(index)
            if not isinstance(self.reactions_df.index, pd.MultiIndex):
                self.reactions_df.index = pd.MultiIndex.from_tuples(self.reactions_df.index, names=['antigram_id', 'cell_number'])
            
            # Delete from database if session is available
            if self.db_session:
                try:
                    stored = self.db_session.query(PatientReactionStorage).filter_by(
                        antigram_id=antigram_id, 
                        cell_number=cell_number
                    ).first()
                    if stored:
                        self.db_session.delete(stored)
                        self.db_session.commit()
                except Exception as e:
                    self.db_session.rollback()
                    logger.error(f"Error deleting patient reaction from database: {e}")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        if self.reactions_df.empty:
            return {}
        
        # Serialize MultiIndex as string keys
        return {str(index): row.to_dict() for index, row in self.reactions_df.iterrows()}
    
    def from_dict(self, data: Dict):
        """Load from dictionary format."""
        if data:
            tuples = []
            rows = []
            for index_str, row in data.items():
                index_str = index_str.strip('()')
                antigram_id, cell_number = map(int, index_str.split(', '))
                tuples.append((antigram_id, cell_number))
                rows.append(row)
            self.reactions_df = pd.DataFrame(rows, index=pd.MultiIndex.from_tuples(tuples, names=['antigram_id', 'cell_number']))
        else:
            self.clear_reactions()


# SQLAlchemy model for storing pandas data
class AntigramMatrixStorage(Base):
    """SQLAlchemy model for storing antigram matrices as JSON."""
    __tablename__ = 'antigram_matrix_storage'
    
    id = Column(Integer, primary_key=True)
    antigram_id = Column(Integer, nullable=False, unique=True)
    matrix_data = Column(Text, nullable=False)  # JSON string of pandas DataFrame
    matrix_metadata = Column(Text, nullable=False)     # JSON string of metadata
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'antigram_id': self.antigram_id,
            'matrix_data': json.loads(self.matrix_data),
            'metadata': json.loads(self.matrix_metadata),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PatientReactionStorage(Base):
    """SQLAlchemy model for storing patient reactions as JSON."""
    __tablename__ = 'patient_reaction_storage'
    
    id = Column(Integer, primary_key=True)
    antigram_id = Column(Integer, nullable=False)
    cell_number = Column(Integer, nullable=False)
    patient_reaction = Column(String(10), nullable=False)  # The reaction value
    created_at = Column(Date, nullable=False)
    updated_at = Column(Date, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'antigram_id': self.antigram_id,
            'cell_number': self.cell_number,
            'patient_reaction': self.patient_reaction,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PandasTemplateManager:
    """
    Manages antigram templates with database persistence.
    Mirrors the SQLAlchemy AntigramTemplate model for consistency.
    """
    def __init__(self, db_session=None):
        self.templates = {}  # template_id: dict
        self.db_session = db_session

    def add_template(self, template_id: int, name: str, antigen_order: list, cell_count: int, cell_range: list = None):
        """Add template to memory and database."""
        self.templates[template_id] = {
            "id": template_id,
            "name": name,
            "antigen_order": antigen_order,
            "cell_count": cell_count,
            "cell_range": cell_range
        }
        
        # Persist to database if session is available
        if self.db_session:
            self._save_template_to_db(template_id, name, antigen_order, cell_count, cell_range)

    def _save_template_to_db(self, template_id: int, name: str, antigen_order: list, cell_count: int, cell_range: list = None):
        """Save template to database."""
        try:
            from models import AntigramTemplate
            
            # Check if template already exists
            existing = self.db_session.query(AntigramTemplate).filter_by(id=template_id).first()
            
            # Convert cell_range to JSON string if provided
            cell_range_json = json.dumps(cell_range) if cell_range else None
            
            if existing:
                # Update existing record
                existing.name = name
                existing.antigen_order = ",".join(antigen_order)
                existing.cell_count = cell_count
                existing.cell_range = cell_range_json
            else:
                # Create new record
                template = AntigramTemplate(
                    id=template_id,
                    name=name,
                    antigen_order=",".join(antigen_order),
                    cell_count=cell_count,
                    cell_range=cell_range_json
                )
                self.db_session.add(template)
            
            # Don't commit immediately - let the caller handle batching
            # self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving template to database: {e}")
            raise

    def load_from_database(self, db_session):
        """Load all templates from database."""
        self.db_session = db_session
        try:
            from models import AntigramTemplate
            
            # Load all stored templates
            stored_templates = db_session.query(AntigramTemplate).all()
            
            for stored in stored_templates:
                # Parse cell_range from JSON string
                cell_range_list = None
                if stored.cell_range:
                    try:
                        cell_range_list = json.loads(stored.cell_range)
                    except (json.JSONDecodeError, TypeError):
                        cell_range_list = None
                
                self.templates[stored.id] = {
                    "id": stored.id,
                    "name": stored.name,
                    "antigen_order": stored.antigen_order.split(",") if stored.antigen_order else [],
                    "cell_count": stored.cell_count,
                    "cell_range": cell_range_list
                }
            
            logger.info(f"Loaded {len(stored_templates)} templates from database")
            
        except Exception as e:
            logger.error(f"Error loading templates from database: {e}")

    def save_all_to_database(self):
        """Save all current templates to database."""
        if not self.db_session:
            logger.warning("No database session available")
            return
        
        try:
            for template_id, template_data in self.templates.items():
                self._save_template_to_db(
                    template_id,
                    template_data["name"],
                    template_data["antigen_order"],
                    template_data["cell_count"],
                    template_data.get("cell_range")
                )
            
            # Batch commit all changes
            self.db_session.commit()
            logger.info(f"Saved {len(self.templates)} templates to database")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error saving templates to database: {e}")
    
    def commit_changes(self):
        """Commit pending database changes."""
        if self.db_session:
            try:
                self.db_session.commit()
            except Exception as e:
                self.db_session.rollback()
                logger.error(f"Error committing changes: {e}")
                raise

    def delete_template(self, template_id: int):
        """Delete template from memory and database."""
        if template_id in self.templates:
            del self.templates[template_id]
            
            # Delete from database if session is available
            if self.db_session:
                try:
                    from models import AntigramTemplate
                    stored = self.db_session.query(AntigramTemplate).filter_by(id=template_id).first()
                    if stored:
                        self.db_session.delete(stored)
                        self.db_session.commit()
                except Exception as e:
                    self.db_session.rollback()
                    logger.error(f"Error deleting template from database: {e}")

    def get_template(self, template_id: int):
        return self.templates.get(template_id)

    def get_all_templates(self):
        return list(self.templates.values())

    def to_json(self):
        return self.templates

    def from_json(self, data):
        self.templates = data

    def save_to_json(self, filepath):
        import json
        with open(filepath, 'w') as f:
            json.dump(self.templates, f, indent=2)

    def load_from_json(self, filepath):
        import json
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.templates = json.load(f)
    
    def validate_cell_range(self, cell_count: int, cell_range: list = None) -> bool:
        """
        Validate that cell_count matches the cell_range.
        
        Args:
            cell_count: Number of cells
            cell_range: List of [start, end] cell numbers
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not cell_range:
            return True  # No range specified, so it's valid
        
        if not isinstance(cell_range, list) or len(cell_range) != 2:
            return False
        
        start, end = cell_range
        if start >= end:
            return False
        
        expected_count = end - start + 1
        return cell_count == expected_count

