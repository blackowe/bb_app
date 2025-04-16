import json

def get_default_rules():
    """Return the default antigen rules."""
    return [
        # P System Rules
        {
            "target_antigen": "P",
            "rule_type": "standard",
            "rule_antigens": "P",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "P",
                        "cell_reaction": "+",
                        "patient_reaction": "0"
                    }
                ]
            }),
            "required_count": 1,
            "description": "P can be ruled out when patient=0 to cell where P=+"
        },

        # Rh System Rules
        {
            "target_antigen": "D",
            "rule_type": "standard",
            "rule_antigens": "D",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "D",
                        "cell_reaction": "+",
                        "patient_reaction": "0"
                    }
                ]
            }),
            "required_count": 1,
            "description": "D can be ruled out when patient=0 to cell where D=+"
        },
        {
            "target_antigen": "E",
            "rule_type": "standard",
            "rule_antigens": "E,e",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "E",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "e",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "E can be ruled out when patient=0 to cell where E=+ and e=0"
        },
        {
            "target_antigen": "e",
            "rule_type": "standard",
            "rule_antigens": "e,E",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "e",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "E",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "e can be ruled out when patient=0 to cell where e=+ and E=0"
        },
        {
            "target_antigen": "C",
            "rule_type": "standard",
            "rule_antigens": "C,c",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "C",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "c",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "C can be ruled out when patient=0 to cell where C=+ and c=0"
        },
        {
            "target_antigen": "c",
            "rule_type": "standard",
            "rule_antigens": "c,C",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "c",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "C",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "c can be ruled out when patient=0 to cell where c=+ and C=0"
        },
        
        # Kell System Rules
        {
            "target_antigen": "K",
            "rule_type": "composite",
            "rule_antigens": "K,k",
            "rule_conditions": json.dumps({
                "type": "composite",
                "conditions": [
                    {
                        "antigen": "K",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "k",
                                "cell_reaction": "0"
                            }
                        ],
                        "required_count": 1
                    },
                    {
                        "antigen": "K",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "k",
                                "cell_reaction": "+"
                            }
                        ],
                        "required_count": 3
                    }
                ],
                "operator": "OR"
            }),
            "required_count": 3,
            "description": "K can be ruled out when either: 1) patient=0 to cell where K=+ and k=0, or 2) patient=0 to 3 cells where K=+ and k=+"
        },
        {
            "target_antigen": "k",
            "rule_type": "standard",
            "rule_antigens": "k,K",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "k",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "K",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "k can be ruled out when patient=0 to cell where k=+ and K=0"
        },
        
        # Duffy System Rules
        {
            "target_antigen": "Fya",
            "rule_type": "standard",
            "rule_antigens": "Fya,Fyb",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "Fya",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "Fyb",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "Fya can be ruled out when patient=0 to cell where Fya=+ and Fyb=0"
        },
        {
            "target_antigen": "Fyb",
            "rule_type": "standard",
            "rule_antigens": "Fyb,Fya",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "Fyb",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "Fya",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "Fyb can be ruled out when patient=0 to cell where Fyb=+ and Fya=0"
        },
        
        # Kidd System Rules
        {
            "target_antigen": "Jka",
            "rule_type": "standard",
            "rule_antigens": "Jka,Jkb",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "Jka",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "Jkb",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "Jka can be ruled out when patient=0 to cell where Jka=+ and Jkb=0"
        },
        {
            "target_antigen": "Jkb",
            "rule_type": "standard",
            "rule_antigens": "Jkb,Jka",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "Jkb",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "Jka",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "Jkb can be ruled out when patient=0 to cell where Jkb=+ and Jka=0"
        },
        
        # MNS System Rules
        {
            "target_antigen": "M",
            "rule_type": "standard",
            "rule_antigens": "M,N",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "M",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "N",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "M can be ruled out when patient=0 to cell where M=+ and N=0"
        },
        {
            "target_antigen": "N",
            "rule_type": "standard",
            "rule_antigens": "N,M",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "N",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "M",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "N can be ruled out when patient=0 to cell where N=+ and M=0"
        },
        {
            "target_antigen": "S",
            "rule_type": "standard",
            "rule_antigens": "S,s",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "S",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "s",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "S can be ruled out when patient=0 to cell where S=+ and s=0"
        },
        {
            "target_antigen": "s",
            "rule_type": "standard",
            "rule_antigens": "s,S",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "s",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "S",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "s can be ruled out when patient=0 to cell where s=+ and S=0"
        },
        
        # Lewis System Rules
        {
            "target_antigen": "Lea",
            "rule_type": "standard",
            "rule_antigens": "Lea,Leb",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "Lea",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "Leb",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "Lea can be ruled out when patient=0 to cell where Lea=+ and Leb=0"
        },
        {
            "target_antigen": "Leb",
            "rule_type": "standard",
            "rule_antigens": "Leb,Lea",
            "rule_conditions": json.dumps({
                "type": "single",
                "conditions": [
                    {
                        "antigen": "Leb",
                        "cell_reaction": "+",
                        "patient_reaction": "0",
                        "paired_conditions": [
                            {
                                "antigen": "Lea",
                                "cell_reaction": "0"
                            }
                        ]
                    }
                ]
            }),
            "required_count": 1,
            "description": "Leb can be ruled out when patient=0 to cell where Leb=+ and Lea=0"
        }
    ] 