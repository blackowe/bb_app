from flask import request, jsonify, render_template
from models import Antigram, Cell, Reaction, AntigramTemplate, PatientReactionProfile
from datetime import datetime
from sqlalchemy import cast, String

def register_antigram_routes(app, db_session):
    # Create Antigram
    @app.route("/api/antigrams", methods=["POST"])
    def add_antigram():
        """Creates a new antigram using the selected template and saves reactions."""
        try:
            data = request.json
            required_keys = ["templateId", "lotNumber", "expirationDate", "cells"]
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return jsonify({"error": f"Missing keys: {missing_keys}"}), 400

            template_id = data["templateId"]
            expiration_date = datetime.strptime(data["expirationDate"], "%Y-%m-%d").date()

            # Fetch the template
            template = db_session.query(AntigramTemplate).filter_by(id=template_id).first()
            if not template:
                return jsonify({"error": "Template not found"}), 404

            # Create new antigram
            new_antigram = Antigram(template_id=template.id, lot_number=data["lotNumber"], expiration_date=expiration_date)
            db_session.add(new_antigram)
            db_session.flush()  # Retrieve ID of the new antigram

            # Save cells and reactions
            for cell_data in data["cells"]:
                new_cell = Cell(antigram_id=new_antigram.id, cell_number=cell_data["cellNumber"])
                db_session.add(new_cell)
                db_session.flush()

                for antigen, reaction_value in cell_data["reactions"].items():
                    new_reaction = Reaction(cell_id=new_cell.id, antigen=antigen, reaction_value=reaction_value)
                    db_session.add(new_reaction)

            db_session.commit()
            return jsonify({"message": "Antigram created successfully!", "antigram_id": new_antigram.id}), 201

        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500




    # Get All Antigrams or Filter by Lot Number
    @app.route("/api/antigrams", methods=["GET"])
    def get_all_antigrams():
        """Fetch all antigrams or filter by lot number."""
        try:
            search_query = request.args.get('search', '').strip()

            # Debugging: Print raw search query to Flask logs
            print(f"Searching for lot number: '{search_query}'")

            # Join Antigram with AntigramTemplate to get template details
            query = db_session.query(Antigram, AntigramTemplate.name).join(AntigramTemplate, Antigram.template_id == AntigramTemplate.id)

            if search_query:
                query = query.filter(cast(Antigram.lot_number, String).ilike(f"%{search_query}%"))  # ✅ Ensures lot_number is treated as a string

            antigrams = query.all()

            # Debugging: Print the fetched results to check query correctness
            print(f"Fetched {len(antigrams)} antigrams matching lot number '{search_query}'")

            result = []
            for antigram, template_name in antigrams:
                cells = db_session.query(Cell).filter_by(antigram_id=antigram.id).all()
                cell_data = []
                for cell in cells:
                    reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()
                    cell_data.append({
                        "cell_number": cell.cell_number,
                        "reactions": {reaction.antigen: reaction.reaction_value for reaction in reactions}
                    })

                result.append({
                    "id": antigram.id,
                    "name": template_name,  # Fetch template name from AntigramTemplate
                    "lot_number": antigram.lot_number,
                    "expiration_date": antigram.expiration_date.strftime("%Y-%m-%d"),
                    "cells": cell_data
                })

            return jsonify(result), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    # Get Antigram by ID
    @app.route("/api/antigrams/<int:id>", methods=["GET"])
    def get_antigram_by_id(id):
        try:
            antigram = db_session.query(Antigram).filter_by(id=id).first()
            if not antigram:
                return jsonify({"error": f"Antigram with ID {id} not found"}), 404

            # Fetch the template name
            template = db_session.query(AntigramTemplate).filter_by(id=antigram.template_id).first()
            template_name = template.name if template else "Unknown"

            cells = db_session.query(Cell).filter_by(antigram_id=id).all()
            cell_data = []
            for cell in cells:
                reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()
                cell_data.append({
                    "cell_number": cell.cell_number,
                    "reactions": {reaction.antigen: reaction.reaction_value for reaction in reactions}
                })

            return jsonify({
                "id": antigram.id,
                "name": template_name, 
                "lot_number": antigram.lot_number,
                "expiration_date": antigram.expiration_date.strftime("%Y-%m-%d"),
                "cells": cell_data
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @app.route("/api/antigrams/<int:id>", methods=["DELETE"])
    def delete_antigram_by_id(id):
        """Deletes a single antigram and its associated cells and reactions."""
        try:
            # Check if antigram exists
            antigram = db_session.query(Antigram).filter_by(id=id).first()
            if not antigram:
                return jsonify({"error": f"Antigram with ID {id} not found"}), 404

            # Get all cells for this antigram
            cells = db_session.query(Cell).filter_by(antigram_id=id).all()
            cell_ids = [cell.id for cell in cells]

            # First delete all patient reaction profiles for these cells
            if cell_ids:
                db_session.query(PatientReactionProfile).filter(PatientReactionProfile.cell_id.in_(cell_ids)).delete(synchronize_session=False)

            # Now delete the antigram (cascade will handle cells and reactions)
            db_session.delete(antigram)
            db_session.commit()
            
            return jsonify({
                "message": f"Antigram with ID {id} has been deleted successfully.",
                "deleted_lot_number": antigram.lot_number
            }), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500


    @app.route("/api/antigrams/delete-all-antigrams", methods=["DELETE"])
    def delete_all_antigrams():
        """Deletes all antigrams, cells, and reactions from the database."""
        try:
            # Delete all reactions first (to avoid foreign key constraint issues)
            db_session.query(Reaction).delete()

            # Delete all cells
            db_session.query(Cell).delete()

            # Delete all antigrams
            db_session.query(Antigram).delete()

            db_session.commit()
            return jsonify({"message": "All antigrams have been deleted successfully."}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500