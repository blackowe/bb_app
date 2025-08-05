import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any
from core.pandas_models import PandasAntigramManager, PandasPatientReactionManager
from core.antibody_rule_evaluator import AntibodyRuleEvaluator, AntibodyRuleValidator

class EnhancedAntibodyIdentifier:
    """
    Enhanced antibody identification using the new rule evaluation system.
    Replaces the old PandasAntibodyIdentifier with more sophisticated rule-based logic.
    Now optimized with set theory operations for improved performance.
    """
    
    def __init__(self, antigram_manager: PandasAntigramManager, 
                 patient_reaction_manager: PandasPatientReactionManager,
                 db_session=None):
        self.antigram_manager = antigram_manager
        self.patient_reaction_manager = patient_reaction_manager
        self.db_session = db_session
        self.rule_evaluator = AntibodyRuleEvaluator(antigram_manager, patient_reaction_manager)
        self.rule_validator = AntibodyRuleValidator(db_session) if db_session else None
        
        # Cache for performance optimization
        self._antigen_reactions_cache = {}
        self._all_antigens_cache = None
        
        # Set-based data structures for Phase 2 optimization
        self._antigen_sets = {}
        self._patient_reaction_sets = {}
        self._sets_initialized = False
    
    def identify_antibodies(self, rules: List[Dict] = None) -> Dict:
        """
        Main antibody identification algorithm using the enhanced rule system.
        Now optimized with set theory operations.
        
        Args:
            rules: List of antibody rules. If None, loads from database.
            
        Returns:
            Dict: Results with ruled_out, stro, matches, and detailed information
        """
        # Get all patient reactions
        if self.patient_reaction_manager.reactions_df.empty:
            return {
                "ruled_out": [],
                "stro": [],
                "matches": [],
                "progress": {},
                "ruled_out_details": {},
                "suspected_antibodies": []
            }
        
        # Load rules from database if not provided
        if rules is None:
            rules = self._load_rules_from_database()
        
        # Get all unique antigens from matrices (cached)
        all_antigens = self._get_all_antigens()
        
        # Initialize set-based data structures
        self._initialize_set_structures()
        
        # First pass: identify potential antibodies using sets
        potential_antibodies = self._identify_potential_antibodies_set_based()
        
        # Second pass: evaluate rules to determine ruled out antigens
        rule_results = self.rule_evaluator.evaluate_all_rules(rules, potential_antibodies)
        ruled_out_antigens = set(rule_results['ruled_out_antigens'])
        ruling_out_details = rule_results['ruling_out_details']
        
        # Third pass: categorize remaining antigens using set operations
        stro_antigens = set()
        match_antigens = set()
        
        for antigen in all_antigens:
            if antigen in ruled_out_antigens:
                continue
            
            # Use set-based match criteria check
            if self._check_match_criteria_set_based(antigen):
                match_antigens.add(antigen)
            else:
                stro_antigens.add(antigen)
        
        # Create progress tracking (optimized)
        progress = self._create_progress_tracking_set_based(all_antigens, ruling_out_details)
        
        return {
            "ruled_out": sorted(list(ruled_out_antigens)),
            "stro": sorted(list(stro_antigens)),
            "matches": sorted(list(match_antigens)),
            "progress": progress,
            "ruled_out_details": ruling_out_details,
            "suspected_antibodies": potential_antibodies
        }
    
    def _initialize_set_structures(self):
        """Initialize set-based data structures for optimized operations."""
        if self._sets_initialized:
            return
        
        # Initialize patient reaction sets
        self._patient_reaction_sets = {
            'positive_cells': set(),  # Cells with positive patient reactions
            'negative_cells': set(),  # Cells with negative patient reactions
            'by_antigram': {}         # Patient reactions grouped by antigram
        }
        
        # Initialize antigen expression sets
        self._antigen_sets = {
            'expressing_cells': {},    # antigen -> set of cells expressing it
            'non_expressing_cells': {} # antigen -> set of cells not expressing it
        }
        
        # Build patient reaction sets
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            antigram_cells = set()
            
            for cell_number, patient_reaction in patient_reactions.items():
                cell_key = f"{antigram_id}_{cell_number}"
                antigram_cells.add(cell_key)
                
                if patient_reaction == '+':
                    self._patient_reaction_sets['positive_cells'].add(cell_key)
                elif patient_reaction == '0':
                    self._patient_reaction_sets['negative_cells'].add(cell_key)
            
            self._patient_reaction_sets['by_antigram'][antigram_id] = antigram_cells
        
        # Build antigen expression sets
        all_antigens = self._get_all_antigens()
        for antigen in all_antigens:
            expressing_cells = set()
            non_expressing_cells = set()
            
            for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
                if antigen not in matrix.columns:
                    continue
                
                # Get cells that express this antigen
                antigen_positive = matrix[antigen] == '+'
                antigen_negative = matrix[antigen] == '0'
                
                for cell_number in antigen_positive[antigen_positive].index:
                    cell_key = f"{antigram_id}_{cell_number}"
                    expressing_cells.add(cell_key)
                
                for cell_number in antigen_negative[antigen_negative].index:
                    cell_key = f"{antigram_id}_{cell_number}"
                    non_expressing_cells.add(cell_key)
            
            self._antigen_sets['expressing_cells'][antigen] = expressing_cells
            self._antigen_sets['non_expressing_cells'][antigen] = non_expressing_cells
        
        self._sets_initialized = True
    
    def _identify_potential_antibodies_set_based(self) -> List[str]:
        """
        Identify potential antibodies using set operations.
        These are antigens that have positive patient reactions and will be used
        for ABSpecificRO rule evaluation.
        """
        potential_antibodies = set()
        positive_cells = self._patient_reaction_sets['positive_cells']
        
        for antigen, expressing_cells in self._antigen_sets['expressing_cells'].items():
            # If any cell expressing this antigen has a positive patient reaction
            if expressing_cells & positive_cells:
                potential_antibodies.add(antigen)
        
        return sorted(list(potential_antibodies))
    
    def _check_match_criteria_set_based(self, antigen: str) -> bool:
        """
        Check if antigen meets the 100% match criteria using set operations.
        
        For an antigen to be considered a 100% match, it needs:
        - All expressing cells must have positive patient reactions
        - All non-expressing cells must have negative patient reactions
        - NO mismatches allowed
        
        Args:
            antigen: Antigen name
            
        Returns:
            bool: True if criteria are met (100% perfect match)
        """
        expressing_cells = self._antigen_sets['expressing_cells'].get(antigen, set())
        non_expressing_cells = self._antigen_sets['non_expressing_cells'].get(antigen, set())
        positive_cells = self._patient_reaction_sets['positive_cells']
        negative_cells = self._patient_reaction_sets['negative_cells']
        
        # All expressing cells must be positive AND all non-expressing cells must be negative
        expressing_positive = expressing_cells <= positive_cells
        non_expressing_negative = non_expressing_cells <= negative_cells
        
        return expressing_positive and non_expressing_negative
    
    def _get_all_antigens(self) -> Set[str]:
        """Get all unique antigens from matrices (cached)."""
        if self._all_antigens_cache is None:
            all_antigens = set()
            for matrix in self.antigram_manager.antigram_matrices.values():
                all_antigens.update(matrix.columns)
            self._all_antigens_cache = all_antigens
        return self._all_antigens_cache
    
    def _precompute_antigen_reactions(self, all_antigens: Set[str]):
        """Pre-compute antigen reactions data for all antigens to avoid repeated calculations."""
        self._antigen_reactions_cache.clear()
        
        # Get all patient reactions once
        patient_reactions_by_antigram = {}
        for antigram_id in self.antigram_manager.antigram_matrices.keys():
            patient_reactions_by_antigram[antigram_id] = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
        
        # Pre-compute for each antigen
        for antigen in all_antigens:
            antigen_reactions = []
            
            for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
                if antigen not in matrix.columns:
                    continue
                
                # Get cell reactions for this antigen
                cell_reactions = matrix[antigen]
                patient_reactions = patient_reactions_by_antigram[antigram_id]
                
                # Include ALL cells that have patient reactions
                for cell_number, cell_reaction in cell_reactions.items():
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
            
            self._antigen_reactions_cache[antigen] = antigen_reactions
    
    def _load_rules_from_database(self) -> List[Dict]:
        """Load antibody rules from database."""
        if not self.db_session:
            return []
        
        try:
            from models import AntibodyRule
            rules = self.db_session.query(AntibodyRule).filter_by(enabled=True).all()
            return [rule.to_dict() for rule in rules]
        except Exception:
            return []
    
    def _identify_potential_antibodies(self) -> List[str]:
        """
        Identify potential antibodies based on positive patient reactions.
        These are antigens that have positive patient reactions and will be used
        for ABSpecificRO rule evaluation.
        """
        potential_antibodies = set()
        
        # Get all patient reactions
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            
            for cell_number, patient_reaction in patient_reactions.items():
                if patient_reaction == '+':  # Positive patient reaction
                    # Find which antigens this cell expresses
                    cell_data = matrix.loc[cell_number]
                    for antigen, cell_reaction in cell_data.items():
                        if cell_reaction == '+':  # Cell expresses this antigen
                            potential_antibodies.add(antigen)
        
        return sorted(list(potential_antibodies))
    
    def _get_antigen_reactions_data(self, antigen: str) -> List[Dict]:
        """
        Get all reactions for a specific antigen using cached data.
        
        Args:
            antigen: Antigen name
            
        Returns:
            List of reaction data with cell and patient info
        """
        return self._antigen_reactions_cache.get(antigen, [])
    
    def _check_match_criteria(self, antigen_reactions: List[Dict]) -> bool:
        """
        Check if antigen meets the 100% match criteria.
        
        For an antigen to be considered a 100% match, it needs:
        - Cell-for-cell perfect match
        - Every cell must either:
          * Express the antigen (antigen=+) AND patient reacts positively (+), OR
          * Not express the antigen (antigen=0) AND patient reacts negatively (0)
        - NO mismatches allowed
        
        This is about pattern matching, not antibody identification.
        
        Args:
            antigen_reactions: List of reaction data for this antigen
            
        Returns:
            bool: True if criteria are met (100% perfect match)
        """
        if not antigen_reactions:
            return False
        
        # Check each cell for perfect match
        for reaction in antigen_reactions:
            cell_reaction = reaction['cell_reaction']
            patient_reaction = reaction['patient_reaction']
            
            # Check if this cell is a mismatch
            if (cell_reaction == '+' and patient_reaction == '0') or \
               (cell_reaction == '0' and patient_reaction == '+'):
                # This is a mismatch - not 100% match
                return False
        
        # If we get here, all cells match perfectly
        return True
    
    def _create_progress_tracking_set_based(self, all_antigens: Set[str], ruling_out_details: Dict) -> Dict:
        """Create progress tracking information for each antigen using set operations."""
        progress = {}
        
        for antigen in all_antigens:
            expressing_cells = self._antigen_sets['expressing_cells'].get(antigen, set())
            non_expressing_cells = self._antigen_sets['non_expressing_cells'].get(antigen, set())
            positive_cells = self._patient_reaction_sets['positive_cells']
            negative_cells = self._patient_reaction_sets['negative_cells']
            
            # Calculate match statistics using set operations
            positive_matches = len(expressing_cells & positive_cells)
            negative_matches = len(non_expressing_cells & negative_cells)
            mismatches = len(expressing_cells & negative_cells) + len(non_expressing_cells & positive_cells)
            total_cells = len(expressing_cells | non_expressing_cells)
            
            progress[antigen] = {
                "total_cells": total_cells,
                "positive_matches": positive_matches,
                "negative_matches": negative_matches,
                "mismatches": mismatches,
                "match_percentage": ((positive_matches + negative_matches) / total_cells * 100) if total_cells > 0 else 0,
                "ruling_out_cells": ruling_out_details.get(antigen, []),
                "can_be_ruled_out": antigen in ruling_out_details,
                "meets_match_criteria": self._check_match_criteria_set_based(antigen)
            }
        
        return progress
    
    def _create_progress_tracking_optimized(self, all_antigens: Set[str], ruling_out_details: Dict) -> Dict:
        """Create progress tracking information for each antigen (optimized version)."""
        progress = {}
        
        for antigen in all_antigens:
            antigen_reactions = self._antigen_reactions_cache.get(antigen, [])
            
            # Calculate match statistics
            positive_matches = sum(1 for r in antigen_reactions 
                                 if r['cell_reaction'] == '+' and r['patient_reaction'] == '+')
            negative_matches = sum(1 for r in antigen_reactions 
                                 if r['cell_reaction'] == '0' and r['patient_reaction'] == '0')
            mismatches = sum(1 for r in antigen_reactions 
                           if (r['cell_reaction'] == '+' and r['patient_reaction'] == '0') or
                              (r['cell_reaction'] == '0' and r['patient_reaction'] == '+'))
            
            progress[antigen] = {
                "total_cells": len(antigen_reactions),
                "positive_matches": positive_matches,
                "negative_matches": negative_matches,
                "mismatches": mismatches,
                "match_percentage": ((positive_matches + negative_matches) / len(antigen_reactions) * 100) if antigen_reactions else 0,
                "ruling_out_cells": ruling_out_details.get(antigen, []),
                "can_be_ruled_out": antigen in ruling_out_details,
                "meets_match_criteria": self._check_match_criteria(antigen_reactions) if antigen_reactions else False
            }
        
        return progress
    
    def get_antigen_summary(self, antigen: str, rules: List[Dict] = None) -> Dict:
        """
        Get a detailed summary for a specific antigen.
        
        Args:
            antigen: Antigen name
            rules: List of antibody rules. If None, loads from database.
            
        Returns:
            Dict: Detailed summary for the antigen
        """
        if rules is None:
            rules = self._load_rules_from_database()
        
        antigen_reactions = self._get_antigen_reactions_data(antigen)
        
        if not antigen_reactions:
            return {
                'antigen': antigen,
                'total_cells': 0,
                'positive_patient_reactions': 0,
                'negative_patient_reactions': 0,
                'can_be_ruled_out': False,
                'meets_match_criteria': False,
                'applicable_rules': [],
                'ruling_out_cells': []
            }
        
        # Find applicable rules for this antigen
        applicable_rules = [rule for rule in rules if rule['target_antigen'] == antigen]
        
        # Evaluate rules for this antigen
        ruling_out_cells = []
        can_be_ruled_out = False
        
        for rule in applicable_rules:
            if rule.get('enabled', True):
                is_satisfied, cells = self.rule_evaluator.evaluate_rule(rule)
                if is_satisfied:
                    can_be_ruled_out = True
                    ruling_out_cells.extend(cells)
        
        # Calculate match statistics
        positive_matches = sum(1 for r in antigen_reactions 
                             if r['cell_reaction'] == '+' and r['patient_reaction'] == '+')
        negative_matches = sum(1 for r in antigen_reactions 
                             if r['cell_reaction'] == '0' and r['patient_reaction'] == '0')
        mismatches = sum(1 for r in antigen_reactions 
                        if (r['cell_reaction'] == '+' and r['patient_reaction'] == '0') or
                           (r['cell_reaction'] == '0' and r['patient_reaction'] == '+'))
        
        meets_criteria = self._check_match_criteria(antigen_reactions)
        
        return {
            'antigen': antigen,
            'total_cells': len(antigen_reactions),
            'positive_matches': positive_matches,
            'negative_matches': negative_matches,
            'mismatches': mismatches,
            'match_percentage': ((positive_matches + negative_matches) / len(antigen_reactions) * 100) if antigen_reactions else 0,
            'can_be_ruled_out': can_be_ruled_out,
            'meets_match_criteria': meets_criteria,
            'applicable_rules': [rule['rule_type'] for rule in applicable_rules],
            'ruling_out_cells': ruling_out_cells
        }
    
    def get_all_antigen_summaries(self, rules: List[Dict] = None) -> List[Dict]:
        """
        Get summaries for all antigens.
        
        Args:
            rules: List of antibody rules. If None, loads from database.
            
        Returns:
            List of antigen summaries
        """
        all_antigens = self._get_all_antigens()
        return [self.get_antigen_summary(antigen, rules) for antigen in sorted(all_antigens)]
    
    def validate_rules(self, rules: List[Dict] = None) -> Dict[str, List[str]]:
        """
        Validate antibody rules for conflicts and completeness.
        
        Args:
            rules: List of antibody rules. If None, loads from database.
            
        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        if rules is None:
            rules = self._load_rules_from_database()
        
        if not self.rule_validator:
            return {
                'errors': ["No database session available for validation"],
                'warnings': []
            }
        
        return self.rule_validator.validate_rules(rules) 