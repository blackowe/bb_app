import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class PandasMatrixUtils:
    """
    Utility functions for pandas matrix operations in the antigram system.
    Provides helper methods for common matrix operations and data transformations.
    """
    
    @staticmethod
    def create_antigram_matrix_from_dict(data: Dict) -> pd.DataFrame:
        """
        Create an antigram matrix from a dictionary of cell data.
        
        Args:
            data: Dict with structure {cell_number: {antigen: reaction_value}}
            
        Returns:
            pandas.DataFrame: Matrix with cells as index and antigens as columns
        """
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data, orient='index')
        df.index.name = 'cell_number'
        
        # Fill missing values with '-'
        df = df.fillna('-')
        
        return df
    
    @staticmethod
    def matrix_to_dict(matrix: pd.DataFrame) -> Dict:
        """
        Convert a pandas matrix back to dictionary format.
        
        Args:
            matrix: pandas.DataFrame matrix
            
        Returns:
            Dict: Dictionary representation of the matrix
        """
        if matrix.empty:
            return {}
        
        return matrix.to_dict('index')
    
    @staticmethod
    def validate_matrix_format(matrix: pd.DataFrame) -> Dict:
        """
        Validate that a matrix has the correct format for antigram data.
        
        Args:
            matrix: pandas.DataFrame to validate
            
        Returns:
            Dict: Validation results with 'valid' boolean and 'errors' list
        """
        errors = []
        
        if matrix.empty:
            errors.append("Matrix is empty")
            return {'valid': False, 'errors': errors}
        
        # Check index name
        if matrix.index.name != 'cell_number':
            errors.append("Matrix index should be named 'cell_number'")
        
        # Check for required columns (basic antigens)
        required_antigens = ['D', 'C', 'E', 'e', 'c']
        missing_antigens = [antigen for antigen in required_antigens if antigen not in matrix.columns]
        if missing_antigens:
            errors.append(f"Missing required antigens: {missing_antigens}")
        
        # Check for valid reaction values
        valid_reactions = ['+', '0', '-', 'w+', 'w']
        invalid_values = []
        for col in matrix.columns:
            unique_values = matrix[col].unique()
            for value in unique_values:
                if pd.notna(value) and str(value) not in valid_reactions:
                    invalid_values.append(f"{col}: {value}")
        
        if invalid_values:
            errors.append(f"Invalid reaction values found: {invalid_values[:5]}...")  # Limit output
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def export_matrix_to_json(matrix: pd.DataFrame, filepath: str):
        """
        Export a matrix to JSON file.
        
        Args:
            matrix: pandas.DataFrame to export
            filepath: Path to save the JSON file
        """
        if not matrix.empty:
            matrix_dict = matrix.to_dict('index')
            with open(filepath, 'w') as f:
                json.dump(matrix_dict, f, indent=2, default=str)
            logger.info(f"Matrix exported to {filepath}")
        else:
            logger.warning("Matrix is empty, nothing to export")
    
    @staticmethod
    def import_matrix_from_json(filepath: str) -> pd.DataFrame:
        """
        Import a matrix from JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            pandas.DataFrame: Loaded matrix
        """
        try:
            with open(filepath, 'r') as f:
                matrix_dict = json.load(f)
            
            matrix = pd.DataFrame.from_dict(matrix_dict, orient='index')
            matrix.index.name = 'cell_number'
            return matrix
        except Exception as e:
            logger.error(f"Error importing matrix from {filepath}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_matrix_statistics(matrix: pd.DataFrame) -> Dict:
        """
        Get statistics about a matrix.
        
        Args:
            matrix: pandas.DataFrame to analyze
            
        Returns:
            Dict: Statistics about the matrix
        """
        if matrix.empty:
            return {
                'cell_count': 0,
                'antigen_count': 0,
                'total_reactions': 0,
                'positive_reactions': 0,
                'negative_reactions': 0,
                'weak_reactions': 0
            }
        
        stats = {
            'cell_count': len(matrix),
            'antigen_count': len(matrix.columns),
            'total_reactions': matrix.size,
            'positive_reactions': (matrix == '+').sum().sum(),
            'negative_reactions': (matrix == '0').sum().sum(),
            'weak_reactions': ((matrix == 'w+') | (matrix == 'w')).sum().sum()
        }
        
        return stats
    
    @staticmethod
    def find_pattern_matches(matrix: pd.DataFrame, pattern: Dict[str, str]) -> List[int]:
        """
        Find cells that match a specific antigen pattern.
        
        Args:
            matrix: pandas.DataFrame matrix
            pattern: Dict of {antigen: reaction_value}
            
        Returns:
            List[int]: Cell numbers that match the pattern
        """
        if matrix.empty or not pattern:
            return []
        
        # Create mask for each pattern condition
        mask = pd.Series(True, index=matrix.index)
        
        for antigen, expected_reaction in pattern.items():
            if antigen in matrix.columns:
                mask &= (matrix[antigen] == expected_reaction)
            else:
                # If antigen not in matrix, no cells can match
                return []
        
        return mask[mask].index.tolist()
    
    @staticmethod
    def get_antigen_summary(matrix: pd.DataFrame, antigen: str) -> Dict:
        """
        Get summary statistics for a specific antigen.
        
        Args:
            matrix: pandas.DataFrame matrix
            antigen: Antigen name to analyze
            
        Returns:
            Dict: Summary statistics for the antigen
        """
        if matrix.empty or antigen not in matrix.columns:
            return {
                'antigen': antigen,
                'total_cells': 0,
                'positive_cells': 0,
                'negative_cells': 0,
                'weak_positive_cells': 0,
                'missing_cells': 0
            }
        
        antigen_series = matrix[antigen]
        
        summary = {
            'antigen': antigen,
            'total_cells': len(antigen_series),
            'positive_cells': (antigen_series == '+').sum(),
            'negative_cells': (antigen_series == '0').sum(),
            'weak_positive_cells': ((antigen_series == 'w+') | (antigen_series == 'w')).sum(),
            'missing_cells': antigen_series.isna().sum()
        }
        
        return summary
    
    @staticmethod
    def get_antigen_column(matrix: pd.DataFrame, antigen: str) -> pd.Series:
        """
        Get a specific antigen column from the matrix.
        
        Args:
            matrix: pandas.DataFrame matrix
            antigen: Antigen name
            
        Returns:
            pandas.Series: Column for the specified antigen
        """
        if matrix.empty or antigen not in matrix.columns:
            return pd.Series(dtype=object)
        
        return matrix[antigen]
    
    @staticmethod
    def get_cell_row(matrix: pd.DataFrame, cell_number: int) -> pd.Series:
        """
        Get a specific cell row from the matrix.
        
        Args:
            matrix: pandas.DataFrame matrix
            cell_number: Cell number
            
        Returns:
            pandas.Series: Row for the specified cell
        """
        if matrix.empty or cell_number not in matrix.index:
            return pd.Series(dtype=object)
        
        return matrix.loc[cell_number]
    
    @staticmethod
    def count_reactions_by_type(matrix: pd.DataFrame, antigen: str) -> Dict[str, int]:
        """
        Count reactions by type for a specific antigen.
        
        Args:
            matrix: pandas.DataFrame matrix
            antigen: Antigen name
            
        Returns:
            Dict: Count of each reaction type
        """
        if matrix.empty or antigen not in matrix.columns:
            return {'+': 0, '0': 0, '-': 0}
        
        antigen_column = matrix[antigen]
        return antigen_column.value_counts().to_dict()
    
    @staticmethod
    def get_antigens_list(matrix: pd.DataFrame) -> List[str]:
        """
        Get list of all antigens in the matrix.
        
        Args:
            matrix: pandas.DataFrame matrix
            
        Returns:
            List of antigen names
        """
        if matrix.empty:
            return []
        
        return list(matrix.columns)
    
    @staticmethod
    def get_cell_numbers_list(matrix: pd.DataFrame) -> List[int]:
        """
        Get list of all cell numbers in the matrix.
        
        Args:
            matrix: pandas.DataFrame matrix
            
        Returns:
            List of cell numbers
        """
        if matrix.empty:
            return []
        
        return list(matrix.index)
    
    @staticmethod
    def filter_matrix_by_antigen(matrix: pd.DataFrame, antigen: str, reaction: str) -> pd.DataFrame:
        """
        Filter matrix to show only cells with a specific antigen reaction.
        
        Args:
            matrix: pandas.DataFrame matrix
            antigen: Antigen name
            reaction: Reaction value to filter by
            
        Returns:
            pandas.DataFrame: Filtered matrix
        """
        if matrix.empty or antigen not in matrix.columns:
            return pd.DataFrame()
        
        return matrix[matrix[antigen] == reaction]
    
    @staticmethod
    def merge_patient_reactions(matrix: pd.DataFrame, patient_reactions: Dict[int, str]) -> pd.DataFrame:
        """
        Merge patient reactions with the antigram matrix.
        
        Args:
            matrix: pandas.DataFrame matrix
            patient_reactions: Dict of {cell_number: patient_reaction}
            
        Returns:
            pandas.DataFrame: Matrix with patient reactions added as a column
        """
        if matrix.empty:
            return pd.DataFrame()
        
        # Create patient reactions series
        patient_series = pd.Series(patient_reactions, name='patient_reaction')
        
        # Merge with matrix
        merged = matrix.join(patient_series)
        
        return merged
    
    @staticmethod
    def create_reaction_summary(matrix: pd.DataFrame, patient_reactions: Dict[int, str]) -> Dict:
        """
        Create a summary of reactions for analysis.
        
        Args:
            matrix: pandas.DataFrame matrix
            patient_reactions: Dict of {cell_number: patient_reaction}
            
        Returns:
            Dict: Summary statistics
        """
        if matrix.empty:
            return {
                'total_cells': 0,
                'total_antigens': 0,
                'antigen_summary': {},
                'patient_reactions_count': 0
            }
        
        summary = {
            'total_cells': len(matrix),
            'total_antigens': len(matrix.columns),
            'antigen_summary': {},
            'patient_reactions_count': len(patient_reactions)
        }
        
        # Add antigen-specific summaries
        for antigen in matrix.columns:
            antigen_counts = PandasMatrixUtils.count_reactions_by_type(matrix, antigen)
            summary['antigen_summary'][antigen] = antigen_counts
        
        return summary
    
    @staticmethod
    def create_antigen_comparison_matrix(matrices: Dict[int, pd.DataFrame], antigen: str) -> pd.DataFrame:
        """
        Create a comparison matrix for a specific antigen across multiple antigrams.
        
        Args:
            matrices: Dict of {antigram_id: matrix}
            antigen: Antigen name to compare
            
        Returns:
            pandas.DataFrame: Comparison matrix
        """
        comparison_data = []
        
        for antigram_id, matrix in matrices.items():
            if antigen not in matrix.columns:
                continue
            
            antigen_column = matrix[antigen]
            row_data = {'antigram_id': antigram_id}
            
            for cell_number in antigen_column.index:
                row_data[f'cell_{cell_number}'] = antigen_column[cell_number]
            
            comparison_data.append(row_data)
        
        if not comparison_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(comparison_data)
        df.set_index('antigram_id', inplace=True)
        return df
    
    @staticmethod
    def calculate_antigen_statistics(matrices: Dict[int, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Calculate statistics for all antigens across all matrices.
        
        Args:
            matrices: Dict of {antigram_id: matrix}
            
        Returns:
            Dict: Statistics for each antigen
        """
        all_antigens = set()
        for matrix in matrices.values():
            all_antigens.update(matrix.columns)
        
        statistics = {}
        
        for antigen in all_antigens:
            antigen_stats = {
                'total_cells': 0,
                'positive_reactions': 0,
                'negative_reactions': 0,
                'missing_reactions': 0,
                'antigram_count': 0
            }
            
            for matrix in matrices.values():
                if antigen in matrix.columns:
                    antigen_stats['antigram_count'] += 1
                    antigen_column = matrix[antigen]
                    antigen_stats['total_cells'] += len(antigen_column)
                    antigen_stats['positive_reactions'] += (antigen_column == '+').sum()
                    antigen_stats['negative_reactions'] += (antigen_column == '0').sum()
                    antigen_stats['missing_reactions'] += (antigen_column == '-').sum()
            
            statistics[antigen] = antigen_stats
        
        return statistics


class MatrixVisualizationUtils:
    """
    Utilities for visualizing matrix data.
    """
    
    @staticmethod
    def create_heatmap_data(matrix: pd.DataFrame) -> Dict:
        """
        Prepare matrix data for heatmap visualization.
        
        Args:
            matrix: pandas.DataFrame matrix
            
        Returns:
            Dict: Data formatted for heatmap
        """
        if matrix.empty:
            return {
                'x': [],
                'y': [],
                'z': [],
                'colors': []
            }
        
        # Convert reaction values to numeric for visualization
        numeric_matrix = matrix.replace({
            '+': 1,
            '0': 0,
            '-': -1
        })
        
        return {
            'x': list(matrix.columns),  # Antigens
            'y': list(matrix.index),    # Cell numbers
            'z': numeric_matrix.values.tolist(),
            'colors': ['red', 'gray', 'blue']  # +, 0, -
        }
    
    @staticmethod
    def create_antigen_frequency_chart(matrices: Dict[int, pd.DataFrame]) -> Dict:
        """
        Create data for antigen frequency visualization.
        
        Args:
            matrices: Dict of {antigram_id: matrix}
            
        Returns:
            Dict: Data for frequency chart
        """
        statistics = PandasMatrixUtils.calculate_antigen_statistics(matrices)
        
        antigens = list(statistics.keys())
        positive_counts = [stats['positive_reactions'] for stats in statistics.values()]
        negative_counts = [stats['negative_reactions'] for stats in statistics.values()]
        
        return {
            'antigens': antigens,
            'positive_reactions': positive_counts,
            'negative_reactions': negative_counts
        } 