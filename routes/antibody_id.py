from flask import request, jsonify, render_template
from models import Cell, PatientReactionProfile, Reaction, Antigram

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

                # Get cells for the antigram
                cells = db_session.query(Cell).filter_by(antigram_id=antigram_id).all()
                cell_map = {cell.cell_number: cell.id for cell in cells}

                if not cell_map:
                    return jsonify({"error": "No matching cells found for antigram."}), 404

                valid_reactions = [r for r in reactions if r.get('patient_rxn') in ["+", "0"]]

                if not valid_reactions:
                    return jsonify({"message": "No valid reactions to save."}), 200

                # Clear existing reactions for the provided cells
                valid_cell_ids = [cell_map[r['cell_number']] for r in valid_reactions if r['cell_number'] in cell_map]
                if valid_cell_ids:
                    db_session.query(PatientReactionProfile).filter(
                        PatientReactionProfile.cell_id.in_(valid_cell_ids)
                    ).delete()

                # Save new reactions
                for reaction in valid_reactions:
                    cell_id = cell_map[reaction['cell_number']]
                    new_reaction = PatientReactionProfile(cell_id=cell_id, patient_rxn=reaction['patient_rxn'])
                    db_session.add(new_reaction)

                db_session.commit()

                return jsonify({"message": f"Saved {len(valid_reactions)} reactions!"}), 200

            except Exception as e:
                db_session.rollback()
                return jsonify({"error": str(e)}), 500

        elif request.method == 'GET':
            try:
                reactions = db_session.query(PatientReactionProfile).all()
                if not reactions:
                    return jsonify({"patient_reactions": []}), 200

                response_data = [
                    {
                        "lot_number": r.cell.antigram.lot_number,
                        "cell_number": r.cell.cell_number,
                        "patient_reaction": r.patient_rxn
                    } for r in reactions
                ]

                return jsonify({"patient_reactions": response_data}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500


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
            ruled_out_mapping = {}  # Maps ruled-out antigens to cell numbers and lot
            antigen_presence_map = {}

            # Define clinically insignificant antibodies
            insignificant_antigens = {"Cw", "Kpa", "Kpb", "Jsa", "Jsb", "Lua", "Lub"}

            # Define antigen pairs (homozygous ruling logic)
            antigen_pairs = {
                "C": "c", "E": "e", "S": "s", "M": "N",
                "Fya": "Fyb", "Jka": "Jkb", "K": "k", "Lea": "Leb"
            }

            # Step 1: Process each patient reaction
            for reaction in patient_reactions:
                cell = db_session.query(Cell).filter_by(id=reaction.cell_id).first()
                if not cell:
                    continue

                cell_reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()
                for r in cell_reactions:
                    antigen_presence_map.setdefault(r.antigen, []).append({
                        "cell_id": cell.id,
                        "lot_number": cell.antigram.lot_number,
                        "cell_number": cell.cell_number,
                        "reaction_value": r.reaction_value,
                        "patient_rxn": reaction.patient_rxn,
                        "homozygous": is_homozygous(r, cell_reactions, antigen_pairs)
                    })

            # Step 2: Remove clinically insignificant antibodies
            antigen_presence_map = {
                antigen: data for antigen, data in antigen_presence_map.items()
                if antigen not in insignificant_antigens
            }

            # Step 3-4: Rule out antigens based on negative patient reactions
            for antigen, details in antigen_presence_map.items():
                ruled_out_flag, stro_flag, match_flag, rule_out_cells = process_antigen(antigen, details, antigen_pairs)

                if ruled_out_flag:
                    ruled_out.add(antigen)
                    ruled_out_mapping[antigen] = [
                        {"lot_number": c["lot_number"], "cell_number": c["cell_number"]}
                        for c in rule_out_cells
                    ]
                elif stro_flag:
                    still_to_rule_out.add(antigen)
                elif match_flag:
                    match_candidates.add(antigen)

            # Step 5: Apply three-pos three-neg rule for match validation
            match_candidates = apply_three_pos_neg_rule(match_candidates, antigen_presence_map)

            # Step 6: Ensure correct categorization
            for antigen in antigen_presence_map:
                if antigen not in match_candidates and antigen not in still_to_rule_out:
                    ruled_out.add(antigen)

            still_to_rule_out -= ruled_out
            ruled_out -= match_candidates

            print("✅ antibody_identification completed successfully!")
            return jsonify({
                "ruled_out": list(ruled_out),
                "ruled_out_details": ruled_out_mapping,
                "still_to_rule_out": list(still_to_rule_out),
                "match": list(match_candidates)
            }), 200

        except Exception as e:
            print(f"❌ Error in antibody_identification: {str(e)}")
            return jsonify({"error": str(e)}), 500


    def is_homozygous(reaction, cell_reactions, antigen_pairs):
        """Check if an antigen is homozygous positive."""
        paired_antigen = antigen_pairs.get(reaction.antigen, None)
        if paired_antigen:
            paired_reaction = next((r for r in cell_reactions if r.antigen == paired_antigen), None)
            return paired_reaction and paired_reaction.reaction_value == "0"
        return reaction.reaction_value == '++'


    def process_antigen(antigen, details, antigen_pairs):
        """Determine if an antigen is ruled out, still to rule out, or a match."""
        ruled_out_flag = False
        stro_flag = False
        match_flag = True
        homozygous_count = 0
        heterozygous_count = 0
        rule_out_cells = []

        for detail in details:
            patient_rxn, reaction_value, homozygous = detail["patient_rxn"], detail["reaction_value"], detail["homozygous"]

            if homozygous:
                homozygous_count += 1
            else:
                heterozygous_count += 1

            # Step 4: Rule out based on homozygous positive cells
            if patient_rxn == "0" and reaction_value == "+":
                if homozygous:
                    ruled_out_flag = True
                    rule_out_cells.append(detail)
                    break  # Stop once we confirm ruling out
                else:
                    stro_flag = True  # Keep in STRO if heterozygous
            elif patient_rxn == "+" and reaction_value != "+":
                match_flag = False

        return ruled_out_flag, stro_flag, match_flag, rule_out_cells


    def apply_three_pos_neg_rule(match_candidates, antigen_presence_map):
        """Ensure valid matches meet the 3-pos 3-neg rule."""
        valid_matches = set()

        for antigen in match_candidates:
            positives = sum(1 for d in antigen_presence_map[antigen] if d["patient_rxn"] == "+")
            negatives = sum(1 for d in antigen_presence_map[antigen] if d["patient_rxn"] == "0")

            if positives >= 2 and negatives >= 2:
                valid_matches.add(antigen)

        return valid_matches