from flask import request, jsonify, render_template
from models import Cell, PatientReactionProfile, Reaction, AntigenRule
import json

def register_antibody_id_routes(app, db_session):

    @app.route('/antibody_id', methods=['GET'])
    def antibody_id_page():
        try:
            # Clear patient reactions when the page loads
            db_session.query(PatientReactionProfile).delete()
            db_session.commit()
            print("✅ Patient reactions cleared on page load.")
        except Exception as e:
            db_session.rollback()
            print(f"❌ Error clearing patient reactions: {e}")
        
        return render_template('antibody_id.html')

    @app.route('/api/patient-reactions', methods=['GET', 'POST'])
    def handle_patient_reactions():
        if request.method == 'POST':
            try:
                data = request.json
                antigram_id = data.get('antigram_id')
                reactions = data.get('reactions', [])

                if not antigram_id or not isinstance(reactions, list):
                    return jsonify({"error": "Invalid request data"}), 400

                # Get all existing reactions for this antigram
                existing_reactions = db_session.query(PatientReactionProfile).filter(
                    PatientReactionProfile.cell.has(antigram_id=antigram_id)
                ).all()

                # Delete all existing reactions before inserting new ones
                if existing_reactions:
                    db_session.query(PatientReactionProfile).filter(
                        PatientReactionProfile.cell.has(antigram_id=antigram_id)
                    ).delete(synchronize_session=False)

                # Ensure only valid reactions are saved
                valid_reactions = [r for r in reactions if r.get('patient_rxn') in ["+", "0"]]

                if not valid_reactions:
                    db_session.commit()  # Commit deletion
                    return jsonify({"message": "No valid reactions to save.", "patient_reactions": []}), 200

                # Get cells for the antigram
                cells = db_session.query(Cell).filter_by(antigram_id=antigram_id).all()
                cell_map = {cell.cell_number: cell.id for cell in cells}

                if not cell_map:
                    return jsonify({"error": "No matching cells found for antigram."}), 404

                # Save new reactions
                for reaction in valid_reactions:
                    cell_id = cell_map.get(reaction['cell_number'])
                    if cell_id:
                        new_reaction = PatientReactionProfile(
                            cell_id=cell_id,
                            patient_rxn=reaction['patient_rxn'],
                            is_ruled_out=False,  # Initialize as not ruled out
                            antigen=None  # Initialize with no antigen ruled out
                        )
                        db_session.add(new_reaction)

                db_session.commit()

                # Trigger antibody identification after update
                return antibody_identification(db_session)

            except Exception as e:
                db_session.rollback()
                return jsonify({"error": str(e)}), 500

        elif request.method == 'GET':
            try:
                reactions = db_session.query(PatientReactionProfile).all()
                
                if not reactions:
                    return jsonify({"message": "No patient reactions found.", "patient_reactions": []}), 200

                response_data = [
                    {
                        "lot_number": r.cell.antigram.lot_number if r.cell else "Unknown",
                        "cell_number": r.cell.cell_number if r.cell else "Unknown",
                        "patient_reaction": r.patient_rxn,
                        "antigram_id": r.cell.antigram_id if r.cell else None,
                        "is_ruled_out": r.is_ruled_out,
                        "antigen": r.antigen
                    } for r in reactions if r.cell is not None
                ]

                return jsonify({"patient_reactions": response_data}), 200
            except Exception as e:
                print(f"❌ Error in handle_patient_reactions GET: {e}")
                return jsonify({"error": "Internal Server Error"}), 500

    @app.route('/api/clear-patient-reactions', methods=['DELETE'])
    def clear_patient_reactions():
        try:
            db_session.query(PatientReactionProfile).delete()
            db_session.commit()
            return antibody_identification(db_session)
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/patient-reactions/<int:antigram_id>/<int:cell_number>', methods=['DELETE'])
    def delete_patient_reaction(antigram_id, cell_number):
        try:
            cell = db_session.query(Cell).filter_by(antigram_id=antigram_id, cell_number=cell_number).first()
            if cell:
                db_session.query(PatientReactionProfile).filter_by(cell_id=cell.id).delete()
                db_session.commit()
                return antibody_identification(db_session)
            else:
                return jsonify({"error": "Cell not found."}), 404
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/abid', methods=['GET'])
    def get_antibody_identification():
        """
        Get the current antibody identification results.
        """
        try:
            results = antibody_identification(db_session)
            return jsonify(results), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

