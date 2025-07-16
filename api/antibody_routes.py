"""
Antibody identification routes.
This module handles all antibody identification and patient reaction endpoints.
"""

from flask import request, jsonify, render_template, current_app
from core.antibody_identifier_pandas import PandasAntibodyIdentifier
import logging

logger = logging.getLogger(__name__)

def register_antibody_routes(app, db_session):
    """Register all antibody identification routes."""
    
    # Get managers from app config
    antigram_manager = app.config['antigram_manager']
    patient_reaction_manager = app.config['patient_reaction_manager']

    @app.route('/antibody_id')
    def antibody_id_page():
        """Render the antibody identification page."""
        try:
            # Clear patient reactions when the page loads
            patient_reaction_manager.clear_reactions()
        except Exception as e:
            logger.error(f"Error clearing patient reactions: {e}")
        
        return render_template('antibody_id.html')

    @app.route('/api/patient-reactions', methods=['GET', 'POST'])
    def handle_patient_reactions():
        """Handle patient reaction operations."""
        if request.method == 'POST':
            try:
                data = request.json
                antigram_id = data.get('antigram_id')
                cell_number = data.get('cell_number')
                reaction = data.get('reaction')

                if not all([antigram_id, cell_number, reaction]):
                    return jsonify({"error": "Missing required fields"}), 400

                patient_reaction_manager.add_reaction(antigram_id, cell_number, reaction)
                
                # Commit changes after adding reaction
                patient_reaction_manager.commit_changes()
                
                return jsonify({"message": "Patient reaction added successfully"}), 201

            except Exception as e:
                logger.error(f"Error in handle_patient_reactions POST: {e}")
                return jsonify({"error": str(e)}), 500

        elif request.method == 'GET':
            try:
                # Get all patient reactions from pandas manager
                all_reactions = []
                for antigram_id in antigram_manager.antigram_matrices.keys():
                    reactions = patient_reaction_manager.get_reactions_for_antigram(antigram_id)
                    metadata = antigram_manager.get_antigram_metadata(antigram_id)
                    
                    for cell_number, patient_reaction in reactions.items():
                        all_reactions.append({
                            "lot_number": metadata['lot_number'],
                            "cell_number": cell_number,
                            "patient_reaction": patient_reaction,
                            "antigram_id": antigram_id,
                            "is_ruled_out": False,  # Not tracked in pandas version yet
                            "antigen": None
                        })

                if not all_reactions:
                    return jsonify({"message": "No patient reactions found.", "patient_reactions": []}), 200

                return jsonify({"patient_reactions": all_reactions}), 200
            except Exception as e:
                logger.error(f"Error in handle_patient_reactions GET: {e}")
                return jsonify({"error": "Internal Server Error"}), 500

    @app.route('/api/clear-patient-reactions', methods=['DELETE'])
    def clear_patient_reactions():
        """Clear all patient reactions and return antibody identification results."""
        try:
            patient_reaction_manager.clear_reactions()
            return antibody_identification()
        except Exception as e:
            logger.error(f"Error in clear_patient_reactions: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/delete-patient-reaction', methods=['DELETE'])
    def delete_patient_reaction():
        """Delete a specific patient reaction."""
        try:
            data = request.json
            antigram_id = data.get('antigram_id')
            cell_number = data.get('cell_number')

            if not all([antigram_id, cell_number]):
                return jsonify({"error": "Missing required fields"}), 400

            patient_reaction_manager.delete_reaction(antigram_id, cell_number)
            return antibody_identification()
        except Exception as e:
            logger.error(f"Error in delete_patient_reaction: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-identification', methods=['GET'])
    def get_antibody_identification():
        """Get antibody identification results."""
        try:
            results = antibody_identification()
            return jsonify(results), 200
        except Exception as e:
            logger.error(f"Error in get_antibody_identification: {e}")
            return jsonify({"error": str(e)}), 500

    def antibody_identification():
        """Perform antibody identification using pandas matrices."""
        try:
            # Create antibody identifier
            identifier = PandasAntibodyIdentifier(antigram_manager, patient_reaction_manager)
            
            # Perform identification
            results = identifier.identify_antibodies()
            
            return results

        except Exception as e:
            logger.error(f"Error in antibody identification: {str(e)}")
            return {
                "ruled_out": [],
                "stro": [],
                "matches": [],
                "progress": {}
            } 