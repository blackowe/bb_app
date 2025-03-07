from flask import request, jsonify, render_template
from models import Cell, PatientReactionProfile, Reaction, AntigenPair, AntigenRuleOut

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

                # **Delete all existing reactions** before inserting new ones
                if existing_reactions:
                    db_session.query(PatientReactionProfile).filter(
                        PatientReactionProfile.cell.has(antigram_id=antigram_id)
                    ).delete()

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
                        new_reaction = PatientReactionProfile(cell_id=cell_id, patient_rxn=reaction['patient_rxn'])
                        db_session.add(new_reaction)

                db_session.commit()

                # ✅ **Trigger antibody identification after update**
                return antibody_identification()

            except Exception as e:
                db_session.rollback()
                return jsonify({"error": str(e)}), 500

        elif request.method == 'GET':
            try:
                reactions = db_session.query(PatientReactionProfile).all()
                
                if not reactions:
                    return jsonify({"message": "No patient reactions found.", "patient_reactions": []}), 200

                # Include antigram_id in the response data
                response_data = [
                    {
                        "lot_number": r.cell.antigram.lot_number if r.cell else "Unknown",
                        "cell_number": r.cell.cell_number if r.cell else "Unknown",
                        "patient_reaction": r.patient_rxn,
                        "antigram_id": r.cell.antigram_id if r.cell else None
                    } for r in reactions if r.cell is not None
                ]

                return jsonify({"patient_reactions": response_data}), 200
            except Exception as e:
                print(f"❌ Error in handle_patient_reactions GET: {e}")
                return jsonify({"error": "Internal Server Error"}), 500



    @app.route('/api/clear-patient-reactions', methods=['DELETE'])
    def clear_patient_reactions():
        try:
            # Delete all records from the PatientReactionProfile table
            db_session.query(PatientReactionProfile).delete()
            db_session.commit()

            # Trigger antibody identification after clearing reactions
            return antibody_identification()

        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/patient-reactions/<int:antigram_id>/<int:cell_number>', methods=['DELETE'])
    def delete_patient_reaction(antigram_id, cell_number):
        try:
            # Find the cell by antigram ID and cell number
            cell = db_session.query(Cell).filter_by(antigram_id=antigram_id, cell_number=cell_number).first()

            if cell:
                # Delete the associated reaction
                db_session.query(PatientReactionProfile).filter_by(cell_id=cell.id).delete()
                db_session.commit()

                # Trigger antibody identification after deleting reactions
                return antibody_identification()
            else:
                return jsonify({"error": "Cell not found."}), 404
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/abid', methods=['GET'])
    def antibody_identification():
        print("✅ antibody_identification() route was hit!")

        try:
            patient_reactions = db_session.query(PatientReactionProfile).all()
            if not patient_reactions:
                return jsonify({"error": "No patient reactions found"}), 404

            ruled_out = set()
            still_to_rule_out = set()
            match_candidates = set()
            ruled_out_mapping = {}
            antigen_presence_map = {}

            # Define clinically insignificant antibodies
            insignificant_antigens = {"Cw", "Kpa", "Kpb", "Jsa", "Jsb", "Lua", "Lub"}

            # Step 1: Process each patient reaction and build antigen presence map
            for reaction in patient_reactions:
                cell = db_session.query(Cell).filter_by(id=reaction.cell_id).first()
                if not cell:
                    continue

                cell_reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()
                
                # Process each antigen in the cell
                for r in cell_reactions:
                    if not isinstance(r, Reaction):
                        continue

                    # Skip clinically insignificant antigens
                    if r.antigen in insignificant_antigens:
                        continue

                    # Process rule-out logic
                    is_ruled_out, rule_type, rule_details = process_rule_out(
                        r.antigen, cell_reactions, reaction.patient_rxn, db_session
                    )

                    if is_ruled_out:
                        # Create rule-out record
                        rule_out = AntigenRuleOut(
                            antigen=r.antigen,
                            cell_id=cell.id,
                            rule_type=rule_type,
                            paired_antigen=rule_details["paired_antigen"] if rule_details else None,
                            patient_reaction=reaction.patient_rxn,
                            cell_reaction=r.reaction_value,
                            paired_reaction=rule_details["paired_reaction"] if rule_details else None
                        )
                        db_session.add(rule_out)
                        
                        # Check if we've met the required count for rule-out
                        if track_rule_out_progress(r.antigen, rule_type, cell, db_session):
                            ruled_out.add(r.antigen)
                            if r.antigen not in ruled_out_mapping:
                                ruled_out_mapping[r.antigen] = []
                            ruled_out_mapping[r.antigen].append({
                                "lot_number": cell.antigram.lot_number,
                                "cell_number": cell.cell_number,
                                "rule_type": rule_type
                            })
                    else:
                        # Track for potential matches
                        antigen_presence_map.setdefault(r.antigen, []).append({
                            "cell_id": cell.id,
                            "lot_number": cell.antigram.lot_number,
                            "cell_number": cell.cell_number,
                            "reaction_value": r.reaction_value,
                            "patient_rxn": reaction.patient_rxn
                        })

            # Step 2: Process potential matches
            for antigen, details in antigen_presence_map.items():
                if antigen in ruled_out:
                    continue

                # Check for match pattern
                valid_pattern = True
                has_positive = False
                has_negative = False

                # First check if all positive antigen reactions match with positive patient reactions
                positive_antigen_cells = [d for d in details if d["reaction_value"] == "+"]
                for detail in positive_antigen_cells:
                    if detail["patient_rxn"] != "+":
                        valid_pattern = False
                        break
                    has_positive = True

                # Then check if we have some negative reactions
                negative_reactions = [d for d in details if d["patient_rxn"] == "0"]
                if negative_reactions:
                    has_negative = True

                if valid_pattern and has_positive and has_negative:
                    match_candidates.add(antigen)
                else:
                    still_to_rule_out.add(antigen)

            # Step 3: Apply three-pos three-neg rule for match validation
            valid_matches = set()
            for antigen in match_candidates:
                details = antigen_presence_map[antigen]
                positives = sum(1 for d in details if d["patient_rxn"] == "+")
                negatives = sum(1 for d in details if d["patient_rxn"] == "0")

                if positives >= 2 and negatives >= 2:
                    valid_matches.add(antigen)

            # Commit any new rule-out records
            db_session.commit()

            # Final categorization cleanup
            still_to_rule_out -= ruled_out
            still_to_rule_out -= valid_matches

            print("✅ antibody_identification completed successfully!")
            return jsonify({
                "ruled_out": list(ruled_out),
                "ruled_out_details": ruled_out_mapping,
                "still_to_rule_out": list(still_to_rule_out),
                "match": list(valid_matches)
            }), 200

        except Exception as e:
            db_session.rollback()
            print(f"❌ Error in antibody_identification: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def is_homozygous(antigen, cell_reactions, antigen_pairs):
        """Determine if an antigen is homozygous based on paired antigen status."""
        paired_antigen = antigen_pairs.get(antigen, None)
        found_homozygous = False

        if not isinstance(cell_reactions, list):  # ✅ Ensure cell_reactions is always a list
            raise TypeError(f"Expected list for cell_reactions, but got {type(cell_reactions)}")

        for reaction in cell_reactions:
            if not isinstance(reaction, Reaction):  # ✅ Ensure we are iterating reactions
                continue
            
            if reaction.antigen != antigen:
                continue
            
            paired_reaction = next((r for r in cell_reactions if r.antigen == paired_antigen), None)

            if paired_reaction:
                # ✅ Homozygous if antigen is "+" and its pair is "0"
                if reaction.reaction_value == "+" and paired_reaction.reaction_value == "0":
                    found_homozygous = True
                
                # ❌ If both antigen and its pair are "+", neither is homozygous
                if reaction.reaction_value == "+" and paired_reaction.reaction_value == "+":
                    return False  

        return found_homozygous

    def process_rule_out(antigen, cell_reactions, patient_rxn, db_session):
        """
        Process rule-out logic for a single antigen, considering homozygous, heterozygous, and single antigen rules.
        Returns (is_ruled_out, rule_out_type, rule_out_details)
        """
        # Skip processing if patient reaction is positive
        if patient_rxn != "0":
            return False, None, None
        
        # Get all rules for this antigen
        rules = db_session.query(AntigenPair).filter(
            ((AntigenPair.antigen1 == antigen) | (AntigenPair.antigen2 == antigen))
        ).all()
        
        # If no rules exist for this antigen, check if it's present in the cell
        if not rules:
            antigen_reaction = next((r for r in cell_reactions if r.antigen == antigen), None)
            if antigen_reaction and antigen_reaction.reaction_value == "+":
                return True, "single", {
                    "antigen": antigen,
                    "paired_antigen": None,
                    "antigen_reaction": antigen_reaction.reaction_value,
                    "paired_reaction": None
                }
            return False, None, None

        # First check for homozygous rules (they take precedence)
        for rule in rules:
            if rule.rule_type == 'homozygous':
                paired_antigen = rule.antigen2 if rule.antigen1 == antigen else rule.antigen1
                antigen_reaction = next((r for r in cell_reactions if r.antigen == antigen), None)
                paired_reaction = next((r for r in cell_reactions if r.antigen == paired_antigen), None)
                
                if antigen_reaction and paired_reaction:
                    # For homozygous rule-out, we need one positive and one negative
                    if antigen_reaction.reaction_value == "+" and paired_reaction.reaction_value == "0":
                        return True, "homozygous", {
                            "antigen": antigen,
                            "paired_antigen": paired_antigen,
                            "antigen_reaction": antigen_reaction.reaction_value,
                            "paired_reaction": paired_reaction.reaction_value
                        }
                    # If the paired antigen is positive and this one is negative, don't process further
                    elif antigen_reaction.reaction_value == "0" and paired_reaction.reaction_value == "+":
                        return False, None, None

        # Then check for single antigen rules
        for rule in rules:
            if rule.rule_type == 'single':
                antigen_reaction = next((r for r in cell_reactions if r.antigen == antigen), None)
                if antigen_reaction and antigen_reaction.reaction_value == "+":
                    return True, "single", {
                        "antigen": antigen,
                        "paired_antigen": None,
                        "antigen_reaction": antigen_reaction.reaction_value,
                        "paired_reaction": None
                    }

        # Finally check for heterozygous rules
        for rule in rules:
            if rule.rule_type == 'heterozygous':
                paired_antigen = rule.antigen2 if rule.antigen1 == antigen else rule.antigen1
                antigen_reaction = next((r for r in cell_reactions if r.antigen == antigen), None)
                paired_reaction = next((r for r in cell_reactions if r.antigen == paired_antigen), None)
                
                if antigen_reaction and paired_reaction:
                    if antigen_reaction.reaction_value == "+" and paired_reaction.reaction_value == "+":
                        return True, "heterozygous", {
                            "antigen": antigen,
                            "paired_antigen": paired_antigen,
                            "antigen_reaction": antigen_reaction.reaction_value,
                            "paired_reaction": paired_reaction.reaction_value
                        }
                    
        return False, None, None

    def track_rule_out_progress(antigen, rule_type, cell, db_session):
        """
        Track progress towards ruling out an antigen based on the required count.
        Returns True if the antigen has been fully ruled out.
        """
        # Get the rule configuration
        pair = db_session.query(AntigenPair).filter(
            ((AntigenPair.antigen1 == antigen) | (AntigenPair.antigen2 == antigen)) &
            (AntigenPair.rule_type == rule_type)
        ).first()
        
        if not pair:
            return False
        
        # Count existing rule-outs
        rule_out_count = db_session.query(AntigenRuleOut).filter(
            AntigenRuleOut.antigen == antigen,
            AntigenRuleOut.rule_type == rule_type
        ).count()
        
        return rule_out_count >= pair.required_count

    def apply_three_pos_neg_rule(match_candidates, antigen_presence_map):
        """Ensure valid matches meet the 3-pos 3-neg rule."""
        valid_matches = set()

        for antigen in match_candidates:
            positives = sum(1 for d in antigen_presence_map[antigen] if d["patient_rxn"] == "+")
            negatives = sum(1 for d in antigen_presence_map[antigen] if d["patient_rxn"] == "0")

            if positives >= 2 and negatives >= 2:
                valid_matches.add(antigen)

        return valid_matches

    def check_homozygous_rule_out(antigen, cell_reactions, antigen_pairs, db_session):
        """
        Check if an antigen can be ruled out based on homozygous expression.
        Returns (is_ruled_out, rule_out_details)
        """
        pair = db_session.query(AntigenPair).filter(
            ((AntigenPair.antigen1 == antigen) | (AntigenPair.antigen2 == antigen)) &
            (AntigenPair.rule_type == 'homozygous')
        ).first()
        
        if not pair:
            return False, None
        
        # Get the paired antigen
        paired_antigen = pair.antigen2 if pair.antigen1 == antigen else pair.antigen1
        
        # Find homozygous expression
        antigen_reaction = next((r for r in cell_reactions if r.antigen == antigen), None)
        paired_reaction = next((r for r in cell_reactions if r.antigen == paired_antigen), None)
        
        if not antigen_reaction or not paired_reaction:
            return False, None
        
        # Check for homozygous expression (one positive, one negative)
        is_homozygous = (
            (antigen_reaction.reaction_value == "+" and paired_reaction.reaction_value == "0") or
            (antigen_reaction.reaction_value == "0" and paired_reaction.reaction_value == "+")
        )
        
        if is_homozygous:
            return True, {
                "antigen": antigen,
                "paired_antigen": paired_antigen,
                "antigen_reaction": antigen_reaction.reaction_value,
                "paired_reaction": paired_reaction.reaction_value
            }
        
        return False, None

    def check_heterozygous_rule_out(antigen, cell_reactions, antigen_pairs, db_session):
        """
        Check if an antigen can be ruled out based on heterozygous expression.
        Returns (is_ruled_out, rule_out_details)
        """
        pair = db_session.query(AntigenPair).filter(
            ((AntigenPair.antigen1 == antigen) | (AntigenPair.antigen2 == antigen)) &
            (AntigenPair.rule_type == 'heterozygous')
        ).first()
        
        if not pair:
            return False, None
        
        # Get the paired antigen
        paired_antigen = pair.antigen2 if pair.antigen1 == antigen else pair.antigen1
        
        # Find heterozygous expression
        antigen_reaction = next((r for r in cell_reactions if r.antigen == antigen), None)
        paired_reaction = next((r for r in cell_reactions if r.antigen == paired_antigen), None)
        
        if not antigen_reaction or not paired_reaction:
            return False, None
        
        # Check for heterozygous expression (both positive)
        is_heterozygous = (antigen_reaction.reaction_value == "+" and paired_reaction.reaction_value == "+")
        
        if is_heterozygous:
            return True, {
                "antigen": antigen,
                "paired_antigen": paired_antigen,
                "antigen_reaction": antigen_reaction.reaction_value,
                "paired_reaction": paired_reaction.reaction_value
            }
        
        return False, None
