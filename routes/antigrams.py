from flask import request, jsonify
from models import Antigram, Cell, Reaction
from datetime import datetime

def register_antigram_routes(app, db_session):
    
    # Create Antigram
    @app.route("/api/antigrams", methods=["POST"])
    def add_antigram():
        try:
            data = request.json
            required_keys = ["name", "lotNumber", "expirationDate", "cells"]
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return jsonify({"error": f"Missing keys: {missing_keys}"}), 400

            expiration_date = datetime.strptime(data["expirationDate"], "%Y-%m-%d").date()
            new_antigram = Antigram(name=data["name"], lot_number=data["lotNumber"], expiration_date=expiration_date)
            db_session.add(new_antigram)
            db_session.flush()  # Retrieve the ID of the newly created Antigram

            for cell in data["cells"]:
                new_cell = Cell(antigram_id=new_antigram.id, cell_number=cell["cellNumber"])
                db_session.add(new_cell)
                db_session.flush()

                for antigen, reaction_value in cell["reactions"].items():
                    new_reaction = Reaction(cell_id=new_cell.id, antigen=antigen, reaction_value=reaction_value)
                    db_session.add(new_reaction)

            db_session.commit()
            return jsonify({"message": "Antigram created successfully"}), 201
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    # Get All Antigrams
    @app.route("/api/antigrams", methods=["GET"])
    def get_all_antigrams():
        try:
            antigrams = db_session.query(Antigram).all()
            result = []

            for antigram in antigrams:
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
                    "name": antigram.name,
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
                "name": antigram.name,
                "lot_number": antigram.lot_number,
                "expiration_date": antigram.expiration_date.strftime("%Y-%m-%d"),
                "cells": cell_data
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get Antigram by Lot Number
    @app.route("/api/antigrams/lot/<lot_number>", methods=["GET"])
    def get_antigram_by_lot(lot_number):
        try:
            antigram = db_session.query(Antigram).filter_by(lot_number=lot_number).first()
            if not antigram:
                return jsonify({"error": "Antigram not found"}), 404

            cells = db_session.query(Cell).filter_by(antigram_id=antigram.id).all()
            cell_data = []
            for cell in cells:
                reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()
                cell_data.append({
                    "cell_number": cell.cell_number,
                    "reactions": {reaction.antigen: reaction.reaction_value for reaction in reactions}
                })

            result = {
                "id": antigram.id,
                "name": antigram.name,
                "lot_number": antigram.lot_number,
                "cells": cell_data
            }
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
