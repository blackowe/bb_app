import json

def get_default_rules():
    """Return the default antibody rules based on RULE_CREATION_GUIDE.md."""
    return [
        # ABSpecificRO Rules
        {
            "rule_type": "abspecific",
            "target_antigen": "C",
            "rule_data": {
                "antibody": "D",
                "antigen1": "C",
                "antigen2": "c",
                "required_count": 3
            },
            "description": "ABSpecificRO(D,C,c,3) - Rule out C antigen when patient is 0 for cells with expression C=+, c=+"
        },
        {
            "rule_type": "abspecific",
            "target_antigen": "E",
            "rule_data": {
                "antibody": "D",
                "antigen1": "E",
                "antigen2": "e",
                "required_count": 3
            },
            "description": "ABSpecificRO(D,E,e,3) - Rule out E antigen when patient is 0 for cells with expression E=+, e=+"
        },
        {
            "rule_type": "abspecific",
            "target_antigen": "c",
            "rule_data": {
                "antibody": "D",
                "antigen1": "c",
                "antigen2": "C",
                "required_count": 3
            },
            "description": "ABSpecificRO(D,c,C,3) - Rule out c antigen when patient is 0 for cells with expression c=+, C=+"
        },
        {
            "rule_type": "abspecific",
            "target_antigen": "e",
            "rule_data": {
                "antibody": "D",
                "antigen1": "e",
                "antigen2": "E",
                "required_count": 3
            },
            "description": "ABSpecificRO(D,e,E,3) - Rule out e antigen when patient is 0 for cells with expression e=+, E=+"
        },
        
        # SingleAG Rules
        {
            "rule_type": "single",
            "target_antigen": "D",
            "rule_data": {
                "antigens": ["D"]
            },
            "description": "SingleAG(D) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        {
            "rule_type": "single",
            "target_antigen": "Lea",
            "rule_data": {
                "antigens": ["Lea"]
            },
            "description": "SingleAG(Lea) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        {
            "rule_type": "single",
            "target_antigen": "Leb",
            "rule_data": {
                "antigens": ["Leb"]
            },
            "description": "SingleAG(Leb) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        {
            "rule_type": "single",
            "target_antigen": "P",
            "rule_data": {
                "antigens": ["P"]
            },
            "description": "SingleAG(P) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        {
            "rule_type": "single",
            "target_antigen": "Xga",
            "rule_data": {
                "antigens": ["Xga"]
            },
            "description": "SingleAG(Xga) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        {
            "rule_type": "single",
            "target_antigen": "f",
            "rule_data": {
                "antigens": ["f"]
            },
            "description": "SingleAG(f) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        {
            "rule_type": "single",
            "target_antigen": "Jsb",
            "rule_data": {
                "antigens": ["Jsb"]
            },
            "description": "SingleAG(Jsb) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        {
            "rule_type": "single",
            "target_antigen": "Kpb",
            "rule_data": {
                "antigens": ["Kpb"]
            },
            "description": "SingleAG(Kpb) - Single antigens ruled out when patient is 0 and cell has expression of +"
        },
        
        # LowF Rules
        {
            "rule_type": "lowf",
            "target_antigen": "Kpa",
            "rule_data": {
                "antigens": ["Kpa"]
            },
            "description": "LowF(Kpa) - Low frequency antigens automatically ruled out"
        },
        {
            "rule_type": "lowf",
            "target_antigen": "Jsa",
            "rule_data": {
                "antigens": ["Jsa"]
            },
            "description": "LowF(Jsa) - Low frequency antigens automatically ruled out"
        },
        {
            "rule_type": "lowf",
            "target_antigen": "Lua",
            "rule_data": {
                "antigens": ["Lua"]
            },
            "description": "LowF(Lua) - Low frequency antigens automatically ruled out"
        },
        {
            "rule_type": "lowf",
            "target_antigen": "Cw",
            "rule_data": {
                "antigens": ["Cw"]
            },
            "description": "LowF(Cw) - Low frequency antigens automatically ruled out"
        },
        {
            "rule_type": "lowf",
            "target_antigen": "Wra",
            "rule_data": {
                "antigens": ["Wra"]
            },
            "description": "LowF(Wra) - Low frequency antigens automatically ruled out"
        },
        {
            "rule_type": "lowf",
            "target_antigen": "V",
            "rule_data": {
                "antigens": ["V"]
            },
            "description": "LowF(V) - Low frequency antigens automatically ruled out"
        },
        
        
        # Homo Rules
        {
            "rule_type": "homo",
            "target_antigen": "c",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "C",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "E",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "e",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "K",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "k",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        
        # ADDED: Missing rules for S and s antigens
        {
            "rule_type": "homo",
            "target_antigen": "S",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "s",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        
        # ADDED: Missing rules for Fya and Fyb antigens
        {
            "rule_type": "homo",
            "target_antigen": "Fya",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "Fyb",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        
        # ADDED: Missing rules for Jka and Jkb antigens
        {
            "rule_type": "homo",
            "target_antigen": "Jka",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "Jkb",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        
        # ADDED: Missing rules for M and N antigens
        {
            "rule_type": "homo",
            "target_antigen": "M",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        {
            "rule_type": "homo",
            "target_antigen": "N",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        
        # ADDED: Missing rule for Lub antigen
        {
            "rule_type": "homo",
            "target_antigen": "Lub",
            "rule_data": {
                "antigen_pairs": [["c", "C"], ["C", "c"], ["E", "e"], ["e", "E"], ["K", "k"], ["k", "K"], 
                                 ["Kpb", "Kpa"], ["Jsa", "Jsb"], ["Fya", "Fyb"], ["Fyb", "Fya"], 
                                 ["Jka", "Jkb"], ["Jkb", "Jka"], ["M", "N"], ["N", "M"], ["S", "s"], 
                                 ["s", "S"], ["Lub", "Lua"]]
            },
            "description": "Homo[(c,C), (C,c), (E,e), (e,E), (K,k), (k,K), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua)]"
        },
        
        # Hetero Rules
        {
            "rule_type": "hetero",
            "target_antigen": "K",
            "rule_data": {
                "antigen_a": "K",
                "antigen_b": "k",
                "required_count": 3
            },
            "description": "Hetero(K,k,3) - Can rule out K antigen when patient is 0 for cells with expression K=+, k=+"
        }
    ] 