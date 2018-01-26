"""
Module that helps with parsind CST files into a more efficent and simpler format
"""

import os.path
DELIMITER = ";"

def split_output_file(input_file, tmin=None, tmax=None):
    """
    Splits a CST ASCII Output File (PICStyle) into one part containing the costant particle
    properties and one part containing the trajectories. The files are located in the same folder
    as the input file.
    If tmin and tmax are given only timesteps with these boundaries will be saved into the output
    """
    filepath = os.path.dirname(input_file)
    filename = os.path.basename(input_file)
    filename= os.path.splittext(filename)[0]

    trajectory_header = "% particleID;Time;x;y;z;px(normed);py(normed);pz(normed)"
    constants_header = "% particleID;mass(kg);macroCharge(C);sourceID"

    trajectory_file = filepath + "\\" + filename + "-trajectories.txt"
    constants_file = filepath + "\\" + filename + "-constants.txt"

    with open(input_file, 'r') as inp,\
         open(trajectory_file, 'w') as out_tr,\
         open(constants_file, 'w') as out_co:

        # Write headers
        out_tr.write(trajectory_header + "\n")
        out_co.write(constants_header + "\n")

        # Skip 7 rows
        for dummy in range(7):
            inp.readline()

        # Process each line in inp
        last_particleID = ""
        for line in inp:
            # Break on empty line(last line)
            if line == "":
                break
            data = line.split()

            # Save trajectory info
            if ((tmin is None or float(data[9]) >= tmin) and
                    (tmax is None or float(data[9]) <= tmax)):
                tr_ls = [data[10], data[9], data[0], data[1], data[2], data[3], data[4], data[5]]
                out_tr.write(DELIMITER.join(tr_ls) + "\n")

            # If reached new particle, update constants
            if data[10] != last_particleID:
                last_particleID = data[10]
                co_ls = [data[10], data[6], data[8], data[11]]
                out_co.write(DELIMITER.join(co_ls) + "\n")

        # Write End of File Markers
        out_tr.write("EOF")
        out_co.write("EOF")
    print("Conversion complete.")
