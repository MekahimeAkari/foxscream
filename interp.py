#!/usr/bin/env python3

import sys
import pprint
from parser import Parser
from astree import SymbolTable, InterpObj
from dataclasses import dataclass, field

class Interpreter:
    def __init__(self, source, symbol_table=None):
        self.ast = Parser(source).parse()
        if symbol_table is None:
            symbol_table = SymbolTable()
            symbol_table.symbols["print"] = InterpObj("print", func=print)
        self.symbol_table = symbol_table

    def eval(self):
        self.ast.eval(self.symbol_table)

if __name__ == "__main__":
    source_text = ""
    with open(sys.argv[1]) as source_file:
        source_text = source_file.read()
    interp = Interpreter(source_text)
    print(interp.ast.lprint())
    interp.eval()
