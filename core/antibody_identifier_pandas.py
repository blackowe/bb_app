import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple, Optional
from core.pandas_models import PandasAntigramManager, PandasPatientReactionManager
import logging

# Set up logging
logger = logging.getLogger(__name__)


class PandasAntibodyIdentifier:
    """
    Antibody identification using pandas matrices for efficient operations.
    Replaces the complex SQL-based antibody identification with matrix operations.
    """
    
    def __init__(self, antigram_manager: PandasAntigramManager, 
                 patient_reaction_manager: PandasPatientReactionManager):
        self.antigram_manager = antigram_manager
        self.patient_reaction_manager = patient_reaction_manager
    
    def identify_antibodies(self) -> Dict:
        """
        Main antibody identification algorithm using pandas matrices.
        
        Returns:
            Dict: Results with ruled_out, stro, matches, and progress
        """
        logger.debug("Starting antibody identification")
        
        # Get all patient reactions
        if self.patient_reaction_manager.reactions_df.empty:
            logger.debug("No patient reactions found")
            return {
                "ruled_out": [],
                "stro": [],
                "matches": [],
                "progress": {}
            }
        
        logger.debug(f"Patient reactions DataFrame: {self.patient_reaction_manager.reactions_df}")
        
        # Get all unique antigens from matrices
        all_antigens = set()
        for matrix in self.antigram_manager.antigram_matrices.values():
            all_antigens.update(matrix.columns)
        
        logger.debug(f"All antigens found: {sorted(all_antigens)}")
        
        # Initialize results
        ruled_out = set()
        stro = set()
        matches = set()
        progress = {}
        
        # Process each antigen
        for antigen in all_antigens:
            logger.debug(f"Processing antigen: {antigen}")
            antigen_reactions = self._get_antigen_reactions_data(antigen)
            
            if not antigen_reactions:
                logger.debug(f"No reactions found for antigen {antigen}")
                continue
            
            logger.debug(f"Found {len(antigen_reactions)} reactions for antigen {antigen}")
            
            # Track progress for this antigen
            progress[antigen] = {
                "total_rule_outs": 0,
                "required_count": 0,
                "is_complete": False,
                "ruling_out_cells": []
            }
            
            # Check if antigen can be ruled out
            is_ruled_out, rule_out_cells = self._check_antigen_rule_out(antigen, antigen_reactions)
            logger.debug(f"Antigen {antigen} ruled out: {is_ruled_out}, rule out cells: {len(rule_out_cells)}")
            
            if is_ruled_out:
                ruled_out.add(antigen)
                progress[antigen]["is_complete"] = True
                progress[antigen]["ruling_out_cells"] = rule_out_cells
                progress[antigen]["total_rule_outs"] = len(rule_out_cells)
                logger.debug(f"Added {antigen} to ruled_out")
            else:
                # Check if it meets match criteria
                if self._check_match_criteria(antigen_reactions):
                    matches.add(antigen)
                    logger.debug(f"Added {antigen} to matches")
                else:
                    stro.add(antigen)
                    logger.debug(f"Added {antigen} to stro")
        
        logger.debug(f"Final results - ruled_out: {ruled_out}, matches: {matches}, stro: {stro}")
        
        return {
            "ruled_out": sorted(list(ruled_out)),
            "stro": sorted(list(stro)),
            "matches": sorted(list(matches)),
            "progress": progress
        }
    
    def _get_antigen_reactions_data(self, antigen: str) -> List[Dict]:
        """
        Get all reactions for a specific antigen using pandas operations.
        
        Args:
            antigen: Antigen name
            
        Returns:
            List of reaction data with cell and patient info
        """
        antigen_reactions = []
        
        logger.debug(f"Getting antigen reactions for {antigen}")
        
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            if antigen not in matrix.columns:
                logger.debug(f"Antigen {antigen} not found in antigram {antigram_id}")
                continue
            
            logger.debug(f"Processing antigram {antigram_id} for antigen {antigen}")
            
            # Get cell reactions for this antigen
            cell_reactions = matrix[antigen]
            logger.debug(f"Cell reactions for {antigen}: {cell_reactions.to_dict()}")
            
            # Get patient reactions for this antigram
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            logger.debug(f"Patient reactions for antigram {antigram_id}: {patient_reactions}")
            
            # Only include cells that express the antigen and have patient reactions
            for cell_number, cell_reaction in cell_reactions.items():
                logger.debug(f"Cell {cell_number}: cell_reaction={cell_reaction}, patient_reaction={patient_reactions.get(cell_number)}")
                if cell_reaction == '+':  # Cell expresses the antigen
                    patient_reaction = patient_reactions.get(cell_number)
                    if patient_reaction is not None:
                        metadata = self.antigram_manager.get_antigram_metadata(antigram_id)
                        antigen_reactions.append({
                            'antigram_id': antigram_id,
                            'lot_number': metadata['lot_number'],
                            'cell_number': cell_number,
                            'cell_reaction': cell_reaction,
                            'patient_reaction': patient_reaction
                        })
                        logger.debug(f"Added reaction for {antigen} - cell {cell_number}: {cell_reaction}/{patient_reaction}")
        
        logger.debug(f"Total antigen reactions for {antigen}: {len(antigen_reactions)}")
        return antigen_reactions
    
    def _check_antigen_rule_out(self, antigen: str, antigen_reactions: List[Dict]) -> Tuple[bool, List[Dict]]:
        """
        Check if an antigen can be ruled out based on patient reactions.
        
        Args:
            antigen: Antigen name
            antigen_reactions: List of reaction data for this antigen
            
        Returns:
            Tuple of (is_ruled_out, ruling_out_cells)
        """
        # Get rules for this antigen (you'll need to pass rules to this class)
        # For now, we'll implement basic rule checking
        
        ruling_out_cells = []
        
        # Basic rule: antigen can be ruled out if patient=0 to cell where antigen=+
        for reaction in antigen_reactions:
            if (reaction['cell_reaction'] == '+' and 
                reaction['patient_reaction'] == '0'):
                ruling_out_cells.append({
                    'cell_number': reaction['cell_number'],
                    'lot_number': reaction['lot_number']
                })
        
        # For now, require at least 1 ruling out cell
        # In practice, you'd check against actual antigen rules
        return len(ruling_out_cells) >= 1, ruling_out_cells
    
    def _check_match_criteria(self, antigen_reactions: List[Dict]) -> bool:
        """
        Check if antigen meets the 3 positive and 3 negative reaction criteria.
        
        Args:
            antigen_reactions: List of reaction data for this antigen
            
        Returns:
            bool: True if criteria are met
        """
        positive_count = sum(1 for r in antigen_reactions 
                           if r['patient_reaction'] == '+' and r['cell_reaction'] == '+')
        negative_count = sum(1 for r in antigen_reactions 
                           if r['patient_reaction'] == '0' and r['cell_reaction'] == '+')
        
        return positive_count >= 3 and negative_count >= 3
    
    def get_antigen_reactions_matrix(self, antigen: str) -> pd.DataFrame:
        """
        Create a matrix of reactions for a specific antigen across all antigrams.
        
        Args:
            antigen: Antigen name
            
        Returns:
            pandas.DataFrame: Matrix with antigram_id as index and cell_number as columns
        """
        antigen_data = []
        
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            if antigen not in matrix.columns:
                continue
            
            # Get cell reactions for this antigen
            cell_reactions = matrix[antigen]
            
            # Get patient reactions for this antigram
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            
            # Create row for this antigram
            row_data = {'antigram_id': antigram_id}
            for cell_number in cell_reactions.index:
                cell_reaction = cell_reactions[cell_number]
                patient_reaction = patient_reactions.get(cell_number, '')
                
                if cell_reaction == '+':  # Only include cells that express the antigen
                    row_data[f'cell_{cell_number}'] = f"{cell_reaction}/{patient_reaction}"
            
            antigen_data.append(row_data)
        
        if not antigen_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(antigen_data)
        df.set_index('antigram_id', inplace=True)
        return df
    
    def get_antigen_summary(self, antigen: str) -> Dict:
        """
        Get a summary of reactions for a specific antigen.
        
        Args:
            antigen: Antigen name
            
        Returns:
            Dict: Summary statistics for the antigen
        """
        antigen_reactions = self._get_antigen_reactions_data(antigen)
        
        if not antigen_reactions:
            return {
                'antigen': antigen,
                'total_cells': 0,
                'positive_patient_reactions': 0,
                'negative_patient_reactions': 0,
                'can_be_ruled_out': False,
                'meets_match_criteria': False
            }
        
        positive_count = sum(1 for r in antigen_reactions 
                           if r['patient_reaction'] == '+' and r['cell_reaction'] == '+')
        negative_count = sum(1 for r in antigen_reactions 
                           if r['patient_reaction'] == '0' and r['cell_reaction'] == '+')
        
        is_ruled_out, _ = self._check_antigen_rule_out(antigen, antigen_reactions)
        meets_criteria = self._check_match_criteria(antigen_reactions)
        
        return {
            'antigen': antigen,
            'total_cells': len(antigen_reactions),
            'positive_patient_reactions': positive_count,
            'negative_patient_reactions': negative_count,
            'can_be_ruled_out': is_ruled_out,
            'meets_match_criteria': meets_criteria
        }
    
    def get_all_antigen_summaries(self) -> List[Dict]:
        """
        Get summaries for all antigens.
        
        Returns:
            List of antigen summaries
        """
        all_antigens = set()
        for matrix in self.antigram_manager.antigram_matrices.values():
            all_antigens.update(matrix.columns)
        
        return [self.get_antigen_summary(antigen) for antigen in sorted(all_antigens)]


 