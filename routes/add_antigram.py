from flask import request, jsonify, render_template
from models import Antigram, Cell, Reaction, AntigramTemplate
from sqlalchemy import and_, func
from datetime import datetime

def register_add_antigram_routes(app, db_session):
  @app.route("/add_antigram", methods=["GET"])
  def add_antigram_page():
      return render_template("add_antigram.html")

  @app.route("/api/antigram-from-template", methods=["POST"])
  def create_antigram_from_template():
      try:
          data = request.json
          template_name = data.get("templateName")
          lot_number = data.get("lotNumber")
          expiration_date = datetime.strptime(data.get("expirationDate"), "%Y-%m-%d").date()

          # Find the template
          templates = {
              "Standard ABO-Rh": ["D", "C", "E", "e", "c", "Jka", "Jkb"],
              "Extended Panel": ["D", "C", "E", "e", "c", "Jka", "Jkb", "M", "N", "S", "s", "P1"]
          }
          antigens = templates.get(template_name)

          if not antigens:
              return jsonify({"error": "Template not found"}), 400

          # Create new antigram
          new_antigram = Antigram(name=template_name, lot_number=lot_number, expiration_date=expiration_date)
          db_session.add(new_antigram)
          db_session.flush()

          # Add predefined cells and reactions
          for i in range(1, len(antigens) + 1):
              new_cell = Cell(antigram_id=new_antigram.id, cell_number=i)
              db_session.add(new_cell)
              db_session.flush()

              for antigen in antigens:
                  new_reaction = Reaction(cell_id=new_cell.id, antigen=antigen, reaction_value="+")  # Default to positive
                  db_session.add(new_reaction)

          db_session.commit()
          return jsonify({"message": "Antigram created successfully", "antigram_id": new_antigram.id}), 201
      except Exception as e:
          db_session.rollback()
          return jsonify({"error": str(e)}), 500

# ---------------------------Antigram Template Routes--------------------------------
  
  @app.route("/api/antigram-templates", methods=["GET"])
  def get_antigram_templates():
      """Fetches all available antigram templates from the database."""
      try:
          templates = db_session.query(AntigramTemplate).all()
          return jsonify([t.to_dict() for t in templates]), 200
      except Exception as e:
          return jsonify({"error": str(e)}), 500
      
  @app.route("/api/antigram-templates/<int:id>", methods=["GET"])
  def get_antigram_template_by_id(id):
      """Fetch a single antigram template by ID."""
      try:
          template = db_session.query(AntigramTemplate).filter_by(id=id).first()
          if not template:
              return jsonify({"error": "Template not found"}), 404

          return jsonify({
              "id": template.id,
              "name": template.name,
              "antigen_order": template.antigen_order.split(","),  # Convert from stored string
              "cell_count": template.cell_count
          }), 200
      except Exception as e:
          return jsonify({"error": str(e)}), 500

  # Create new template
  @app.route("/api/antigram-templates", methods=["POST"])
  def create_antigram_template():
      """Creates a new antigram template."""
      try:
          data = request.json
          required_keys = ["name", "antigenOrder", "cellCount"]
          missing_keys = [key for key in required_keys if key not in data]
          if missing_keys:
              return jsonify({"error": f"Missing keys: {missing_keys}"}), 400

          new_template = AntigramTemplate(
              name=data["name"],
              antigen_order=",".join(data["antigenOrder"]),
              cell_count=data["cellCount"]
          )
          db_session.add(new_template)
          db_session.commit()
          return jsonify({"message": "Template created successfully", "template_id": new_template.id}), 201
      except Exception as e:
          db_session.rollback()
          return jsonify({"error": str(e)}), 500

  @app.route("/api/antigram-templates/<int:id>", methods=["DELETE"])
  def delete_antigram_template(id):
      """Deletes an existing antigram template."""
      try:
          template = db_session.query(AntigramTemplate).filter_by(id=id).first()
          if not template:
              return jsonify({"error": "Template not found"}), 404

          db_session.delete(template)
          db_session.commit()
          return jsonify({"message": "Template deleted successfully"}), 200
      except Exception as e:
          db_session.rollback()
          return jsonify({"error": str(e)}), 500


