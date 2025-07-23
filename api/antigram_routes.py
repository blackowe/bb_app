"""
Consolidated antigram and template routes.
This module handles all antigram and template-related API endpoints.
"""

from flask import request, jsonify, render_template, current_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def register_antigram_routes(app, db_session):
    """Register all antigram and template routes."""
    
    # Get managers from app config
    antigram_manager = app.config['antigram_manager']
    template_manager = app.config.get('template_manager')

    #  ---------- Template Routes ----------
    @app.route("/api/templates", methods=["POST"])
    def create_template():
        """Create a new antigram template."""
        try:
            data = request.json
            name = data.get("name")
            antigen_order = data.get("antigen_order")
            cell_count = data.get("cell_count")
            cell_range = data.get("cell_range")  # New optional field
            
            if not name or not antigen_order or not cell_count:
                return jsonify({"error": "Missing name, antigen_order, or cell_count"}), 400

            # Validate cell_range if provided
            if cell_range:
                if not isinstance(cell_range, list) or len(cell_range) != 2:
                    return jsonify({"error": "cell_range must be a list with exactly 2 elements [start, end]"}), 400
                if cell_range[0] >= cell_range[1]:
                    return jsonify({"error": "cell_range start must be less than end"}), 400
                # Validate that cell_count matches the range
                expected_count = cell_range[1] - cell_range[0] + 1
                if cell_count != expected_count:
                    return jsonify({"error": f"cell_count ({cell_count}) must match cell_range ({expected_count} cells from {cell_range[0]} to {cell_range[1]})"}), 400

            # --- VALIDATION: Only allow antigens that exist in Antigen table AND have at least one enabled antibody rule ---
            from models import Antigen, AntibodyRule
            antigens = {a.name for a in db_session.query(Antigen).all()}
            rules = db_session.query(AntibodyRule).filter_by(enabled=True).all()
            antigens_with_rules = {rule.target_antigen for rule in rules}
            valid_antigens = antigens & antigens_with_rules
            invalid_antigens = [ag for ag in antigen_order if ag not in valid_antigens]
            if invalid_antigens:
                return jsonify({
                    "error": f"The following antigens are not valid (must exist in Antigen table and have at least one enabled antibody rule): {', '.join(invalid_antigens)}"
                }), 400

            # Generate unique template ID
            template_id = int(datetime.now().timestamp() * 1000)
            
            # Add to template manager (this will also save to database)
            template_manager.add_template(template_id, name, antigen_order, cell_count, cell_range)
            
            # Commit changes after creating template
            template_manager.commit_changes()
            
            return jsonify({"message": "Template created", "template_id": template_id}), 201
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/templates", methods=["GET"])
    def get_templates():
        """Get all templates."""
        templates = template_manager.get_all_templates()
        return jsonify(templates), 200

    @app.route("/api/templates/<int:template_id>", methods=["GET"])
    def get_template(template_id):
        """Get a specific template by ID."""
        template = template_manager.get_template(template_id)
        if not template:
            return jsonify({"error": "Not found"}), 404
        return jsonify(template), 200

    @app.route("/api/templates/<int:template_id>", methods=["PUT"])
    def update_template(template_id):
        """Update an existing antigram template."""
        try:
            data = request.json
            name = data.get("name")
            antigen_order = data.get("antigen_order")
            cell_count = data.get("cell_count")
            cell_range = data.get("cell_range")
            
            if not name or not antigen_order or not cell_count:
                return jsonify({"error": "Missing name, antigen_order, or cell_count"}), 400

            # Validate cell_range if provided
            if cell_range:
                if not isinstance(cell_range, list) or len(cell_range) != 2:
                    return jsonify({"error": "cell_range must be a list with exactly 2 elements [start, end]"}), 400
                if cell_range[0] >= cell_range[1]:
                    return jsonify({"error": "cell_range start must be less than end"}), 400
                expected_count = cell_range[1] - cell_range[0] + 1
                if cell_count != expected_count:
                    return jsonify({"error": f"cell_count ({cell_count}) must match cell_range ({expected_count} cells from {cell_range[0]} to {cell_range[1]})"}), 400

            # --- VALIDATION: Only allow antigens that exist in Antigen table AND have at least one enabled antibody rule ---
            from models import Antigen, AntibodyRule
            antigens = {a.name for a in db_session.query(Antigen).all()}
            rules = db_session.query(AntibodyRule).filter_by(enabled=True).all()
            antigens_with_rules = {rule.target_antigen for rule in rules}
            valid_antigens = antigens & antigens_with_rules
            invalid_antigens = [ag for ag in antigen_order if ag not in valid_antigens]
            if invalid_antigens:
                return jsonify({
                    "error": f"The following antigens are not valid (must exist in Antigen table and have at least one enabled antibody rule): {', '.join(invalid_antigens)}"
                }), 400

            # Update the template
            template = template_manager.get_template(template_id)
            if not template:
                return jsonify({"error": "Not found"}), 404
            template_manager.add_template(template_id, name, antigen_order, cell_count, cell_range)
            template_manager.commit_changes()
            return jsonify({"message": "Template updated", "template_id": template_id}), 200
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/templates/<int:template_id>", methods=["DELETE"])
    def delete_template(template_id):
        """Delete a template."""
        template = template_manager.get_template(template_id)
        if not template:
            return jsonify({"error": "Not found"}), 404
        
        template_manager.delete_template(template_id)
        return jsonify({"message": "Template deleted"}), 200

    #  ---------- Template Management Page ----------
    @app.route("/template_management", methods=["GET"])
    def template_management_page():
        """Render the template management page."""
        return render_template("template_management.html")

    #  ---------- Antigram Routes ----------
    @app.route("/add_antigram", methods=["GET"])
    def add_antigram_page():
        """Render the add antigram page."""
        return render_template("add_antigram.html")

    @app.route("/api/antigrams", methods=["POST"])
    def add_antigram():
        """Create a new antigram using the selected template and save reactions."""
        try:
            data = request.json
            required_keys = ["templateId", "lotNumber", "expirationDate", "cells", "templateName", "antigenOrder"]
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return jsonify({"error": f"Missing keys: {missing_keys}"}), 400

            antigram_id = int(datetime.now().timestamp() * 1000)
            lot_number = data["lotNumber"]
            template_name = data["templateName"]
            antigens = data["antigenOrder"]
            expiration_date = datetime.strptime(data["expirationDate"], "%Y-%m-%d").date()
            cells_data = [
                {"cell_number": cell["cellNumber"], "reactions": cell["reactions"]}
                for cell in data["cells"]
            ]

            antigram_manager.create_antigram_matrix(
                antigram_id=antigram_id,
                lot_number=lot_number,
                template_name=template_name,
                antigens=antigens,
                cells_data=cells_data,
                expiration_date=expiration_date
            )
            
            # Commit changes after creating antigram
            antigram_manager.commit_changes()
            
            return jsonify({"message": "Antigram created successfully!", "antigram_id": antigram_id}), 201
        except Exception as e:
            logger.error(f"Error creating antigram: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/antigrams", methods=["GET"])
    def get_all_antigrams():
        """Fetch all antigrams or filter by lot number."""
        try:
            search_query = request.args.get('search', '').strip()
            all_antigrams = antigram_manager.get_all_antigrams()
            if search_query:
                filtered = [a for a in all_antigrams if search_query.lower() in a['lot_number'].lower()]
            else:
                filtered = all_antigrams
            return jsonify(filtered), 200
        except Exception as e:
            logger.error(f"Error getting antigrams: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/antigrams/<int:id>", methods=["GET"])
    def get_antigram_by_id(id):
        """Get a specific antigram by ID."""
        try:
            matrix = antigram_manager.get_antigram_matrix(id)
            metadata = antigram_manager.get_antigram_metadata(id)
            if matrix is None or metadata is None:
                return jsonify({"error": f"Antigram with ID {id} not found"}), 404
            
            # Format cells data - matrix has cells as index and antigens as columns
            cells = []
            for cell_number in matrix.index:
                cells.append({
                    "cell_number": str(cell_number),  # Ensure cell_number is string
                    "reactions": matrix.loc[cell_number].to_dict()
                })
            return jsonify({
                "id": id,
                "name": metadata["template_name"],
                "lot_number": metadata["lot_number"],
                "expiration_date": str(metadata["expiration_date"]),
                "cells": cells
            }), 200
        except Exception as e:
            logger.error(f"Error getting antigram {id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/antigrams/<int:id>", methods=["PUT"])
    def update_antigram_by_id(id):
        """Update an existing antigram."""
        try:
            data = request.json
            required_keys = ["lotNumber", "expirationDate", "cells"]
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return jsonify({"error": f"Missing keys: {missing_keys}"}), 400

            # Check if antigram exists
            existing_matrix = antigram_manager.get_antigram_matrix(id)
            existing_metadata = antigram_manager.get_antigram_metadata(id)
            if existing_matrix is None or existing_metadata is None:
                return jsonify({"error": f"Antigram with ID {id} not found"}), 404

            # Update metadata
            lot_number = data["lotNumber"]
            expiration_date = datetime.strptime(data["expirationDate"], "%Y-%m-%d").date()
            
            # Update cells data
            cells_data = [
                {"cell_number": cell["cellNumber"], "reactions": cell["reactions"]}
                for cell in data["cells"]
            ]

            # Update the antigram
            antigram_manager.update_antigram_matrix(
                antigram_id=id,
                lot_number=lot_number,
                cells_data=cells_data,
                expiration_date=expiration_date
            )
            
            # Commit changes after updating antigram
            antigram_manager.commit_changes()
            
            return jsonify({"message": "Antigram updated successfully!", "antigram_id": id}), 200
        except Exception as e:
            logger.error(f"Error updating antigram {id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/antigrams/<int:id>", methods=["DELETE"])
    def delete_antigram_by_id(id):
        """Delete a single antigram and its matrix."""
        try:
            deleted = antigram_manager.delete_antigram(id)
            if not deleted:
                return jsonify({"error": f"Antigram with ID {id} not found"}), 404
            return jsonify({
                "message": f"Antigram with ID {id} has been deleted successfully."
            }), 200
        except Exception as e:
            logger.error(f"Error deleting antigram {id}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/antigrams/delete-all-antigrams", methods=["DELETE"])
    def delete_all_antigrams():
        """Delete all antigrams from the pandas manager."""
        try:
            antigram_manager.antigram_matrices.clear()
            antigram_manager.antigram_metadata.clear()
            return jsonify({"message": "All antigrams have been deleted successfully."}), 200
        except Exception as e:
            logger.error(f"Error deleting all antigrams: {e}")
            return jsonify({"error": str(e)}), 500 