def antibody_identification(db_session):
    """Process patient reactions to identify ruled-out antigens and potential matches."""
    try:
        # Reset all is_ruled_out flags
        db_session.query(PatientReactionProfile).update({"is_ruled_out": False, "antigen": None})
        db_session.commit()
        
        # Get all patient reactions
        patient_reactions = db_session.query(PatientReactionProfile).all()
        
        if not patient_reactions:
            return {
                "ruled_out": [],
                "potential_matches": [],
                "progress": {}
            }
        
        # Initialize sets for tracking
        ruled_out = set()
        potential_matches = set()
        progress = {}
        
        # Get all unique antigens from reactions and rules
        all_antigens = set()
        antigen_reactions = {}  # Track reactions for each antigen
        
        # First, get antigens from cell reactions
        for reaction in patient_reactions:
            cell = db_session.query(Cell).get(reaction.cell_id)
            if cell:
                for r in cell.reactions:
                    all_antigens.add(r.antigen)
                    if r.antigen not in antigen_reactions:
                        antigen_reactions[r.antigen] = []
                    antigen_reactions[r.antigen].append({
                        "cell_reaction": r.reaction_value,
                        "patient_reaction": reaction.patient_rxn,
                        "cell_number": cell.cell_number,
                        "lot_number": cell.antigram.lot_number
                    })
        
        # Then, get antigens from rules to ensure we don't miss any
        rules = db_session.query(AntigenRule).all()
        for rule in rules:
            all_antigens.add(rule.target_antigen)
        
        # Process each antigen
        for antigen in all_antigens:
            # Skip if already ruled out
            if antigen in ruled_out:
                continue

            # Track progress for this antigen
            progress[antigen] = {
                "total_rule_outs": 0,
                "required_count": 0,
                "is_complete": False
            }
            
            # Get rules for this antigen
            antigen_rules = db_session.query(AntigenRule).filter(
                AntigenRule.target_antigen == antigen
            ).all()
            
            if not antigen_rules:
                # If no rules but we have reactions, consider it for potential matches
                if antigen in antigen_reactions:
                    has_positive = any(r["patient_reaction"] == "+" for r in antigen_reactions[antigen])
                    if has_positive:
                        potential_matches.add(antigen)
                continue

            # Set required count based on rules
            progress[antigen]["required_count"] = max(rule.required_count for rule in antigen_rules)
            
            # Process each cell's reactions
            for reaction in patient_reactions:
                cell = db_session.query(Cell).get(reaction.cell_id)
                if not cell:
                    continue

                # Process rule-out logic
                is_ruled_out, rule_details = process_rule_out(db_session, reaction, antigen)

                if is_ruled_out:
                    # Track rule-out progress
                    is_complete, total_rule_outs = track_rule_out_progress(
                        antigen, rule_details, db_session
                    )
                    
                    # Update progress
                    progress[antigen]["total_rule_outs"] = total_rule_outs
                    progress[antigen]["is_complete"] = is_complete
                    
                    # If complete, add to ruled out set
                    if is_complete:
                        ruled_out.add(antigen)
                        break
            
            # If not ruled out and has positive reactions, check if it meets potential match criteria
            if antigen not in ruled_out and antigen in antigen_reactions:
                # Count positive and negative reactions
                positive_count = sum(1 for r in antigen_reactions[antigen] if r["patient_reaction"] == "+")
                negative_count = sum(1 for r in antigen_reactions[antigen] if r["patient_reaction"] == "0")
                
                # Apply 2-pos 2-neg rule
                if positive_count >= 2 and negative_count >= 2:
                    potential_matches.add(antigen)
        
        return {
            "ruled_out": sorted(list(ruled_out)),
            "potential_matches": sorted(list(potential_matches)),
            "progress": progress
        }

    except Exception as e:
        print(f"Error in antibody identification: {str(e)}")
        return {
            "ruled_out": [],
            "potential_matches": [],
            "progress": {}
        }

def process_rule_out(db_session, patient_reaction, antigen_name):
    """Process rule-out for a specific antigen based on patient reaction."""
    try:
        # Get all rules for this antigen
        rules = db_session.query(AntigenRule).filter_by(target_antigen=antigen_name).all()
        
        for rule in rules:
            rule_conditions = rule.conditions
            
            # Check if this is a composite rule
            if rule.rule_type == 'composite':
                # For composite rules, we need to check multiple conditions
                conditions_met = 0
                required_count = rule_conditions.get('required_count', 1)
                
                for condition in rule_conditions['conditions']:
                    # Check if the condition is met
                    if check_condition(db_session, patient_reaction, condition):
                        conditions_met += 1
                
                # Check if we met the required number of conditions
                if conditions_met >= required_count:
                    # Mark this cell as ruling out the antigen
                    mark_cell_as_ruling_out(db_session, patient_reaction.cell_id, antigen_name, rule.id)
                    return True, {"rule_type": "composite", "conditions": rule_conditions}
                    
            else:  # Standard rule
                # For standard rules, we check a single condition
                condition = rule_conditions['conditions'][0]
                if check_condition(db_session, patient_reaction, condition):
                    # Mark this cell as ruling out the antigen
                    mark_cell_as_ruling_out(db_session, patient_reaction.cell_id, antigen_name, rule.id)
                    return True, {"rule_type": "standard", "conditions": rule_conditions}
                    
        return False, None
        
    except Exception as e:
        print(f"Error processing rule: {str(e)}")
        return False, None

