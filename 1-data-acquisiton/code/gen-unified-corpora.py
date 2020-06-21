#!/usr/bin/env python
# coding: utf-8

from os.path import join
import os
import json
from utils import *

# Step 0: Set the variables
CURR_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(CURR_DIR)

DATA_DIR = os.path.join(ROOT_DIR, "data")
ANNOTATIONS_DIR = join(DATA_DIR, "ArgumentAnnotatedEssays-2.0/brat-project-final/")
BIAS_FILE = join(DATA_DIR, "UKP-OpposingArgumentsInEssays_v1.0/labels.tsv")
SUFFICIENCY_FILE = join(DATA_DIR, "UKP-InsufficientArguments_v1.0/data-tokenized.tsv")
SAMPLE_JSON = os.path.join(CURR_DIR, "provided_data/sample_output.json")


# Step 1: Read the essay text
essays = read_essay_text(DATA_DIR)

# Step 2: Read the annotations
annotations = read_essay_annotations(ANNOTATIONS_DIR)

# Step 3: Read the bias data
bias = read_bias(BIAS_FILE)

# Step 4: Read the sufficiency data
sufficiency = read_sufficiency(SUFFICIENCY_FILE)

# Step 5: Combine all the individual elements for each essay in a list
output = []
for key, value in essays.items():
    data = {}
    data["id"] = int(re.findall("\d+", key)[0])
    data["text"] = value
    data.update(annotations[key])
    data.update(bias[key])
    data.update(sufficiency[key])
    output.append(data)

# Step 6: Sort to ensure the numbering is in correct order
output = sorted(output, key=lambda x: x["id"])

# Step 7: Check that the value matches the sample provided completely
with open(SAMPLE_JSON) as f:
    sample = json.loads(f.read()).pop()
output_sample = output[sample["id"] - 1]
for key in sample:
    msg = f"Discrepancy b/w sample JSON and read data for key --> {key}"
    assert sample[key] == output_sample[key], msg


# Step 8: Generate the output JSON in the data folder
output_fp = join(DATA_DIR, "output.json")
with open(output_fp, mode="w") as f:
    f.write(json.dumps(output))

# Step 9: Print final message
if os.path.exists(output_fp):
    print(f"Output JSON file generated!\nOutput --> {output_fp}")
else:
    raise Exception("File could not be successfully generated.")
