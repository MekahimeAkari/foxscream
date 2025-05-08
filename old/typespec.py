#!/usr/bin/env python

import sys
from lark import Lark, Token, Tree
from lark.visitors import Interpreter

class TypeSpecInterp(Interpreter):
    def __init__(self, parser):
        self.parser = parser

    def parse(self, string, print_parse=True, run_parse=True):
        parse_res = self.parser.parse(string)
        if print_parse:
            print(parse_res.pretty())
        prog_res = self.visit(parse_res)

parser = Lark.open('typespec.lark', rel_to=__file__)
prog_text = """
a[.a:b]
[a]
[a: b]
fn()-> a or b
a as b
"""
interp = TypeSpecInterp(parser)
if len(sys.argv) > 1:
    with open(sys.argv[1]) as prog_file:
        prog_text = prog_file.read()
interp.parse(prog_text)
