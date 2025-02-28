# bb_app chat gpt prompt:




# test logic for antigen rules:
        if antigen in ["K"] and (homozygous_count >= 1 or heterozygous_count >= 3):
            ruled_out_flag = True
        elif antigen in ["D"] and homozygous_count >= 1:
            ruled_out_flag = True
        elif antigen in ["f", "P", "Lea", "Leb", "Xga"] and homozygous_count + heterozygous_count >= 1:
            ruled_out_flag = True
        elif antigen in antigen_pairs.keys() and homozygous_count >= 1:
            ruled_out_flag = True