import pandas as pd
import numpy as np
from typing import Dict, List, Set, Tuple, Optional, Any
from core.pandas_models import PandasAntigramManager, PandasPatientReactionManager
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)


class AntibodyRuleEvaluator:
    """
    Evaluates antibody rules against patient reaction data.
    Supports all rule types: ABSpecificRO, Homo, Hetero, SingleAG, LowF
    """
    
    def __init__(self, antigram_manager: PandasAntigramManager, 
                 patient_reaction_manager: PandasPatientReactionManager):
        self.antigram_manager = antigram_manager
        self.patient_reaction_manager = patient_reaction_manager
    
    def evaluate_rule(self, rule: Dict, suspected_antibody: str = None) -> Tuple[bool, List[Dict]]:
        """
        Evaluate a single antibody rule.
        
        Args:
            rule: Rule dictionary with rule_type, target_antigen, and rule_data
            suspected_antibody: The suspected antibody (for ABSpecificRO rules)
            
        Returns:
            Tuple of (is_satisfied, ruling_out_cells)
        """
        rule_type = rule['rule_type']
        target_antigen = rule['target_antigen']
        rule_data = rule['rule_data']
        
        logger.debug(f"Evaluating {rule_type} rule for antigen {target_antigen}")
        
        if rule_type == 'abspecific':
            return self._evaluate_abspecific_rule(target_antigen, rule_data, suspected_antibody)
        elif rule_type == 'homo':
            return self._evaluate_homo_rule(target_antigen, rule_data)
        elif rule_type == 'hetero':
            return self._evaluate_hetero_rule(target_antigen, rule_data)
        elif rule_type == 'single':
            return self._evaluate_single_rule(target_antigen, rule_data)
        elif rule_type == 'lowf':
            return self._evaluate_lowf_rule(target_antigen, rule_data)
        else:
            logger.warning(f"Unknown rule type: {rule_type}")
            return False, []
    
    def _evaluate_abspecific_rule(self, target_antigen: str, rule_data: Dict, suspected_antibody: str) -> Tuple[bool, List[Dict]]:
        """
        Evaluate ABSpecificRO(A,B,C,X) rule.
        Rule out B antigen when patient is 0 for cells with expression B=+, C=+.
        Must have minimum of X number of occurrences for B antigen to be ruled out.
        """
        if not suspected_antibody:
            logger.debug("No suspected antibody provided for ABSpecificRO rule")
            return False, []
        
        antibody = rule_data.get('antibody')
        antigen1 = rule_data.get('antigen1')  # B in the rule
        antigen2 = rule_data.get('antigen2')  # C in the rule
        required_count = rule_data.get('required_count', 1)
        
        if antibody != suspected_antibody:
            logger.debug(f"ABSpecificRO rule antibody {antibody} doesn't match suspected {suspected_antibody}")
            return False, []
        
        ruling_out_cells = []
        
        # Find cells where both antigen1=+ and antigen2=+
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            if antigen1 not in matrix.columns or antigen2 not in matrix.columns:
                continue
            
            # Get patient reactions for this antigram
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            
            # Find cells where both antigens are positive
            antigen1_positive = matrix[antigen1] == '+'
            antigen2_positive = matrix[antigen2] == '+'
            both_positive = antigen1_positive & antigen2_positive
            
            # Check patient reactions for these cells
            for cell_number in both_positive[both_positive].index:
                patient_reaction = patient_reactions.get(cell_number)
                if patient_reaction == '0':  # Patient is negative
                    metadata = self.antigram_manager.get_antigram_metadata(antigram_id)
                    ruling_out_cells.append({
                        'cell_number': cell_number,
                        'lot_number': metadata['lot_number'],
                        'antigram_id': antigram_id,
                        'rule_type': 'abspecific',
                        'antigen1': antigen1,
                        'antigen2': antigen2
                    })
        
        is_satisfied = len(ruling_out_cells) >= required_count
        logger.debug(f"ABSpecificRO rule for {target_antigen}: {len(ruling_out_cells)}/{required_count} cells found")
        
        return is_satisfied, ruling_out_cells
    
    def _evaluate_homo_rule(self, target_antigen: str, rule_data: Dict) -> Tuple[bool, List[Dict]]:
        """
        Evaluate Homo[(A,B),] rule.
        A antigen will be ruled out when patient is 0 for cells with expression A=+, B=0.
        """
        antigen_pairs = rule_data.get('antigen_pairs', [])
        ruling_out_cells = []
        
        for antigen_a, antigen_b in antigen_pairs:
            if antigen_a == target_antigen:
                # Find cells where A=+ and B=0
                for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
                    if antigen_a not in matrix.columns or antigen_b not in matrix.columns:
                        continue
                    
                    # Get patient reactions for this antigram
                    patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
                    
                    # Find cells where A=+ and B=0
                    antigen_a_positive = matrix[antigen_a] == '+'
                    antigen_b_negative = matrix[antigen_b] == '0'
                    matching_cells = antigen_a_positive & antigen_b_negative
                    
                    # Check patient reactions for these cells
                    for cell_number in matching_cells[matching_cells].index:
                        patient_reaction = patient_reactions.get(cell_number)
                        if patient_reaction == '0':  # Patient is negative
                            metadata = self.antigram_manager.get_antigram_metadata(antigram_id)
                            ruling_out_cells.append({
                                'cell_number': cell_number,
                                'lot_number': metadata['lot_number'],
                                'antigram_id': antigram_id,
                                'rule_type': 'homozygous',
                                'antigen_a': antigen_a,
                                'antigen_b': antigen_b
                            })
        
        is_satisfied = len(ruling_out_cells) >= 1  # At least one cell needed
        logger.debug(f"Homo rule for {target_antigen}: {len(ruling_out_cells)} cells found")
        
        return is_satisfied, ruling_out_cells
    
    def _evaluate_hetero_rule(self, target_antigen: str, rule_data: Dict) -> Tuple[bool, List[Dict]]:
        """
        Evaluate Hetero(A,B,X) rule.
        Can rule out A antigen when patient is 0 for cells with expression A=+, B=+.
        Must have X number of cells/occurrence to successfully rule out A antigen.
        """
        antigen_a = rule_data.get('antigen_a')
        antigen_b = rule_data.get('antigen_b')
        required_count = rule_data.get('required_count', 3)
        
        if antigen_a != target_antigen:
            logger.debug(f"Hetero rule antigen_a {antigen_a} doesn't match target {target_antigen}")
            return False, []
        
        ruling_out_cells = []
        
        # Find cells where both A=+ and B=+
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            if antigen_a not in matrix.columns or antigen_b not in matrix.columns:
                continue
            
            # Get patient reactions for this antigram
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            
            # Find cells where both antigens are positive
            antigen_a_positive = matrix[antigen_a] == '+'
            antigen_b_positive = matrix[antigen_b] == '+'
            both_positive = antigen_a_positive & antigen_b_positive
            
            # Check patient reactions for these cells
            for cell_number in both_positive[both_positive].index:
                patient_reaction = patient_reactions.get(cell_number)
                if patient_reaction == '0':  # Patient is negative
                    metadata = self.antigram_manager.get_antigram_metadata(antigram_id)
                    ruling_out_cells.append({
                        'cell_number': cell_number,
                        'lot_number': metadata['lot_number'],
                        'antigram_id': antigram_id,
                        'rule_type': 'heterozygous',
                        'antigen_a': antigen_a,
                        'antigen_b': antigen_b
                    })
        
        is_satisfied = len(ruling_out_cells) >= required_count
        logger.debug(f"Hetero rule for {target_antigen}: {len(ruling_out_cells)}/{required_count} cells found")
        
        return is_satisfied, ruling_out_cells
    
    def _evaluate_single_rule(self, target_antigen: str, rule_data: Dict) -> Tuple[bool, List[Dict]]:
        """
        Evaluate SingleAG([A,B,C,...]) rule.
        Antigens in the SingleAG() category are ruled out when patient is 0 and cell has expression of +.
        """
        antigens = rule_data.get('antigens', [])
        
        if target_antigen not in antigens:
            logger.debug(f"Target antigen {target_antigen} not in SingleAG antigens {antigens}")
            return False, []
        
        ruling_out_cells = []
        
        # Find cells where target antigen is positive
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            if target_antigen not in matrix.columns:
                continue
            
            # Get patient reactions for this antigram
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            
            # Find cells where target antigen is positive
            antigen_positive = matrix[target_antigen] == '+'
            
            # Check patient reactions for these cells
            for cell_number in antigen_positive[antigen_positive].index:
                patient_reaction = patient_reactions.get(cell_number)
                if patient_reaction == '0':  # Patient is negative
                    metadata = self.antigram_manager.get_antigram_metadata(antigram_id)
                    ruling_out_cells.append({
                        'cell_number': cell_number,
                        'lot_number': metadata['lot_number'],
                        'antigram_id': antigram_id,
                        'rule_type': 'single',
                        'antigen': target_antigen
                    })
        
        is_satisfied = len(ruling_out_cells) >= 1  # At least one cell needed
        logger.debug(f"SingleAG rule for {target_antigen}: {len(ruling_out_cells)} cells found")
        
        return is_satisfied, ruling_out_cells
    
    def _evaluate_lowf_rule(self, target_antigen: str, rule_data: Dict) -> Tuple[bool, List[Dict]]:
        """
        Evaluate LowF([A,B,C,…]) rule.
        Antigens in the LowF() category are automatically ruled out due to low prevalence.
        """
        antigens = rule_data.get('antigens', [])
        
        if target_antigen in antigens:
            # Low frequency antigens are automatically ruled out
            logger.debug(f"LowF rule: {target_antigen} automatically ruled out due to low prevalence")
            return True, [{'rule_type': 'lowf', 'antigen': target_antigen, 'reason': 'low_prevalence'}]
        
        return False, []
    
    def evaluate_all_rules(self, rules: List[Dict], suspected_antibodies: List[str] = None) -> Dict[str, Any]:
        """
        Evaluate all rules for all antigens.
        
        Args:
            rules: List of rule dictionaries
            suspected_antibodies: List of suspected antibodies (for ABSpecificRO rules)
            
        Returns:
            Dict with ruled_out antigens and their ruling out details
        """
        ruled_out_antigens = set()
        ruling_out_details = {}
        
        for rule in rules:
            if not rule.get('enabled', True):
                continue
            
            target_antigen = rule['target_antigen']
            
            # For ABSpecificRO rules, try with each suspected antibody
            if rule['rule_type'] == 'abspecific':
                if suspected_antibodies:
                    for suspected_antibody in suspected_antibodies:
                        is_satisfied, ruling_out_cells = self.evaluate_rule(rule, suspected_antibody)
                        if is_satisfied:
                            ruled_out_antigens.add(target_antigen)
                            if target_antigen not in ruling_out_details:
                                ruling_out_details[target_antigen] = []
                            ruling_out_details[target_antigen].extend(ruling_out_cells)
                            break  # Only need one satisfied rule per antigen
            else:
                # For other rule types, evaluate normally
                is_satisfied, ruling_out_cells = self.evaluate_rule(rule)
                if is_satisfied:
                    ruled_out_antigens.add(target_antigen)
                    if target_antigen not in ruling_out_details:
                        ruling_out_details[target_antigen] = []
                    ruling_out_details[target_antigen].extend(ruling_out_cells)
        
        return {
            'ruled_out_antigens': list(ruled_out_antigens),
            'ruling_out_details': ruling_out_details
        }


