from flask import request, jsonify, render_template, Blueprint, current_app
from models import AntigenRule, Antigen
from flask_sqlalchemy import SQLAlchemy
from default_rules import get_default_rules

antigen_rules_bp = Blueprint('antigen_rules', __name__)

def register_antigen_rules_routes(app, db_session):
    app.register_blueprint(antigen_rules_bp)
    app.extensions['db_session'] = db_session

def initialize_default_rules(db_session):
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
        return True
    except Exception as e:
        db_session.rollback()
        raise e

def initialize_base_antigens(db_session):
    """Initialize base antigens if they don't exist."""
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

        # Add any missing antigens
        for antigen_data in base_antigens:
            existing_antigen = db_session.query(Antigen).filter_by(name=antigen_data['name']).first()
            if not existing_antigen:
                new_antigen = Antigen(**antigen_data)
                db_session.add(new_antigen)

        db_session.commit()
        return True
    except Exception as e:
        db_session.rollback()
        raise e

@antigen_rules_bp.route('/api/antigen-rules', methods=['GET'])
def get_rules():
    db_session = current_app.extensions['db_session']
    try:
        rules = db_session.query(AntigenRule).all()
        return jsonify([rule.to_dict() for rule in rules])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@antigen_rules_bp.route('/api/antigen-rules/init', methods=['POST'])
def init_rules():
    db_session = current_app.extensions['db_session']
    try:
        # First ensure base antigens exist
        initialize_base_antigens(db_session)
        
        # Clear existing rules
        db_session.query(AntigenRule).delete()
        
        # Get default rules
        default_rules = get_default_rules()
        
        # Add new rules
        for rule_data in default_rules:
            rule = AntigenRule(**rule_data)
            db_session.add(rule)
        
        db_session.commit()
        return jsonify({"message": "Antigen rules initialized successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 500 