def check_condition(db_session, patient_reaction, condition):
    """Check if a specific condition is met for a patient reaction."""
    try:
        # Get the cell's reactions
        cell = db_session.query(Cell).get(patient_reaction.cell_id)
        if not cell:
            return False
            
        # Check if patient reaction matches
        if patient_reaction.patient_rxn != condition['patient_reaction']:
            return False
            
        # Check if cell has the required antigen with correct reaction
        cell_reaction = next((r for r in cell.reactions if r.antigen == condition['antigen']), None)
        if not cell_reaction or cell_reaction.reaction_value != condition['cell_reaction']:
            return False
            
        # Check paired conditions if they exist
        if 'paired_conditions' in condition:
            for paired_condition in condition['paired_conditions']:
                paired_reaction = next((r for r in cell.reactions if r.antigen == paired_condition['antigen']), None)
                if not paired_reaction or paired_reaction.reaction_value != paired_condition['cell_reaction']:
                    return False
                    
        return True
        
    except Exception as e:
        print(f"Error checking condition: {str(e)}")
        return False

def mark_cell_as_ruling_out(db_session, cell_id, antigen_name, rule_id):
    """Mark a cell as ruling out a specific antigen."""
    try:
        # Update the patient reaction profile
        profile = db_session.query(PatientReactionProfile).filter_by(cell_id=cell_id).first()
        if profile:
            profile.is_ruled_out = True
            profile.antigen = antigen_name
            db_session.commit()
            
    except Exception as e:
        print(f"Error marking cell as ruling out: {str(e)}")
        db_session.rollback()

def track_rule_out_progress(antigen, rule_details, db_session):
    """Track progress towards ruling out an antigen."""
    try:
        if not rule_details:
            return False, 0
            
        # Count existing rule-outs for this antigen
        existing_rule_outs = db_session.query(PatientReactionProfile).filter_by(
            antigen=antigen,
            is_ruled_out=True
        ).count()
        
        # Get the rule to check required count
        rule = db_session.query(AntigenRule).filter_by(target_antigen=antigen).first()
        if not rule:
            return False, 0
            
        # Check if we've met the required count
        is_complete = existing_rule_outs >= rule.required_count
        return is_complete, existing_rule_outs
        
    except Exception as e:
        print(f"Error tracking rule out progress: {str(e)}")
        return False, 0

def check_homozygous_rule_out(antigen, cell_reactions, antigen_pairs, db_session):
    """Check if an antigen can be ruled out based on homozygous expression."""
    rules = db_session.query(AntigenRule).filter_by(
        target_antigen=antigen,
        rule_type='homozygous'
    ).all()

    if not rules:
        return False, None
    
    for rule in rules:
        conditions = rule.conditions
        antigen_reaction = next((r for r in cell_reactions if r.antigen == conditions["antigen"]), None)
        paired_reaction = next((r for r in cell_reactions if r.antigen == conditions["paired_antigen"]), None)
        
        if not antigen_reaction or not paired_reaction:
            continue
        
        if (antigen_reaction.reaction_value == conditions["cell_reaction"] and 
            paired_reaction.reaction_value == conditions["paired_reaction"]):
            return True, {
                "antigen": antigen,
                "paired_antigen": conditions["paired_antigen"],
                "antigen_reaction": antigen_reaction.reaction_value,
                "paired_reaction": paired_reaction.reaction_value,
                "rule_type": "homozygous"
            }
        
        return False, None

def check_heterozygous_rule_out(antigen, cell_reactions, antigen_pairs, db_session):
    """Check if an antigen can be ruled out based on heterozygous expression."""
    rules = db_session.query(AntigenRule).filter_by(
        target_antigen=antigen,
        rule_type='heterozygous'
    ).all()

    if not rules:
        return False, None
    
    for rule in rules:
        conditions = rule.conditions
        antigen_reaction = next((r for r in cell_reactions if r.antigen == conditions["antigen"]), None)
        paired_reaction = next((r for r in cell_reactions if r.antigen == conditions["paired_antigen"]), None)
        
        if not antigen_reaction or not paired_reaction:
            continue
        
        if (antigen_reaction.reaction_value == conditions["cell_reaction"] and 
            paired_reaction.reaction_value == conditions["paired_reaction"]):
            return True, {
                "antigen": antigen,
                "paired_antigen": conditions["paired_antigen"],
                "antigen_reaction": antigen_reaction.reaction_value,
                "paired_reaction": paired_reaction.reaction_value,
                "rule_type": "heterozygous"
            }
        
        return False, None