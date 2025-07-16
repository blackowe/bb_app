"""
Consolidated antigen routes.
This module handles all antigen and antigen rule management endpoints.
"""

from flask import request, jsonify, render_template, current_app
from models import Antigen, AntigenRule
from default_rules import get_default_rules
import logging

logger = logging.getLogger(__name__)

def register_antigen_routes(app, db_session):
    """Register all antigen and antigen rule routes."""
    
    @app.route('/antigens')
    def antigens_page():
        """Render the antigens management page."""
        return render_template('antigen_rules.html')

    @app.route('/antigen-rules')
    def antigen_rules_page():
        """Render the antigen rules management page."""
        return render_template('antigen_rules.html')

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
            db_session.query(AntigenRule).filter(
                (AntigenRule.target_antigen == antigen.name) |
                (AntigenRule.rule_antigens.like(f"%{antigen.name}%"))
            ).delete()

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
                {"name": "Leb", "system": "Lewis"},
                
                # P System
                {"name": "P", "system": "P"}
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

    # Antigen Rules Management Routes
    @app.route('/api/antigen-rules', methods=['GET'])
    def get_rules():
        """Get all antigen rules."""
        try:
            rules = db_session.query(AntigenRule).all()
            return jsonify([rule.to_dict() for rule in rules])
        except Exception as e:
            logger.error(f"Error getting antigen rules: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules', methods=['POST'])
    def create_rule():
        """Create a new antigen rule."""
        try:
            data = request.json
            if not data or 'target_antigen' not in data or 'rule_type' not in data:
                return jsonify({"error": "Missing required fields"}), 400

            # Prepare rule data
            rule_data = {
                'target_antigen': data['target_antigen'],
                'rule_type': data['rule_type'],
                'rule_conditions': data.get('rule_conditions', '{}'),
                'rule_antigens': data.get('rule_antigens', ''),
                'required_count': data.get('required_count', 1),
                'description': data.get('description', '')
            }

            new_rule = AntigenRule(**rule_data)
            db_session.add(new_rule)
            db_session.commit()
            
            logger.info(f"Created new antigen rule for: {data['target_antigen']}")
            return jsonify(new_rule.to_dict()), 201
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error creating antigen rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/<int:rule_id>', methods=['GET'])
    def get_rule(rule_id):
        """Get a specific antigen rule."""
        try:
            rule = db_session.query(AntigenRule).filter_by(id=rule_id).first()
            if not rule:
                return jsonify({"error": "Rule not found"}), 404
            return jsonify(rule.to_dict())
        except Exception as e:
            logger.error(f"Error getting antigen rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/<int:rule_id>', methods=['PUT'])
    def update_rule(rule_id):
        """Update an antigen rule."""
        try:
            rule = db_session.query(AntigenRule).filter_by(id=rule_id).first()
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            data = request.json
            if data.get('target_antigen'):
                rule.target_antigen = data['target_antigen']
            if data.get('rule_type'):
                rule.rule_type = data['rule_type']
            if data.get('rule_conditions'):
                rule.rule_conditions = data['rule_conditions']
            if data.get('rule_antigens'):
                rule.rule_antigens = data['rule_antigens']
            if data.get('required_count'):
                rule.required_count = data['required_count']
            if data.get('description'):
                rule.description = data['description']

            db_session.commit()
            logger.info(f"Updated antigen rule: {rule_id}")
            return jsonify(rule.to_dict())
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error updating antigen rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/<int:rule_id>', methods=['DELETE'])
    def delete_rule(rule_id):
        """Delete an antigen rule."""
        try:
            rule = db_session.query(AntigenRule).filter_by(id=rule_id).first()
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            db_session.delete(rule)
            db_session.commit()
            
            logger.info(f"Deleted antigen rule: {rule_id}")
            return jsonify({"message": "Rule deleted successfully"})
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error deleting antigen rule: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/delete-all', methods=['DELETE'])
    def delete_all_rules():
        """Delete all antigen rules."""
        try:
            db_session.query(AntigenRule).delete()
            db_session.commit()
            
            logger.info("Deleted all antigen rules")
            return jsonify({"message": "All rules deleted successfully"})
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error deleting all antigen rules: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/initialize', methods=['POST'])
    def initialize_rules():
        """Initialize default antigen rules."""
        try:
            # Clear existing rules
            db_session.query(AntigenRule).delete()
            
            # Get default rules
            default_rules = get_default_rules()
            
            # Add new rules
            for rule_data in default_rules:
                rule = AntigenRule(**rule_data)
                db_session.add(rule)
            
            db_session.commit()
            logger.info("Antigen rules initialized successfully")
            return jsonify({"message": "Antigen rules initialized successfully"})
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error initializing antigen rules: {e}")
            return jsonify({"error": str(e)}), 500 