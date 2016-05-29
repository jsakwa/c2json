"""
trivial example program that pretty prints the fully parsed types extracted
from the json file passed as the first argument to the program
"""
import sys
import parser

with open(sys.argv[1]) as inf:    
    for t in parser.parse(inf): print t