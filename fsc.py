#!/usr/bin/env python

import os
import sys
from lark import Lark

parser = Lark.open('foxscream.lark', rel_to=__file__)
prog_text = ""
with open(sys.argv[1]) as prog_file:
    prog_text = prog_file.read()
print(parser.parse(prog_text).pretty())
