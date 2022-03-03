import argparse
from datetime import datetime
import json
import os
import logging
from ctparse.ctparse import logger
from datetime import datetime

logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

from ctparse import ctparse

def test():
  ref = datetime(2022, 3, 3, 13,30)
  parsed = ctparse("I did it for one and a half hour.", ts=ref, latent_time=True, debug=False)
  print(parsed.resolution)
  assert True


test()