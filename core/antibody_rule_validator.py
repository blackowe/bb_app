import pandas as pd
from typing import Dict, List, Set, Tuple, Optional
from core.pandas_models import PandasAntigramManager, PandasPatientReactionManager
import logging

logger = logging.getLogger(__name__)


class AntibodyRuleValidator:
    """
    Comprehensive validator for antibody rules that ensures all antigens have proper rule coverage.
    """
    
    def __init__(self, antigram_manager: PandasAntigramManager, 
                 patient_reaction_manager: PandasPatientReactionManager,
                 db_session=None):
        self.antigram_manager = antigram_manager
        self.patient_reaction_manager = patient_reaction_manager
        self.db_session = db_session
    
    def validate_rule_coverage(self, rules: List[Dict] = None) -> Dict[str, any]:
        """
        Comprehensive validation of antibody rule coverage.
        
        Args:
            rules: List of antibody rules. If None, loads from database.
            
        Returns:
            Dict: Validation results with missing rules, warnings, and recommendations
        """
        if rules is None:
            rules = self._load_rules_from_database()
        
        # Get all antigens present in antigrams
        antigram_antigens = self._get_all_antigram_antigens()
        
        # Get antigens that have rules
        ruled_antigens = self._get_ruled_antigens(rules)
        
        # Find missing antigens
        missing_antigens = antigram_antigens - ruled_antigens
        
        # Analyze rule distribution
        rule_analysis = self._analyze_rule_distribution(rules)
        
        # Check for antigens with patient reactions but no rules
        antigens_with_reactions = self._get_antigens_with_patient_reactions()
        critical_missing = missing_antigens & antigens_with_reactions
        
        # Generate recommendations
        recommendations = self._generate_recommendations(missing_antigens, rule_analysis)
        
        return {
            'validation_passed': len(missing_antigens) == 0,
            'total_antigrams_analyzed': len(self.antigram_manager.antigram_matrices),
            'total_antigens_in_antigrams': len(antigram_antigens),
            'antigens_with_rules': len(ruled_antigens),
            'missing_antigens': sorted(list(missing_antigens)),
            'critical_missing_antigens': sorted(list(critical_missing)),
            'antigens_with_patient_reactions': sorted(list(antigens_with_reactions)),
            'rule_distribution': rule_analysis,
            'recommendations': recommendations,
            'warnings': self._generate_warnings(missing_antigens, critical_missing),
            'detailed_analysis': self._get_detailed_analysis(antigram_antigens, ruled_antigens, rules)
        }
    
    def _load_rules_from_database(self) -> List[Dict]:
        """Load antibody rules from database."""
        if not self.db_session:
            logger.warning("No database session available, using empty rules")
            return []
        
        try:
            from models import AntibodyRule
            rules = self.db_session.query(AntibodyRule).filter_by(enabled=True).all()
            return [rule.to_dict() for rule in rules]
        except Exception as e:
            logger.error(f"Error loading rules from database: {e}")
            return []
    
    def _get_all_antigram_antigens(self) -> Set[str]:
        """Get all unique antigens present in all antigrams."""
        all_antigens = set()
        for matrix in self.antigram_manager.antigram_matrices.values():
            all_antigens.update(matrix.columns)
        return all_antigens
    
    def _get_ruled_antigens(self, rules: List[Dict]) -> Set[str]:
        """Get all antigens that have rules targeting them."""
        ruled_antigens = set()
        for rule in rules:
            if rule.get('enabled', True):
                ruled_antigens.add(rule['target_antigen'])
        return ruled_antigens
    
    def _get_antigens_with_patient_reactions(self) -> Set[str]:
        """Get antigens that have patient reactions recorded."""
        antigens_with_reactions = set()
        
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            patient_reactions = self.patient_reaction_manager.get_reactions_for_antigram(antigram_id)
            
            if not patient_reactions:
                continue
            
            # Find antigens that are expressed in cells with patient reactions
            for cell_number, patient_reaction in patient_reactions.items():
                if cell_number in matrix.index:
                    cell_data = matrix.loc[cell_number]
                    for antigen, cell_reaction in cell_data.items():
                        if cell_reaction == '+':  # Cell expresses this antigen
                            antigens_with_reactions.add(antigen)
        
        return antigens_with_reactions
    
    def _analyze_rule_distribution(self, rules: List[Dict]) -> Dict[str, any]:
        """Analyze the distribution of rule types and target antigens."""
        rule_types = {}
        target_antigens = {}
        
        for rule in rules:
            if not rule.get('enabled', True):
                continue
            
            rule_type = rule['rule_type']
            target_antigen = rule['target_antigen']
            
            # Count rule types
            if rule_type not in rule_types:
                rule_types[rule_type] = []
            rule_types[rule_type].append(target_antigen)
            
            # Count target antigens
            if target_antigen not in target_antigens:
                target_antigens[target_antigen] = []
            target_antigens[target_antigen].append(rule_type)
        
        return {
            'rule_types': {rt: len(antigens) for rt, antigens in rule_types.items()},
            'target_antigens': {ta: rules for ta, rules in target_antigens.items()},
            'total_rules': len([r for r in rules if r.get('enabled', True)])
        }
    
    def _generate_recommendations(self, missing_antigens: Set[str], rule_analysis: Dict) -> List[str]:
        """Generate recommendations for missing rules."""
        recommendations = []
        
        if missing_antigens:
            recommendations.append(f"Missing rules for {len(missing_antigens)} antigens: {', '.join(sorted(missing_antigens))}")
            
            # Specific recommendations for common antigens
            for antigen in sorted(missing_antigens):
                if antigen in ['S', 's']:
                    recommendations.append(f"Add SingleAG rule for {antigen} or ensure it's covered by Homozygous rules")
                elif antigen in ['Fya', 'Fyb']:
                    recommendations.append(f"Add SingleAG rule for {antigen} or ensure it's covered by Homozygous rules")
                elif antigen in ['Jka', 'Jkb']:
                    recommendations.append(f"Add SingleAG rule for {antigen} or ensure it's covered by Homozygous rules")
                else:
                    recommendations.append(f"Add appropriate rule for {antigen} (SingleAG, Homozygous, or LowF)")
        
        # Check rule type distribution
        rule_types = rule_analysis.get('rule_types', {})
        if 'single' not in rule_types:
            recommendations.append("Consider adding SingleAG rules for antigens that can be ruled out by single expression")
        
        if 'homo' not in rule_types:
            recommendations.append("Consider adding Homozygous rules for antigen pairs")
        
        return recommendations
    
    def _generate_warnings(self, missing_antigens: Set[str], critical_missing: Set[str]) -> List[str]:
        """Generate warnings about missing rules."""
        warnings = []
        
        if critical_missing:
            warnings.append(f"CRITICAL: {len(critical_missing)} antigens with patient reactions have no rules: {', '.join(sorted(critical_missing))}")
            warnings.append("This may lead to incorrect antibody identification results")
        
        if missing_antigens:
            warnings.append(f"WARNING: {len(missing_antigens)} antigens in antigrams have no rules: {', '.join(sorted(missing_antigens))}")
            warnings.append("Consider adding rules for these antigens to improve antibody identification accuracy")
        
        return warnings
    
    def _get_detailed_analysis(self, antigram_antigens: Set[str], ruled_antigens: Set[str], rules: List[Dict]) -> Dict[str, any]:
        """Get detailed analysis of rule coverage."""
        detailed = {
            'antigens_by_status': {
                'has_rules': sorted(list(ruled_antigens)),
                'missing_rules': sorted(list(antigram_antigens - ruled_antigens)),
                'unused_rules': sorted(list(ruled_antigens - antigram_antigens))
            },
            'rule_coverage_percentage': len(ruled_antigens) / len(antigram_antigens) * 100 if antigram_antigens else 0,
            'antigram_details': self._get_antigram_antigen_details(),
            'rule_details': self._get_rule_details(rules)
        }
        
        return detailed
    
    def _get_antigram_antigen_details(self) -> Dict[str, any]:
        """Get detailed information about antigens in each antigram."""
        antigram_details = {}
        
        for antigram_id, matrix in self.antigram_manager.antigram_matrices.items():
            metadata = self.antigram_manager.get_antigram_metadata(antigram_id)
            antigram_details[str(antigram_id)] = {
                'lot_number': metadata.get('lot_number', 'Unknown'),
                'template_name': metadata.get('name', 'Unknown'),
                'antigens': sorted(list(matrix.columns)),
                'cell_count': len(matrix.index)
            }
        
        return antigram_details
    
    def _get_rule_details(self, rules: List[Dict]) -> Dict[str, any]:
        """Get detailed information about rules."""
        rule_details = {
            'by_type': {},
            'by_target': {}
        }
        
        for rule in rules:
            if not rule.get('enabled', True):
                continue
            
            rule_type = rule['rule_type']
            target_antigen = rule['target_antigen']
            
            # Group by rule type
            if rule_type not in rule_details['by_type']:
                rule_details['by_type'][rule_type] = []
            rule_details['by_type'][rule_type].append({
                'target_antigen': target_antigen,
                'description': rule.get('description', ''),
                'rule_data': rule.get('rule_data', {})
            })
            
            # Group by target antigen
            if target_antigen not in rule_details['by_target']:
                rule_details['by_target'][target_antigen] = []
            rule_details['by_target'][target_antigen].append({
                'rule_type': rule_type,
                'description': rule.get('description', ''),
                'rule_data': rule.get('rule_data', {})
            })
        
        return rule_details
    
    def get_validation_summary(self, rules: List[Dict] = None) -> str:
        """Get a human-readable validation summary."""
        validation = self.validate_rule_coverage(rules)
        
        summary = f"""
Antibody Rule Validation Summary
================================

Overall Status: {'✅ PASSED' if validation['validation_passed'] else '❌ FAILED'}

Coverage Statistics:
- Antigrams Analyzed: {validation['total_antigrams_analyzed']}
- Total Antigens in Antigrams: {validation['total_antigens_in_antigrams']}
- Antigens with Rules: {validation['antigens_with_rules']}
- Missing Rules: {len(validation['missing_antigens'])}
- Coverage: {validation['detailed_analysis']['rule_coverage_percentage']:.1f}%

Critical Issues:
{chr(10).join(validation['warnings']) if validation['warnings'] else 'None'}

Missing Antigens: {', '.join(validation['missing_antigens']) if validation['missing_antigens'] else 'None'}

Recommendations:
{chr(10).join(validation['recommendations']) if validation['recommendations'] else 'None'}
"""
        
        return summary.strip() 