"""
Utility routes for cell finding and other utility operations.
This module handles cell finding and other utility endpoints.
"""

from flask import request, jsonify, render_template, current_app

def register_utility_routes(app, db_session):
    """Register all utility routes."""
    
    # Get managers from app config
    antigram_manager = app.config['antigram_manager']

    @app.route("/cell_finder", methods=["GET", "POST"])
    def cell_finder():
        """Cell finder page and pattern matching functionality."""
        try:
            # Get all distinct antigens from pandas matrices
            all_antigens = set()
            for matrix in antigram_manager.antigram_matrices.values():
                all_antigens.update(matrix.columns)
            antigen_list = sorted(list(all_antigens))

            if request.method == "GET":
                return render_template("cell_finder.html", antigens=antigen_list)

            elif request.method == "POST":
                if request.content_type != "application/json":
                    return jsonify({"error": "Unsupported Media Type: Content-Type must be 'application/json'"}), 415

                antigen_profile = request.json.get("antigenProfile", {})

                if not antigen_profile:
                    return jsonify({"error": "Missing antigen profile in request body"}), 400

                # Use pandas pattern matching
                matching_cells = antigram_manager.find_cells_by_pattern(antigen_profile)

                # Format results with all antigens, not just search pattern
                results = []
                for match in matching_cells:
                    # Get all reactions for this cell from the matrix
                    antigram_id = match['antigram_id']
                    cell_number = match['cell_number']
                    matrix = antigram_manager.antigram_matrices[antigram_id]
                    
                    # Get all reactions for this cell
                    cell_reactions = {}
                    if cell_number in matrix.index:
                        cell_row = matrix.loc[cell_number]
                        for antigen in antigen_list:
                            cell_reactions[antigen] = cell_row.get(antigen, '-')
                    
                    results.append({
                        "antigram": {
                            "id": match['antigram_id'],
                            "name": match['template_name'],
                            "lot_number": match['lot_number'],
                            "expiration_date": str(match['expiration_date']),
                        },
                        "cell": {
                            "cell_number": match['cell_number'],
                            "reactions": cell_reactions
                        }
                    })

                return jsonify({
                    "results": results, 
                    "antigens": antigen_list,
                    "search_pattern": list(antigen_profile.keys())
                }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/antigens", methods=["GET"])
    def get_all_antigens():
        """Fetch all distinct antigens from the pandas matrices."""
        try:
            all_antigens = set()
            for matrix in antigram_manager.antigram_matrices.values():
                all_antigens.update(matrix.columns)
            antigen_list = sorted(list(all_antigens))

            return jsonify({"antigens": antigen_list}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500 