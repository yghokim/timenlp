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
  #2020-02-25T12:34
  ref = datetime(2020, 2, 25, 12, 34)
  phrase = "today 3:00 pm for one hour"
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