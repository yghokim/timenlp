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
  ref = datetime(2022, 3, 7, 0, 0)
  parsed = timenlp("8:00", ts=ref, latent_time=True)
  print(parsed)
  print(parsed.resolution)
  
  assert True


test()