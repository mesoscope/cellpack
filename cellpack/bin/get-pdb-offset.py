import os
import fire
from cellpack.autopack.pdb_tools import download
from cellpack.autopack.pdb_tools import center_of_pdb
from cellpack.autopack.pdb_tools.download import SAVE_FOLDER


def get_pdbs(pdb_codes):
    print(pdb_codes)
    pdb_list = []
    for pdb_code in pdb_codes:
        if os.path.isfile(f"{SAVE_FOLDER}{pdb_code}") and pdb_code[-4:] != ".pdb":
            # Read in input file
            f = open(pdb_code, "r")
            tmp_list = f.readlines()
            f.close()

            # Strip comments and blank lines, recombine file, then split on all
            # white space
            tmp_list = [p for p in tmp_list if p[0] != "#" and p.strip() != ""]
            tmp_list = "".join(tmp_list)
            tmp_list = tmp_list.split()
            tmp_list = [p.lower() for p in tmp_list]
            pdb_list.extend(tmp_list)

        else:

            # Lower case, remove .pdb if appended
            pdb_id = pdb_code.lower()
            if pdb_id[-4:] == ".pdb":
                pdb_id = pdb_id[:-4]

            pdb_list.append(pdb_id)

    # Download pdbs
    download.pdbDownload(pdb_list)

    for pdb_file in pdb_list:

        # Load in pdb file
        f = open(f"{SAVE_FOLDER}{pdb_file}.pdb", "r")
        pdb = f.readlines()
        f.close()

        center, pdb_out = center_of_pdb.pdbCentermass(pdb, True, False, False)
        print("%s %s" % (pdb_file, "".join(center)))

        # If the user wants re-centered coordinates, write them out
        out_file = f"{SAVE_FOLDER}centered/{pdb_file}.pdb"
        g = open(out_file, "w")
        g.writelines(pdb_out)
        g.close()


def main():
    fire.Fire(get_pdbs)


if __name__ == "__main__":
    main()
