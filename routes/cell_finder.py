from flask import request, jsonify, render_template
from models import Antigram, Cell, Reaction
from sqlalchemy import and_, func

def register_cell_finder_routes(app, db_session):

    @ app.route("/cell_finder", methods=["POST", "GET"])
    def cell_finder():
        if request.method == "GET":
            return render_template("cell_finder.html")

        if request.method == "POST":
            if request.content_type != "application/json":
                return jsonify({"error": "Unsupported Media Type: Content-Type must be 'application/json'"}), 415

            try:
                antigen_profile = request.json.get("antigenProfile", {})
                print("Received Antigen Profile:", antigen_profile)

                if not antigen_profile:
                    return jsonify({"error": "Missing antigen profile in request body"}), 400

                # Fetch all cells
                all_cells = db_session.query(Cell).all()

                # Filter cells based on the antigen profile
                matching_cells = []
                for cell in all_cells:
                    reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()
                    reaction_map = {reaction.antigen: reaction.reaction_value for reaction in reactions}

                    # Check if all antigen-reaction pairs match
                    if all(reaction_map.get(antigen) == reaction for antigen, reaction in antigen_profile.items()):
                        matching_cells.append(cell)

                print(f"Matching Cells Found: {len(matching_cells)}")

                # Format results
                results = []
                for cell in matching_cells:
                    antigram = db_session.query(Antigram).filter_by(id=cell.antigram_id).first()
                    reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()
                    results.append({
                        "antigram": {
                            "id": antigram.id,
                            "name": antigram.name,
                            "lot_number": antigram.lot_number,
                            "expiration_date": antigram.expiration_date.strftime("%Y-%m-%d"),
                        },
                        "cell": {
                            "cell_number": cell.cell_number,
                            "reactions": {reaction.antigen: reaction.reaction_value for reaction in reactions}
                        }
                    })

                print("Returning Results:", results)
                return jsonify(results), 200

            except Exception as e:
                print("Error in Cell Finder Backend:", str(e))
                return jsonify({"error": str(e)}), 500
