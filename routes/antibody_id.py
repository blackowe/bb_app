from flask import request, jsonify, render_template
from models import Cell, PatientReactionProfile, Antigram

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

            for reaction in reactions:
                cell_number = reaction['cell_number']
                patient_rxn = reaction['patient_rxn']

                # Find the cell by antigram ID and cell number
                cell = db_session.query(Cell).filter_by(
                    antigram_id=antigram_id, 
                    cell_number=cell_number
                ).first()

                if cell:
                    # Check if a reaction already exists for this cell
                    existing_reaction = db_session.query(PatientReactionProfile).filter_by(cell_id=cell.id).first()

                    if existing_reaction:
                        # Update the existing reaction
                        existing_reaction.patient_rxn = patient_rxn
                    else:
                        # Create a new reaction
                        new_reaction = PatientReactionProfile(
                            cell_id=cell.id,
                            patient_rxn=patient_rxn,
                        )
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
        

        



