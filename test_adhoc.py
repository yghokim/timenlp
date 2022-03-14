import argparse
from datetime import datetime
import json
import os
import logging
from timenlp.timenlp import logger
from datetime import datetime

from timenlp.types import Interval

logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

from timenlp import timenlp

def test():
  ref = datetime(2022, 3, 7, 22, 34)
  phrase = "I had 3 cups of coffee this morning at 8:00 am to 10:30."
  parsed = timenlp(phrase, ts=ref, latent_time=True)
  print("ref:", ref, "phrase:", phrase)
  print(parsed)
  if parsed is not None:
    print(parsed.resolution)
    if isinstance(parsed.resolution, Interval):
      print("start time: ", parsed.resolution.t_from.mstart, parsed.resolution.t_from.mend)
      print("end time: ", parsed.resolution.t_to.mstart, parsed.resolution.t_to.mend)
      

    print(parsed.resolution.mstart, parsed.resolution.mend)
    
  assert True


test()