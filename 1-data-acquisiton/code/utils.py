#!/usr/bin/env python
# coding: utf-8

import os
import re
import json
import itertools
import heapq


def read_essay_text(data_folder, prefix="essay", ext=".txt"):
    """Walks through the data folder reading only essay text and storing them in a dictionary"""

    assert os.path.exists(data_folder), f"Folder {data_folder} does not exist"
    assert os.path.isdir(data_folder), f"Not a directory{data_folder}"

    essays = {}
    print("Reading essays...")

    for folder, subfolder, files in os.walk(data_folder):
        for file in files:
            if file.startswith(prefix) and file.endswith(ext):
                filepath = os.path.join(folder, file)
                with open(filepath, mode="r", encoding="utf8", newline="\n") as f:
                    data = f.read()

                name, _ = os.path.splitext(file)
                if name not in essays:
                    essays[name] = data
                else:
                    # verify
                    msg = f"Essay {name} non-identical in diff. folders"
                    assert essays[name] == data, msg

    return essays


def read_essay_annotations(data_folder, prefix="essay", ext=".ann"):
    """Walks through the data folder reading only essay annotations"""

    assert os.path.exists(data_folder), f"Folder {data_folder} does not exist"
    assert os.path.isdir(data_folder), f"Not a directory{data_folder}"

    # Basic structrue of regular expr (incl. optional part)
    # tab + boundaried_str + spaces + boundaried_nr + spaces + boundaried_nr + spaces + [tab + text]
    regex_dict = {
        "major_claim": {
            "span": r"\t\bmajorclaim\b\s+(\b\d+\b)\s+(\b\d+\b)",
            "text": r"\t\bmajorclaim\b\s+\b\d+\b\s+\b\d+\b\t(.+)",
        },
        "claims": {
            "span": r"\t\bclaim\b\s+(\b\d+\b)\s+(\b\d+\b)",
            "text": r"\t\bclaim\b\s+\b\d+\b\s+\b\d+\b\t(.+)",
        },
        "premises": {
            "span": r"\t\bpremise\b\s+(\b\d+\b)\s+(\b\d+\b)",
            "text": r"\t\bpremise\b\s+\b\d+\b\s+\b\d+\b\t(.+)",
        },
    }

    essays = {}
    print("Reading annotations...")
    filepaths = []

    for folder, subfolder, files in os.walk(data_folder):
        for file in files:
            if file.startswith(prefix) and file.endswith(ext):

                filepath = os.path.join(folder, file)
                data_dic = {}
                with open(filepath, mode="r", encoding="utf8", newline="\n") as f:
                    data = f.read()

                    for tag in regex_dict:
                        data_dic[tag] = []
                        spans = re.findall(regex_dict[tag]["span"], data, re.I)
                        texts = re.findall(regex_dict[tag]["text"], data, re.I)
                        assert len(spans) == len(texts)
                        for i in range(len(spans)):
                            dic = {"span": list(map(int, spans[i])), "text": texts[i]}
                            data_dic[tag].append(dic)

                name, _ = os.path.splitext(file)
                if name not in essays:
                    essays[name] = data_dic

    return essays


def read_bias(filepath, header_rows=1):
    """Reads the bias data for each essay"""

    assert os.path.exists(filepath), f"File does not exist: {filepath}"
    assert os.path.isfile(filepath), f"Not a valid file: {filepath}"

    essays = {}
    print("Reading bias...")

    with open(filepath) as f:

        for row in itertools.islice(f, header_rows, None):
            key, value = row.split("\t")
            essays[key] = {
                "confirmation_bias": "positive" in value.lower()
            }

    return essays


def read_sufficiency(filepath, header_rows=1, encoding="latin1"):
    """Reads the sufficiency data for each paragraph"""

    assert os.path.exists(filepath), f"File does not exist: {filepath}"
    assert os.path.isfile(filepath), f"Not a valid file: {filepath}"

    essays = {}
    print("Reading sufficiency...")

    with open(filepath, mode="r", encoding=encoding) as f:

        for row in itertools.islice(f, header_rows, None):
            essay, _, text, ann = row.split("\t")
            essay = "essay" + essay.zfill(3)  # zero fill
            value = [{"text": text, "sufficient": not "insufficient" in ann.lower()}]
            if essay not in essays:
                essays[essay] = {"paragraphs": value}
            else:
                essays[essay]["paragraphs"].extend(value)

    return essays


def top_n_specific(argument, mj_cntr, claims_cntr, premises_cntr, n=10):
    """Generates top-n words from a word counter specific to the argument only"""

    assert isinstance(mj_cntr, dict), f"Param 'mj_cntr' not a dict"
    assert isinstance(claims_cntr, dict), f"Param 'claims_cntr' not a dict"
    assert isinstance(premises_cntr, dict), f"Param 'premises_cntr' not a dict"
    assert isinstance(argument, str), f"Param 'argument' not a str"

    # Python only has minimum heap so -ve sign added to invert.
    # This means word with top freq. will be at the top of heap

    # 0
    mj_heap = [(-val, key) for key, val in mj_cntr.items()]
    heapq.heapify(mj_heap)

    # 1
    c_heap = [(-val, key) for key, val in claims_cntr.items()]
    heapq.heapify(c_heap)

    # 2
    p_heap = [(-val, key) for key, val in premises_cntr.items()]
    heapq.heapify(p_heap)

    # heap tree is the most performant way to get top-k elements
    heaps = [mj_heap, c_heap, p_heap]
    sets = [set() for _ in range(3)]

    # Step 1: Add words with top-10 frequency to their respective sets
    for i in range(n):
        sets[0].add(heapq.heappop(mj_heap)[1])
        sets[1].add(heapq.heappop(c_heap)[1])
        sets[2].add(heapq.heappop(p_heap)[1])

    are_eq = len(sets[0]) == len(sets[1]) == len(sets[2]) == n
    assert are_eq, "All sets are not equal lengths"

    # Step 2: Set one argument to focus
    if argument.lower() == "major_claim":
        focus, other1, other2 = 0, 1, 2
    elif argument.lower() == "claims":
        focus, other1, other2 = 1, 0, 2
    elif argument.lower() == "premises":
        focus, other1, other2 = 2, 1, 0
    else:
        raise ValueError(f"'argument' not known {argument}")

    # Step 3: Keep removing words from all sets common b/w focus set and others sets
    while True:

        # get intersection of focus and other sets' words
        intersec1 = sets[other1].intersection(sets[focus])
        intersec2 = sets[other2].intersection(sets[focus])

        # when no intersection, return set as all words in focus are unique
        if len(intersec1) == 0 and len(intersec2) == 0:
            return sets[focus]

        # remove elements from focus that are common to other lists
        sets[focus] -= intersec1
        sets[focus] -= intersec2

        # remove common elements from other lists too
        ### this step is needed to ensure when this func is later called
        ### for the "other1/2" as "focus", the final lists have no overlap
        sets[other1] -= intersec1
        sets[other2] -= intersec2

        # keep pulling elements from heap to fill in the set in desc freq.
        while len(sets[focus]) < n:
            _, new_element = heapq.heappop(heaps[focus])
            sets[focus].add(new_element)

        while len(sets[other1]) < n:
            _, new_element = heapq.heappop(heaps[other1])
            sets[other1].add(new_element)

        while len(sets[other2]) < n:
            _, new_element = heapq.heappop(heaps[other2])
            sets[other2].add(new_element)
