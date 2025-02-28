from flask import request, jsonify, render_template
from models import Antigram, Cell, Reaction, AntigramTemplate
from sqlalchemy import and_, func, distinct

def register_cell_finder_routes(app, db_session):

    @app.route("/cell_finder", methods=["GET", "POST"])
    def cell_finder():
        try:
            # ✅ Fetch all distinct antigens and ensure order matches the input
            all_antigens = db_session.query(distinct(Reaction.antigen)).order_by(Reaction.antigen).all()
            antigen_list = [antigen[0] for antigen in all_antigens]  # Extract as list

            if request.method == "GET":
                return render_template("cell_finder.html", antigens=antigen_list)

            elif request.method == "POST":
                if request.content_type != "application/json":
                    return jsonify({"error": "Unsupported Media Type: Content-Type must be 'application/json'"}), 415

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
                    if not antigram:
                        continue

                    # Fetch the template name
                    template = db_session.query(AntigramTemplate).filter_by(id=antigram.template_id).first()
                    template_name = template.name if template else "Unknown Template"

                    reactions = db_session.query(Reaction).filter_by(cell_id=cell.id).all()

                    # ✅ Ensure reactions are sorted in the same order as `antigen_profile` (input order)
                    reaction_dict = {reaction.antigen: reaction.reaction_value for reaction in reactions}
                    ordered_reactions = [reaction_dict.get(antigen, "-") for antigen in antigen_profile.keys()]

                    results.append({
                        "antigram": {
                            "id": antigram.id,
                            "name": template_name,
                            "lot_number": antigram.lot_number,
                            "expiration_date": antigram.expiration_date.strftime("%Y-%m-%d"),
                        },
                        "cell": {
                            "cell_number": cell.cell_number,
                            "reactions": ordered_reactions  # ✅ Now reactions match input order
                        }
                    })

                return jsonify({"results": results, "antigens": list(antigen_profile.keys())}), 200

        except Exception as e:
            print("Error in Cell Finder Backend:", str(e))
            return jsonify({"error": str(e)}), 500



    @app.route("/api/antigens", methods=["GET"])
    def get_all_antigens():
        """Fetch all distinct antigens from the database."""
        try:
            distinct_antigens = db_session.query(Reaction.antigen).distinct().all()
            antigen_list = [antigen[0] for antigen in distinct_antigens]

            return jsonify({"antigens": antigen_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
