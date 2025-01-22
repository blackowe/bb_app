from flask import request, jsonify, render_template
from models import Cell, PatientReactionProfile, Antigram, Reaction

def register_antibody_id_routes(app, db_session):

    
    @app.route('/antibody_id', methods=['GET'])
    def antibody_id_page():
        return render_template('antibody_id.html')

    @app.route('/api/antigrams', methods=['GET'])
    def get_antigrams():
        # Get the search query from the request
        search_query = request.args.get('search', '').strip()

        # Ensure a valid search query
        if not search_query:
            return jsonify({"error": "Search query cannot be empty"}), 400

        try:
            # Use ilike for case-insensitive partial matching
            antigrams = db_session.query(Antigram).filter(
                Antigram.lot_number.ilike(f"%{search_query}%")
            ).all()

            # Serialize the results to JSON
            return jsonify([{
                "id": antigram.id,
                "lot_number": antigram.lot_number,
                "name": antigram.name,
                "expiration_date": antigram.expiration_date.strftime("%Y-%m-%d"),
            } for antigram in antigrams]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    

    @app.route('/api/antigram/<int:antigram_id>/cells', methods=['GET'])
    def get_cells_for_antigram(antigram_id):
        cells = db_session.query(Cell).filter_by(antigram_id=antigram_id).all()
        return jsonify([cell.to_dict() for cell in cells])

    @app.route('/api/patient-reaction', methods=['POST'])
    def save_patient_reactions():
        try:
            data = request.json
            antigram_id = data.get('antigram_id')
            reactions = data.get('reactions', [])

            # Clear existing reactions for this antigram
            cells = db_session.query(Cell).filter_by(antigram_id=antigram_id).all()
            cell_ids = [cell.id for cell in cells]
            db_session.query(PatientReactionProfile).filter(PatientReactionProfile.cell_id.in_(cell_ids)).delete()

            # Save new reactions
            for reaction in reactions:
                cell_number = reaction['cell_number']
                patient_rxn = reaction['patient_rxn']

                cell = db_session.query(Cell).filter_by(antigram_id=antigram_id, cell_number=cell_number).first()
                if cell:
                    new_reaction = PatientReactionProfile(cell_id=cell.id, patient_rxn=patient_rxn)
                    db_session.add(new_reaction)

            db_session.commit()
            return jsonify({"message": "Reactions saved successfully!"}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

        

    @app.route('/api/patient-reactions', methods=['GET'])
    def get_all_patient_reactions():
        try:
            # Query all patient reactions
            reactions = db_session.query(PatientReactionProfile).all()
            if not reactions:
                return jsonify({"message": "No patient reactions found"}), 404

            # Format the data for response
            response_data = []
            for reaction in reactions:
                cell = db_session.query(Cell).filter_by(id=reaction.cell_id).first()
                antigram = db_session.query(Antigram).filter_by(id=cell.antigram_id).first()
                response_data.append({
                    "lot_number": antigram.lot_number if antigram else "Unknown",
                    "cell_number": cell.cell_number if cell else "Unknown",
                    "patient_reaction": reaction.patient_rxn
                })

            return jsonify({"patient_reactions": response_data}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route('/api/clear-patient-reactions', methods=['DELETE'])
    def clear_patient_reactions():
        try:
            # Delete all records from the PatientReactionProfile table
            db_session.query(PatientReactionProfile).delete()
            db_session.commit()
            return jsonify({"message": "All patient reactions cleared successfully!"}), 200
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
                return jsonify({"message": "Patient reaction deleted successfully!"}), 200
            else:
                return jsonify({"error": "Cell not found."}), 404
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500
        
    @app.route('/api/abid', methods=['GET'])
    def antibody_identification():
        try:
            # Fetch the latest patient reactions
            patient_reactions = db_session.query(PatientReactionProfile).all()

            if not patient_reactions:
                return jsonify({"error": "No patient reactions found"}), 404

            ruled_out = set()
            antigen_list = set()  # Collect all antigens
            match_candidates = set()  # Potential matches
            antigen_presence_map = {}  # Map antigens to their presence/absence by cell

            for reaction in patient_reactions:
                cell = db_session.query(Cell).filter_by(id=reaction.cell_id).first()
                if not cell:
                    continue

                # Fetch reactions associated with this cell
                cell_reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()

                for reaction_item in cell_reactions:
                    antigen_name = reaction_item.antigen
                    antigen_list.add(antigen_name)
                    antigen_presence_map.setdefault(antigen_name, []).append({
                        "cell_id": cell.id,
                        "reaction_value": reaction_item.reaction_value,
                        "patient_rxn": reaction.patient_rxn,
                    })

            print("Antigen Presence Map:", antigen_presence_map)  # Debugging log

            # Process each antigen
            for antigen, details in antigen_presence_map.items():
                is_match = True  # Assume it is a match until proven otherwise
                is_ruled_out = False  # Assume it is not ruled out until proven otherwise

                for detail in details:
                    patient_rxn = detail["patient_rxn"]
                    reaction_value = detail["reaction_value"]

                    if patient_rxn == "0" and reaction_value == "+":
                        # Patient reaction 0, antigen is present -> Rule out
                        is_ruled_out = True
                        is_match = False
                        break
                    elif patient_rxn == "+" and reaction_value != "+":
                        # Patient reaction +, antigen is absent -> Not a match
                        is_match = False

                if is_ruled_out:
                    ruled_out.add(antigen)
                elif is_match:
                    match_candidates.add(antigen)

            # Antigens not ruled out or matched
            still_to_rule_out = antigen_list - ruled_out - match_candidates

            print("Final Results - RO:", ruled_out, "STRO:", still_to_rule_out, "Match:", match_candidates)  # Debugging log

            return jsonify({
                "ruled_out": list(ruled_out),
                "still_to_rule_out": list(still_to_rule_out),
                "match": list(match_candidates),
            }), 200

        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": str(e)}), 500

