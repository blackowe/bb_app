from flask import request, jsonify
from models import AntigenPair

def register_antigen_rules_routes(app, db_session):
    @app.route('/api/antigen-rules', methods=['GET'])
    def get_antigen_rules():
        """Get all configured antigen pair rules."""
        try:
            rules = db_session.query(AntigenPair).all()
            return jsonify([rule.to_dict() for rule in rules]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules', methods=['POST'])
    def create_antigen_rule():
        """Create a new antigen pair rule or single antigen rule."""
        try:
            data = request.json
            required_fields = ['antigen1', 'rule_type', 'required_count']
            
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing required fields"}), 400
                
            if data['rule_type'] not in ['homozygous', 'heterozygous', 'single']:
                return jsonify({"error": "Invalid rule type"}), 400

            # For single antigen rules, antigen2 should be None
            if data['rule_type'] == 'single' and 'antigen2' in data:
                return jsonify({"error": "Single antigen rules should not have antigen2"}), 400

            # For paired rules, antigen2 is required
            if data['rule_type'] in ['homozygous', 'heterozygous']:
                if 'antigen2' not in data:
                    return jsonify({"error": "Paired rules require antigen2"}), 400

            # Check if rule already exists
            existing_rule_query = db_session.query(AntigenPair).filter(
                AntigenPair.antigen1 == data['antigen1']
            )
            
            if 'antigen2' in data:
                existing_rule_query = existing_rule_query.filter(
                    ((AntigenPair.antigen2 == data['antigen2']) |
                    (AntigenPair.antigen1 == data['antigen2']) & (AntigenPair.antigen2 == data['antigen1']))
                )
            else:
                existing_rule_query = existing_rule_query.filter(AntigenPair.antigen2.is_(None))
                
            existing_rule = existing_rule_query.filter_by(rule_type=data['rule_type']).first()

            if existing_rule:
                return jsonify({"error": "Rule already exists for this antigen"}), 409

            new_rule = AntigenPair(
                antigen1=data['antigen1'],
                antigen2=data.get('antigen2'),  # Will be None for single antigen rules
                rule_type=data['rule_type'],
                required_count=data['required_count']
            )
            db_session.add(new_rule)
            db_session.commit()
            
            return jsonify(new_rule.to_dict()), 201
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/<int:rule_id>', methods=['PUT'])
    def update_antigen_rule(rule_id):
        """Update an existing antigen pair rule."""
        try:
            rule = db_session.query(AntigenPair).get(rule_id)
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            data = request.json
            if 'rule_type' in data and data['rule_type'] not in ['homozygous', 'heterozygous']:
                return jsonify({"error": "Invalid rule type"}), 400

            for key in ['antigen1', 'antigen2', 'rule_type', 'required_count']:
                if key in data:
                    setattr(rule, key, data[key])

            db_session.commit()
            return jsonify(rule.to_dict()), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/<int:rule_id>', methods=['DELETE'])
    def delete_antigen_rule(rule_id):
        """Delete an antigen pair rule."""
        try:
            rule = db_session.query(AntigenPair).get(rule_id)
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            db_session.delete(rule)
            db_session.commit()
            return jsonify({"message": "Rule deleted successfully"}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/delete-all', methods=['DELETE'])
    def delete_all_antigen_rules():
        """Delete all antigen pair rules."""
        try:
            count = db_session.query(AntigenPair).delete()
            db_session.commit()
            return jsonify({
                "message": f"Successfully deleted all antigen rules ({count} rules deleted)"
            }), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route('/api/antigen-rules/initialize', methods=['POST'])
    def initialize_default_rules():
        """Initialize default antigen pair rules."""
        try:
            # Define default rules
            default_rules = [
                # Rh System
                {"antigen1": "D", "rule_type": "single", "required_count": 1},  # D antigen as single rule
                {"antigen1": "E", "antigen2": "e", "rule_type": "homozygous", "required_count": 1},
                {"antigen1": "C", "antigen2": "c", "rule_type": "homozygous", "required_count": 1},
                
                # Kell System
                {"antigen1": "K", "antigen2": "k", "rule_type": "homozygous", "required_count": 1},
                {"antigen1": "K", "antigen2": "k", "rule_type": "heterozygous", "required_count": 3},
                
                # Duffy System
                {"antigen1": "Fya", "antigen2": "Fyb", "rule_type": "homozygous", "required_count": 1},
                
                # Kidd System
                {"antigen1": "Jka", "antigen2": "Jkb", "rule_type": "homozygous", "required_count": 1},
                
                # MNS System
                {"antigen1": "M", "antigen2": "N", "rule_type": "homozygous", "required_count": 1},
                {"antigen1": "S", "antigen2": "s", "rule_type": "homozygous", "required_count": 1},
                
                # Lewis System
                {"antigen1": "Lea", "antigen2": "Leb", "rule_type": "homozygous", "required_count": 1}
            ]

            # Clear existing rules
            db_session.query(AntigenPair).delete()

            # Add new rules
            for rule in default_rules:
                new_rule = AntigenPair(**rule)
                db_session.add(new_rule)

            db_session.commit()
            return jsonify({"message": "Default rules initialized successfully"}), 200
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500 