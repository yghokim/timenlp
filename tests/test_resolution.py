from tokenize import Triple
import pytest
import yaml
from os import path, getcwd
from typing import List
from datetime import datetime
import timenlp
from timenlp.corpus import parse_nb_string

class CaseSet():
    ref: str
    phrases: List[str]
    parsed: str

    def __init__(self, dict):
        self.ref = datetime.strptime(dict["ref"], "%Y-%m-%dT%H:%M") 
        self.phrases = dict["phrases"]
        self.parsed = dict["parsed"]

with open(path.join(getcwd(), "datasets/corpus_resolution.yml")) as corpus_file:
        corpus: List[CaseSet] = [CaseSet(d) for d in yaml.load(corpus_file, Loader=yaml.FullLoader)]

assert corpus is not None

corpus_flatten = []
for case in corpus:
    for phrase in case.phrases:
        corpus_flatten.append((phrase, case.ref, case.parsed))

@pytest.mark.parametrize("flatten_case", corpus_flatten)
def test_corpus(flatten_case: Triple) -> None:
    phrase = flatten_case[0]
    ref = flatten_case[1]
    parsed = flatten_case[2]

    result = timenlp.timenlp(phrase, ts=ref, latent_time=True, debug=False)
    assert result is not None, f"Failed to parse \"{phrase}\""
    assert result.resolution.nb_str() == parsed, f"{phrase} -> {result.resolution.nb_str()}. Expected {parsed}"