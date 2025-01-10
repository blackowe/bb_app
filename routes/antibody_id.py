from flask import request, jsonify, render_template
from models import Antigram, Cell, Reaction
from sqlalchemy.orm import sessionmaker
from connect_connector import connect_with_connector

def register_antibody_id_routes(app, Session):
    @app.route("/antibody_id", methods=["GET", "POST"])
    def antibody_id():
        session = Session()
        try:
            if request.method == "GET":
                # Fetch all unique lot numbers
                lot_numbers = [antigram.lot_number for antigram in session.query(Antigram).all()]
                return render_template("antibody_id.html", lot_numbers=lot_numbers)

            if request.method == "POST":
                # Get the selected antigram and patient reactions
                data = request.json
                lot_number = data.get("lot_number")
                patient_reactions = data.get("patient_reactions")  # {cell_number: reaction}

                antigram = session.query(Antigram).filter_by(lot_number=lot_number).first()
                if not antigram:
                    return jsonify({"error": "Antigram not found"}), 404

                cells = session.query(Cell).filter_by(antigram_id=antigram.id).all()
                ruled_out_antigens = set()

                for cell in cells:
                    cell_reactions = session.query(Reaction).filter_by(cell_id=cell.id).all()
                    patient_reaction = patient_reactions.get(str(cell.cell_number))

                    if patient_reaction == "0":  # Only negative patient reactions
                        for reaction in cell_reactions:
                            if reaction.reaction_value == "+":  # Rule out antigens with "+"
                                ruled_out_antigens.add(reaction.antigen)

                all_antigens = {reaction.antigen for reaction in session.query(Reaction).all()}
                possible_antibodies = all_antigens - ruled_out_antigens

                return jsonify({
                    "ruled_out_antigens": list(ruled_out_antigens),
                    "possible_antibodies": list(possible_antibodies)
                }), 200

        except Exception as e:
            print("Error in Antibody ID:", str(e))
            return jsonify({"error": str(e)}), 500
        finally:
            session.close()
