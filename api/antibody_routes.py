"""
Antibody identification routes.
This module handles all antibody identification and patient reaction endpoints.
"""

from flask import request, jsonify, render_template, current_app
from core.enhanced_antibody_identifier import EnhancedAntibodyIdentifier
from core.antibody_rule_validator import AntibodyRuleValidator

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
        except Exception:
            pass
        
        return render_template('antibody_id.html')

    @app.route('/api/patient-reactions', methods=['GET', 'POST'])
    def handle_patient_reactions():
        """Handle patient reaction operations."""
        if request.method == 'POST':
            try:
                data = request.json
                
                # Check if this is a batch request (multiple reactions) or single reaction
                if 'reactions' in data:
                    # Batch request - multiple reactions for one antigram
                    antigram_id = data.get('antigram_id')
                    reactions = data.get('reactions')
                    
                    if not antigram_id or not reactions:
                        return jsonify({"error": "Missing antigram_id or reactions"}), 400
                    
                    # Convert antigram_id to integer
                    try:
                        antigram_id = int(antigram_id)
                    except (ValueError, TypeError):
                        return jsonify({"error": "antigram_id must be a valid integer"}), 400
                    
                    # Validate reactions structure
                    for reaction_data in reactions:
                        if not all(key in reaction_data for key in ['cell_number', 'reaction']):
                            return jsonify({"error": "Each reaction must have cell_number and reaction"}), 400
                    
                    # Add all reactions
                    added_count = 0
                    for reaction_data in reactions:
                        cell_number = str(reaction_data['cell_number'])
                        reaction = reaction_data['reaction']
                        
                        # Only add valid reactions
                        if reaction in ['+', '0']:
                            patient_reaction_manager.add_reaction(antigram_id, cell_number, reaction)
                            added_count += 1
                    
                    # Commit changes after adding all reactions
                    patient_reaction_manager.commit_changes()
                    
                    # Run antibody identification and return results
                    abid_results = antibody_identification()
                    
                    return jsonify({
                        "message": f"Added {added_count} patient reactions successfully",
                        "added_count": added_count,
                        "abid_results": abid_results
                    }), 201
                    
                else:
                    # Single reaction request
                    antigram_id = data.get('antigram_id')
                    cell_number = data.get('cell_number')
                    reaction = data.get('reaction')

                    if not all([antigram_id, cell_number, reaction]):
                        return jsonify({"error": "Missing required fields"}), 400

                    # Convert antigram_id to integer
                    try:
                        antigram_id = int(antigram_id)
                    except (ValueError, TypeError):
                        return jsonify({"error": "antigram_id must be a valid integer"}), 400

                    # Convert cell_number to string to handle both numeric and alphabetic cell numbers
                    cell_number = str(cell_number)
                    
                    patient_reaction_manager.add_reaction(antigram_id, cell_number, reaction)
                    
                    # Commit changes after adding reaction
                    patient_reaction_manager.commit_changes()
                    
                    # Run antibody identification and return results
                    abid_results = antibody_identification()
                    
                    return jsonify({
                        "message": "Patient reaction added successfully",
                        "abid_results": abid_results
                    }), 201

            except Exception as e:
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
            except Exception:
                return jsonify({"error": "Internal Server Error"}), 500

    @app.route('/api/patient-reactions/batch', methods=['POST'])
    def batch_patient_reactions():
        """Handle batch patient reaction operations across multiple antigrams."""
        try:
            data = request.json
            antigram_reactions = data.get('antigram_reactions', [])
            
            if not antigram_reactions:
                return jsonify({"error": "No antigram reactions provided"}), 400
            
            total_added = 0
            
            for antigram_data in antigram_reactions:
                antigram_id = antigram_data.get('antigram_id')
                reactions = antigram_data.get('reactions', [])
                
                if not antigram_id or not reactions:
                    continue
                
                # Convert antigram_id to integer
                try:
                    antigram_id = int(antigram_id)
                except (ValueError, TypeError):
                    continue  # Skip invalid antigram_id
                
                # Add reactions for this antigram
                for reaction_data in reactions:
                    if all(key in reaction_data for key in ['cell_number', 'reaction']):
                        cell_number = str(reaction_data['cell_number'])
                        reaction = reaction_data['reaction']
                        
                        # Only add valid reactions
                        if reaction in ['+', '0']:
                            patient_reaction_manager.add_reaction(antigram_id, cell_number, reaction)
                            total_added += 1
            
            # Commit all changes
            patient_reaction_manager.commit_changes()
            
            # Run antibody identification and return results
            abid_results = antibody_identification()
            
            return jsonify({
                "message": f"Added {total_added} patient reactions across {len(antigram_reactions)} antigrams",
                "total_added": total_added,
                "antigrams_processed": len(antigram_reactions),
                "abid_results": abid_results
            }), 201
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/clear-patient-reactions', methods=['DELETE'])
    def clear_patient_reactions():
        """Clear all patient reactions and return antibody identification results."""
        try:
            patient_reaction_manager.clear_reactions()
            return antibody_identification()
        except Exception as e:
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

            # Convert antigram_id to integer
            try:
                antigram_id = int(antigram_id)
            except (ValueError, TypeError):
                return jsonify({"error": "antigram_id must be a valid integer"}), 400

            # Convert cell_number to string to handle both numeric and alphabetic cell numbers
            cell_number = str(cell_number)
            
            patient_reaction_manager.delete_reaction(antigram_id, cell_number)
            return antibody_identification()
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-identification', methods=['GET'])
    def get_antibody_identification():
        """Get antibody identification results."""
        try:
            results = antibody_identification()
            return jsonify(results), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/abid', methods=['GET'])
    def get_abid():
        """Get antibody identification results (alias for compatibility)."""
        try:
            results = antibody_identification()
            return jsonify(results), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/debug/patient-reactions', methods=['GET'])
    def debug_patient_reactions():
        """Debug endpoint to check patient reactions and rules."""
        try:
            # Check patient reactions
            patient_reactions_info = {
                "total_reactions": len(patient_reaction_manager.reactions_df),
                "reactions_by_antigram": {}
            }
            
            for antigram_id in antigram_manager.antigram_matrices.keys():
                reactions = patient_reaction_manager.get_reactions_for_antigram(antigram_id)
                metadata = antigram_manager.get_antigram_metadata(antigram_id)
                patient_reactions_info["reactions_by_antigram"][str(antigram_id)] = {
                    "lot_number": metadata['lot_number'],
                    "reactions": reactions
                }
            
            # Check rules
            from models import AntibodyRule
            rules = db_session.query(AntibodyRule).filter_by(enabled=True).all()
            rules_info = {
                "total_rules": len(rules),
                "rules_by_type": {}
            }
            
            for rule in rules:
                rule_type = rule.rule_type
                if rule_type not in rules_info["rules_by_type"]:
                    rules_info["rules_by_type"][rule_type] = []
                rules_info["rules_by_type"][rule_type].append({
                    "target_antigen": rule.target_antigen,
                    "description": rule.description
                })
            
            return jsonify({
                "patient_reactions": patient_reactions_info,
                "rules": rules_info
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # NEW: Rule validation endpoints
    @app.route('/api/validate-rules', methods=['GET'])
    def validate_rules():
        """Validate antibody rule coverage and return detailed analysis."""
        try:
            validator = AntibodyRuleValidator(antigram_manager, patient_reaction_manager, db_session)
            validation_results = validator.validate_rule_coverage()
            
            return jsonify(validation_results), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/validate-rules/summary', methods=['GET'])
    def validate_rules_summary():
        """Get a human-readable validation summary."""
        try:
            validator = AntibodyRuleValidator(antigram_manager, patient_reaction_manager, db_session)
            summary = validator.get_validation_summary()
            
            return jsonify({"summary": summary}), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/validate-rules/missing', methods=['GET'])
    def get_missing_rules():
        """Get list of antigens missing rules."""
        try:
            validator = AntibodyRuleValidator(antigram_manager, patient_reaction_manager, db_session)
            validation_results = validator.validate_rule_coverage()
            
            return jsonify({
                "missing_antigens": validation_results['missing_antigens'],
                "critical_missing": validation_results['critical_missing_antigens'],
                "warnings": validation_results['warnings']
            }), 200
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def antibody_identification():
        """Perform antibody identification using enhanced rule system."""
        try:
            # Create enhanced antibody identifier
            identifier = EnhancedAntibodyIdentifier(antigram_manager, patient_reaction_manager, db_session)
            
            # Load rules for debugging
            from models import AntibodyRule
            rules = db_session.query(AntibodyRule).filter_by(enabled=True).all()
            
            # Perform identification
            results = identifier.identify_antibodies()
            
            return results

        except Exception as e:
            return {
                "ruled_out": [],
                "stro": [],
                "matches": [],
                "progress": {},
                "ruled_out_details": {},
                "suspected_antibodies": []
            } 