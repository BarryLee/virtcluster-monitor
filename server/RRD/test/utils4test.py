import os.path
import unittest
import pprint

current_dir = lambda f: os.path.dirname(os.path.abspath(f))

parent_dir = lambda f: os.path.dirname(current_dir(f))

pp = pprint.PrettyPrinter(indent=2)

def myprint(msg):
    pp.pprint(msg)

import sys
sys.path.append(parent_dir(__file__))

if __name__ == '__main__':
    myprint(parent_dir(__file__))
    #import PerfDataReciever