class AntibodyRuleValidator:
    """
    Validates antibody rules for conflicts and completeness.
    """
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    def validate_rules(self, rules: List[Dict]) -> Dict[str, List[str]]:
        """
        Validate a list of rules for conflicts and issues.
        
        Args:
            rules: List of rule dictionaries
            
        Returns:
            Dict with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []
        
        # Check for missing antigens
        missing_antigens = self._check_missing_antigens(rules)
        if missing_antigens:
            warnings.append(f"Antigens without rules: {', '.join(missing_antigens)}")
        
        # Check for conflicting rules
        conflicts = self._check_rule_conflicts(rules)
        if conflicts:
            errors.extend(conflicts)
        
        # Check for invalid rule data
        invalid_rules = self._check_invalid_rule_data(rules)
        if invalid_rules:
            errors.extend(invalid_rules)
        
        return {
            'errors': errors,
            'warnings': warnings
        }
    
    def _check_missing_antigens(self, rules: List[Dict]) -> List[str]:
        """Check which antigens in the database don't have rules."""
        from models import Antigen
        
        # Get all antigens from database
        db_antigens = {antigen.name for antigen in self.db_session.query(Antigen).all()}
        
        # Get antigens that have rules
        ruled_antigens = set()
        for rule in rules:
            ruled_antigens.add(rule['target_antigen'])
        
        return list(db_antigens - ruled_antigens)
    
    def _check_rule_conflicts(self, rules: List[Dict]) -> List[str]:
        """Check for conflicting rules."""
        conflicts = []
        
        # Group rules by target antigen
        antigen_rules = {}
        for rule in rules:
            target = rule['target_antigen']
            if target not in antigen_rules:
                antigen_rules[target] = []
            antigen_rules[target].append(rule)
        
        # Check for conflicts within each antigen's rules
        for antigen, antigen_rule_list in antigen_rules.items():
            if len(antigen_rule_list) > 1:
                # Check for contradictory conditions
                for i, rule1 in enumerate(antigen_rule_list):
                    for rule2 in antigen_rule_list[i+1:]:
                        if self._are_rules_contradictory(rule1, rule2):
                            conflicts.append(
                                f"Contradictory rules for antigen {antigen}: "
                                f"{rule1['rule_type']} vs {rule2['rule_type']}"
                            )
        
        return conflicts
    
    def _are_rules_contradictory(self, rule1: Dict, rule2: Dict) -> bool:
        """Check if two rules are contradictory."""
        # This is a simplified check - can be expanded based on specific requirements
        if rule1['rule_type'] == 'lowf' and rule2['rule_type'] == 'lowf':
            # Multiple lowf rules for same antigen are not contradictory
            return False
        
        # For now, consider rules of different types as potentially contradictory
        # This can be refined based on specific business logic
        return rule1['rule_type'] != rule2['rule_type']
    
    def _check_invalid_rule_data(self, rules: List[Dict]) -> List[str]:
        """Check for invalid rule data."""
        errors = []
        
        for i, rule in enumerate(rules):
            rule_type = rule.get('rule_type')
            rule_data = rule.get('rule_data', {})
            
            if rule_type == 'abspecific':
                required_fields = ['antibody', 'antigen1', 'antigen2', 'required_count']
                missing = [field for field in required_fields if field not in rule_data]
                if missing:
                    errors.append(f"Rule {i+1}: ABSpecificRO missing fields: {missing}")
            
            elif rule_type == 'homo':
                if 'antigen_pairs' not in rule_data or not rule_data['antigen_pairs']:
                    errors.append(f"Rule {i+1}: Homo rule missing antigen_pairs")
            
            elif rule_type == 'hetero':
                required_fields = ['antigen_a', 'antigen_b', 'required_count']
                missing = [field for field in required_fields if field not in rule_data]
                if missing:
                    errors.append(f"Rule {i+1}: Hetero rule missing fields: {missing}")
            
            elif rule_type == 'single':
                if 'antigens' not in rule_data or not rule_data['antigens']:
                    errors.append(f"Rule {i+1}: SingleAG rule missing antigens list")
            
            elif rule_type == 'lowf':
                if 'antigens' not in rule_data or not rule_data['antigens']:
                    errors.append(f"Rule {i+1}: LowF rule missing antigens list")
            
            else:
                errors.append(f"Rule {i+1}: Unknown rule type '{rule_type}'")
        
        return errors 