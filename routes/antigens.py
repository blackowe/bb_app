from flask import request, jsonify, render_template
from models import Antigen, AntigenRule

def register_antigen_routes(app, db_session):
    @app.route('/antigens')
    def antigens_page():
        return render_template('antigens.html')

    @app.route('/api/antigens', methods=['GET'])
    def get_antigens():
        """Get all available antigens."""
        try:
            antigens = db_session.query(Antigen).all()
            return jsonify([antigen.to_dict() for antigen in antigens]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigens', methods=['POST'])
    def create_antigen():
        """Create a new antigen."""
        try:
            data = request.json
            if not data or 'name' not in data or 'system' not in data:
                return jsonify({"error": "Missing required fields"}), 400

            # Check if antigen already exists
            existing_antigen = db_session.query(Antigen).filter_by(name=data['name']).first()
            if existing_antigen:
                return jsonify({"error": "Antigen already exists"}), 409

            new_antigen = Antigen(
                name=data['name'],
                system=data['system']
            )
            db_session.add(new_antigen)
            db_session.commit()
            
            return jsonify(new_antigen.to_dict()), 201
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigens/<name>', methods=['DELETE'])
    def delete_antigen(name):
        """Delete an antigen and its associated rules."""
        try:
            antigen = db_session.query(Antigen).filter_by(name=name).first()
            if not antigen:
                return jsonify({"error": "Antigen not found"}), 404

            # Delete associated rules
            db_session.query(AntigenRule).filter(
                (AntigenRule.target_antigen == antigen.name) |
                (AntigenRule.rule_antigens.like(f"%{antigen.name}%"))
            ).delete()

            db_session.delete(antigen)
            db_session.commit()
            return jsonify({"message": "Antigen deleted successfully"}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigens/initialize', methods=['POST'])
    def initialize_base_antigens():
        """Initialize base antigens in the database."""
        try:
            # Define base antigens
            base_antigens = [
                # Rh System
                {"name": "D", "system": "Rh"},
                {"name": "E", "system": "Rh"},
                {"name": "e", "system": "Rh"},
                {"name": "C", "system": "Rh"},
                {"name": "c", "system": "Rh"},
                
                # Kell System
                {"name": "K", "system": "Kell"},
                {"name": "k", "system": "Kell"},
                
                # Duffy System
                {"name": "Fya", "system": "Duffy"},
                {"name": "Fyb", "system": "Duffy"},
                
                # Kidd System
                {"name": "Jka", "system": "Kidd"},
                {"name": "Jkb", "system": "Kidd"},
                
                # MNS System
                {"name": "M", "system": "MNS"},
                {"name": "N", "system": "MNS"},
                {"name": "S", "system": "MNS"},
                {"name": "s", "system": "MNS"},
                
                # Lewis System
                {"name": "Lea", "system": "Lewis"},
                {"name": "Leb", "system": "Lewis"}
            ]

            # Clear existing antigens
            db_session.query(Antigen).delete()

            # Add new antigens
            for antigen_data in base_antigens:
                new_antigen = Antigen(**antigen_data)
                db_session.add(new_antigen)

            db_session.commit()
            return jsonify({"message": "Base antigens initialized successfully"}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500 