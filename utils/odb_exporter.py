# -*- coding=utf-8 -*-

# ------------------------------------------------------------------
# File Name:        odb_exporter.py
# Author:           Han Xudong
# Version:          1.0.1
# Created:          2024/02/21
# Description:      This is a script to export result from odb file.
#                   Support history and field output.
#                   Must be run with Abaqus.
# Function List:    None
# History:
#       <author>        <version>       <time>      <desc>
#       Han Xudong      1.0.0           2024/02/21  Created file
#       Han Xudong      1.0.1           2024/08/17  Restructured
# ------------------------------------------------------------------

from abaqus import *
from odbAccess import *
from abaqusConstants import *
import sys
import json

# Open odb file
path = sys.argv[-3]
file = sys.argv[-2]
output = sys.argv[-1]
# Open odb file
odb = openOdb("../" + path + file)
# Load output parameters
params = json.load(open("../templates/output/" + output + ".json", "r"))

# Export result
result = dict()
if params["type"] == "history":
    # Get history output
    region = odb.steps[str(params["step"])].historyRegions[str(params["region"])]

    for output in params["outputs"]:
        result[output] = region.historyOutputs[str(output + "  on section " + params["section"])].data[-1][1]
elif params["type"] == "field":
    # Get field output
    field_outputs = odb.steps[params["step"]].frames[-1].fieldOutputs
    if params["set"] == "node":
        # Get node set
        region = odb.rootAssembly.nodeSets[params["region"]]
    elif params["set"] == "element":
        # Get element set
        region = odb.rootAssembly.elementSets[params["region"]]
    
    for output in params["outputs"]:
        values = field_outputs[output].getSubset(region=region).values
        label_values = list()
        for value in values:
            if params["set"] == "node":
                # Get node label and data
                label_values.append([value.nodeLabel, 
                                     value.data[0], 
                                     value.data[1], 
                                     value.data[2]])
            elif params["set"] == "element":
                # Get element label and data
                label_values.append([value.elementLabel, 
                                     value.data[0], 
                                     value.data[1], 
                                     value.data[2], 
                                     value.data[3], 
                                     value.data[4], 
                                     value.data[5]])
        
        result[output] = label_values

# Export result to json file
with open("../" + path + file.replace(".odb", ".json"), "w") as f:
    json.dump(result, 
              f,
              sort_keys=True, 
              indent=4, 
              separators=(",", ": "))

# Close odb
odb.close()