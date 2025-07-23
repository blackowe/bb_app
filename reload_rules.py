#!/usr/bin/env python3
"""
Script to reload the database with updated default rules.
"""

import json
import sqlite3
from default_rules import get_default_rules

def reload_rules():
    """Reload the database with updated default rules."""
    print("🔄 Reloading Antibody Rules")
    print("=" * 40)
    
    try:
        # Connect to the database
        conn = sqlite3.connect('local.db')
        cursor = conn.cursor()
        
        # Clear existing rules
        cursor.execute("DELETE FROM antibody_rule")
        print("✅ Cleared existing rules")
        
        # Get updated default rules
        default_rules = get_default_rules()
        print(f"📋 Loaded {len(default_rules)} default rules")
        
        # Add new rules
        for rule_data in default_rules:
            # Convert rule_data to JSON string for storage
            rule_data_json = json.dumps(rule_data['rule_data'])
            
            cursor.execute("""
                INSERT INTO antibody_rule (rule_type, target_antigen, rule_data, description, enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule_data['rule_type'],
                rule_data['target_antigen'],
                rule_data_json,
                rule_data['description'],
                True
            ))
        
        # Commit changes
        conn.commit()
        print(f"✅ Successfully loaded {len(default_rules)} rules into database")
        
        # Verify the rules were loaded
        cursor.execute("SELECT COUNT(*) FROM antibody_rule WHERE enabled = 1")
        count = cursor.fetchone()[0]
        print(f"📊 Total enabled rules in database: {count}")
        
        # Check for S and s rules specifically
        cursor.execute("SELECT target_antigen, rule_type FROM antibody_rule WHERE target_antigen IN ('S', 's')")
        s_rules = cursor.fetchall()
        
        print(f"🔍 S and s rules found: {len(s_rules)}")
        for antigen, rule_type in s_rules:
            print(f"  {antigen}: {rule_type}")
        
        conn.close()
        print("✅ Database reloaded successfully!")
        
    except Exception as e:
        print(f"❌ Error reloading rules: {e}")

if __name__ == "__main__":
    reload_rules() 