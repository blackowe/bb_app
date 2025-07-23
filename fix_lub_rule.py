#!/usr/bin/env python3
"""
Script to fix the Lub rule by correcting the antigen pair order.
"""

import requests
import json

def fix_lub_rule():
    """Fix the Lub rule by correcting the antigen pair order."""
    base_url = "http://localhost:5000"
    
    print("🔧 Fixing Lub Rule")
    print("=" * 40)
    
    try:
        # Get current Lub rule
        print("1. Getting current Lub rule:")
        response = requests.get(f"{base_url}/api/antibody-rules")
        if response.status_code == 200:
            rules = response.json()
            
            lub_rules = [rule for rule in rules if rule['target_antigen'] == 'Lub']
            if lub_rules:
                lub_rule = lub_rules[0]
                print(f"Current rule ID: {lub_rule['id']}")
                print(f"Current rule data: {lub_rule['rule_data']}")
                
                # Check if the rule is incorrect
                antigen_pairs = lub_rule['rule_data'].get('antigen_pairs', [])
                if antigen_pairs and antigen_pairs[0] == ['Lua', 'Lub']:
                    print("❌ Rule is incorrect: ['Lua', 'Lub'] should be ['Lub', 'Lua']")
                    
                    # Fix the rule
                    print("2. Fixing the rule:")
                    fixed_rule_data = {
                        "target_antigen": "Lub",
                        "rule_type": "homo",
                        "rule_data": {
                            "antigen_pairs": [["Lub", "Lua"]]
                        },
                        "description": "Homo(Lub,Lua) - Lub antigen ruled out when patient is 0 for cells with expression Lub=+, Lua=0",
                        "enabled": True
                    }
                    
                    response = requests.put(
                        f"{base_url}/api/antibody-rules/{lub_rule['id']}",
                        headers={'Content-Type': 'application/json'},
                        json=fixed_rule_data
                    )
                    
                    if response.status_code == 200:
                        print("✅ Successfully fixed Lub rule")
                        updated_rule = response.json()
                        print(f"Updated rule data: {updated_rule['rule_data']}")
                    else:
                        print(f"❌ Failed to fix rule: {response.status_code}")
                        print(f"Response: {response.text}")
                else:
                    print("✅ Rule is already correct")
            else:
                print("❌ No Lub rule found")
        else:
            print(f"Error: {response.status_code}")
        
        # Test the fix
        print("\n3. Testing the fix:")
        response = requests.get(f"{base_url}/api/abid")
        if response.status_code == 200:
            data = response.json()
            
            ruled_out = data.get('ruled_out', [])
            stro = data.get('stro', [])
            matches = data.get('matches', [])
            
            print(f"Ruled Out: {ruled_out}")
            print(f"STRO: {stro}")
            print(f"Matches: {matches}")
            
            if 'Lub' in ruled_out:
                print("✅ Lub is now correctly ruled out!")
            elif 'Lub' in stro:
                print("⚠️  Lub is in STRO")
            elif 'Lub' in matches:
                print("❌ Lub is still incorrectly in matches!")
            else:
                print("❓ Lub not found in any category")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_lub_rule() 