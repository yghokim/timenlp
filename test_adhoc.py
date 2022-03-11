import argparse
from datetime import datetime
import json
import os
import logging
from timenlp.timenlp import logger
from datetime import datetime

logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

from timenlp import timenlp

def test():
  ref = datetime(2022, 3, 7, 22, 34)
  phrase = "I logged a meal of nachos on November 1, 2017. I assessed that nachos are a very healthy meal."
  parsed = timenlp(phrase, ts=ref, latent_time=True)
  print("ref:", ref, "phrase:", phrase)
  print(parsed)
  print(parsed.production)
  print(parsed.resolution.mstart, parsed.resolution.mend)
  
  assert True


test()