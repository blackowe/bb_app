Antibody Identification Guidelines and Rule setup
These rules are to be referred to during the antibody identification process. They are used to set standards and criteria which must be met to ensure antibodies are properly identified and antigens are ruled out correctly.

Rule
ABSpecificRO(A,B,C,X) – A is the suspected Antibody, B,C are both antigen, X is a integer. Will Rule out B antigen when patient is 0 for cells with expression B=+, C=+. Must have minimum of X number of occurrences for B antigen to be ruled out. Note this rule is to be used when attempting to identify suspected antibody A. Suspected antibody will be in the STRO category of the antibody identification process.
Homo[(A,B),] – is a list of tuples where A antigen will be ruled out when patient is 0 for cells with expression A=+, B=0. A and B are antigens.
Hetero(A,B,X) – can rule out A antigen when patient is 0 for cells with expression A=+, B=+ . Must have X number of cells/occurrence to successfully rule out A antigen. A and B are antigens.
SingleAG([A,B,C,...]) – Antigens in the SingleAG() category/list are single and are ruled out when patient is 0 and cell has expression of +, meaning A antigen ruled out when patient is 0 and A = +. SingleAG() should be a list of antigens, A,B,C are antigens.

LowF([A,B,C,…]) – Antigens in the LowF() category/list are automatically ruled out due to low prevalence. A,B,C are antigens

Sample of Active Rules:
ABSpecificRO (D,C,c,3)
ABSpecificRO (D,E,e,3)
ABSpecificRO (c,E,e,3)
ABSpecificRO (e,C,c,3)
SingleAG(D,Lea,Leb,P, Xga,f)
LowF(Kpa,Jsa,Lua,Cw,Wra,V)
Homo[ (c,C), (C,c), (E,e), (e,E), (K,k), (k,k), (Kpb,Kpa), (Jsa,Jsb), (Fya,Fyb), (Fyb,Fya), (Jka,Jkb), (Jkb,Jka), (M,N), (N,M), (S,s), (s,S), (Lub,Lua) ]
Hetero(K,k,3)
