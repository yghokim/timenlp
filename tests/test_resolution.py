import pytest
import yaml
from os import path, getcwd
from typing import List
from datetime import datetime
import timenlp


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

@pytest.mark.parametrize("case", corpus)
def test_corpus(case: CaseSet) -> None:
    for phrase in case.phrases:
        result = timenlp.timenlp(phrase, ts=case.ref, latent_time=True, debug=False)
        assert result is not None, f"Failed to parse \"{phrase}\""
        assert result.resolution.nb_str() == case.parsed, f"Ref ({case.ref}) {phrase} -> {result.resolution.nb_str()}. Expected {case.parsed}"