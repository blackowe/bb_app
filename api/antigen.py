"""
Antigen and antibody rule management routes.
This module handles all antigen and antibody rule management endpoints.
"""

from flask import request, jsonify, render_template, current_app
from models import Antigen, AntibodyRule
from default_rules import get_default_rules
import logging
import json

logger = logging.getLogger(__name__)

def register_antigen_routes(app, db_session):
    """Register all antigen and antibody rule routes."""
    
    @app.route('/antigen')
    def antigen_page():
        """Render the antigen management page."""
        return render_template('antigen.html')

    @app.route('/antibody_rules')
    def antibody_rules_page():
        """Render the antibody rules management page."""
        return render_template('antibody_rules.html')

    # Antigen Management Routes
    @app.route('/api/antigens', methods=['GET'])
    def get_antigens():
        """Get all available antigens."""
        try:
            antigens = db_session.query(Antigen).all()
            return jsonify([antigen.to_dict() for antigen in antigens]), 200
        except Exception as e:
            logger.error(f"Error getting antigens: {e}")
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
            
            logger.info(f"Created new antigen: {data['name']}")
            return jsonify(new_antigen.to_dict()), 201
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error creating antigen: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigens/<name>', methods=['DELETE'])
    def delete_antigen(name):
        """Delete an antigen and its associated rules."""
        try:
            antigen = db_session.query(Antigen).filter_by(name=name).first()
            if not antigen:
                return jsonify({"error": "Antigen not found"}), 404

            # Delete associated rules
            db_session.query(AntibodyRule).filter_by(target_antigen=antigen.name).delete()

            db_session.delete(antigen)
            db_session.commit()
            
            logger.info(f"Deleted antigen: {name}")
            return jsonify({"message": "Antigen deleted successfully"}), 200
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error deleting antigen {name}: {e}")
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
                {"name": "f", "system": "Rh"},  # Rh composite antigen
                {"name": "Cw", "system": "Rh"},  # Rh variant
                {"name": "V", "system": "Rh"},   # Rh variant
                
                # Kell System
                {"name": "K", "system": "Kell"},
                {"name": "k", "system": "Kell"},
                {"name": "Kpa", "system": "Kell"},  # Kell variant
                {"name": "Kpb", "system": "Kell"},  # Kell variant
                {"name": "Jsa", "system": "Kell"},  # Kell variant
                {"name": "Jsb", "system": "Kell"},  # Kell variant
                
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
                {"name": "Leb", "system": "Lewis"},
                
                # Lutheran System
                {"name": "Lua", "system": "Lutheran"},
                {"name": "Lub", "system": "Lutheran"},
                
                # P System
                {"name": "P", "system": "P"},
                
                # Xg System
                {"name": "Xga", "system": "Xg"},
                
                # Wright System
                {"name": "Wra", "system": "Wright"}
            ]

            # Clear existing antigens
            db_session.query(Antigen).delete()

            # Add new antigens
            for antigen_data in base_antigens:
                new_antigen = Antigen(**antigen_data)
                db_session.add(new_antigen)

            db_session.commit()
            logger.info("Base antigens initialized successfully")
            return jsonify({"message": "Base antigens initialized successfully"}), 200
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error initializing base antigens: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigens/pairs', methods=['GET'])
    def get_antigen_pairs():
        """Get antigen pairs for homozygous rules."""
        try:
            # Get all antigens
            antigens = db_session.query(Antigen).all()
            antigen_names = [antigen.name for antigen in antigens]
            
            # Define common antigen pairs based on blood group systems
            # This could be made configurable in the database later
            antigen_pairs = {
                # Rh System
                'D': ['C', 'c', 'E', 'e'],
                'C': ['D', 'E', 'e'],
                'c': ['D', 'E', 'e'],
                'E': ['D', 'C', 'c'],
                'e': ['D', 'C', 'c'],
                
                # Kell System
                'K': ['k'],
                'k': ['K'],
                'Kpa': ['Kpb'],
                'Kpb': ['Kpa'],
                'Jsa': ['Jsb'],
                'Jsb': ['Jsa'],
                
                # Duffy System
                'Fya': ['Fyb'],
                'Fyb': ['Fya'],
                
                # Kidd System
                'Jka': ['Jkb'],
                'Jkb': ['Jka'],
                
                # MNS System
                'M': ['N', 'S', 's'],
                'N': ['M', 'S', 's'],
                'S': ['M', 'N', 's'],
                's': ['M', 'N', 'S'],
                
                # Lewis System
                'Lea': ['Leb'],
                'Leb': ['Lea'],
                
                # Lutheran System
                'Lub': ['Lua'],
                'Lua': ['Lub'],
                
                # Rh System (additional variants)
                'Cw': ['C', 'c'],
                'V': ['D', 'E', 'e'],
                'f': ['C', 'c', 'E', 'e']
            }
            
            # Filter pairs to only include antigens that exist in the database
            filtered_pairs = {}
            for antigen, pairs in antigen_pairs.items():
                if antigen in antigen_names:
                    filtered_pairs[antigen] = [pair for pair in pairs if pair in antigen_names]
            
            return jsonify({
                'antigen_pairs': filtered_pairs,
                'available_antigens': antigen_names
            })
        except Exception as e:
            logger.error(f"Error getting antigen pairs: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigens/valid', methods=['GET'])
    def get_valid_antigens():
        """Get all antigens that exist in the Antigen table and have at least one enabled antibody rule."""
        try:
            # Get all antigens
            antigens = db_session.query(Antigen).all()
            antigen_names = {antigen.name: antigen for antigen in antigens}

            # Get all enabled antibody rules
            rules = db_session.query(AntibodyRule).filter_by(enabled=True).all()
            antigens_with_rules = set(rule.target_antigen for rule in rules)

            # Only include antigens that have at least one enabled rule
            valid_antigens = [antigen_names[name] for name in antigens_with_rules if name in antigen_names]

            # Return as list of dicts with name and system
            return jsonify([
                {"name": antigen.name, "system": antigen.system} for antigen in valid_antigens
            ]), 200
        except Exception as e:
            logger.error(f"Error getting valid antigens: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigens/default-order', methods=['GET'])
    def get_default_antigen_order():
        """Return the default antigen order (Panocell order) as a JSON array."""
        try:
            from default_rules import get_default_antigen_order
            return jsonify(get_default_antigen_order()), 200
        except Exception as e:
            logger.error(f"Error getting default antigen order: {e}")
            return jsonify({"error": str(e)}), 500

    # Antibody Rules Management Routes
    @app.route('/api/antibody-rules', methods=['GET'])
    def get_antibody_rules():
        """Get all antibody rules."""
        try:
            rules = db_session.query(AntibodyRule).all()
            return jsonify([rule.to_dict() for rule in rules])
        except Exception as e:
            logger.error(f"Error getting antibody rules: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-rules', methods=['POST'])
    def create_antibody_rule():
        """Create a new antibody rule."""
        try:
            data = request.json
            if not data or 'rule_type' not in data or 'target_antigen' not in data or 'rule_data' not in data:
                return jsonify({"error": "Missing required fields"}), 400

            # Prepare rule data
            rule_data_json = json.dumps(data['rule_data'])
            
            new_rule = AntibodyRule(
                rule_type=data['rule_type'],
                target_antigen=data['target_antigen'],
                rule_data=rule_data_json,
                description=data.get('description', ''),
                enabled=data.get('enabled', True)
            )
            db_session.add(new_rule)
            db_session.commit()
            
            logger.info(f"Created new antibody rule for: {data['target_antigen']}")
            return jsonify(new_rule.to_dict()), 201
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error creating antibody rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-rules/<int:rule_id>', methods=['GET'])
    def get_antibody_rule(rule_id):
        """Get a specific antibody rule."""
        try:
            rule = db_session.query(AntibodyRule).filter_by(id=rule_id).first()
            if not rule:
                return jsonify({"error": "Rule not found"}), 404
            return jsonify(rule.to_dict())
        except Exception as e:
            logger.error(f"Error getting antibody rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-rules/<int:rule_id>', methods=['PUT'])
    def update_antibody_rule(rule_id):
        """Update an antibody rule."""
        try:
            rule = db_session.query(AntibodyRule).filter_by(id=rule_id).first()
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            data = request.json
            if data.get('rule_type'):
                rule.rule_type = data['rule_type']
            if data.get('target_antigen'):
                rule.target_antigen = data['target_antigen']
            if data.get('rule_data'):
                rule.rule_data = json.dumps(data['rule_data'])
            if data.get('description') is not None:
                rule.description = data['description']
            if data.get('enabled') is not None:
                rule.enabled = data['enabled']

            db_session.commit()
            logger.info(f"Updated antibody rule: {rule_id}")
            return jsonify(rule.to_dict())
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error updating antibody rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-rules/<int:rule_id>', methods=['DELETE'])
    def delete_antibody_rule(rule_id):
        """Delete an antibody rule."""
        try:
            rule = db_session.query(AntibodyRule).filter_by(id=rule_id).first()
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            db_session.delete(rule)
            db_session.commit()
            
            logger.info(f"Deleted antibody rule: {rule_id}")
            return jsonify({"message": "Rule deleted successfully"})
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error deleting antibody rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-rules/delete-all', methods=['DELETE'])
    def delete_all_antibody_rules():
        """Delete all antibody rules."""
        try:
            db_session.query(AntibodyRule).delete()
            db_session.commit()
            
            logger.info("Deleted all antibody rules")
            return jsonify({"message": "All rules deleted successfully"})
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error deleting all antibody rules: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antibody-rules/initialize', methods=['POST'])
    def initialize_antibody_rules():
        """Initialize default antibody rules."""
        try:
            # Clear existing rules
            db_session.query(AntibodyRule).delete()
            
            # Get default rules
            default_rules = get_default_rules()
            
            # Add new rules
            for rule_data in default_rules:
                rule_data_json = json.dumps(rule_data['rule_data'])
                rule = AntibodyRule(
                    rule_type=rule_data['rule_type'],
                    target_antigen=rule_data['target_antigen'],
                    rule_data=rule_data_json,
                    description=rule_data['description'],
                    enabled=True
                )
                db_session.add(rule)
            
            db_session.commit()
            logger.info("Default antibody rules initialized successfully")
            return jsonify({"message": "Default antibody rules initialized successfully"}), 200
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error initializing default antibody rules: {e}")
            return jsonify({"error": str(e)}), 500 