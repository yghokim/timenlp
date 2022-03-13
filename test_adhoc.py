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
  phrase = "I drank a cup of coffee from 8:00 am to 9:00 pm."
  parsed = timenlp(phrase, ts=ref, latent_time=True)
  print("ref:", ref, "phrase:", phrase)
  print(parsed)
  print(parsed.production)
  print(parsed.resolution.mstart, parsed.resolution.mend)
  
  assert True


test()