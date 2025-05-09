#!/usr/bin/env python3

import sys
import copy
try:
    import readline
except ModuleNotFoundError:
    pass
from parser import Parser
from dataclasses import dataclass, field
from astree import SymbolTable, ASTNode, InterpObj

class InterpreterQuitException(Exception):
    pass

def interpreter_quit():
    raise InterpreterQuitException()

class Scope:
    symbol_table: dict = field(default_factory=dict)
    parent: None = None
    label: None = None
    function_scope: bool = False
    loop_scope: bool = False

    def new(self, label=None, function_scope=False, loop_scope=False):
        return Scope(label=label, function_scope=function_scope, loop_scope=loop_scope)

    def find(self, name, exception=True):
        if name in self.symbol_table:
            return self.symbol_table[name]
        else:
            if self.parent is not None:
                return self.parent.find(name)
            if exception:
                raise Exception("Cannot find name {}".format(name))
            else:
                return None

    def set(self, name, value):
        self.symbol_table[name] = value
        return self.symbol_table[name]

    def assign(self, name, value, only_if_found=False):
        if name in self.symbol_table:
            self.symbol_table[name] = value
            return value
        elif self.parent is not None:
            value = self.parent.assign(name, value, True)
            if value is None:
                self.symbol_table[name] = value
        else:
            if only_if_found is True:
                return None
            else:
                self.symbol_table[name] = value

class InterpObj2:
    name: str
    value: None = None
    symbol_table: dict = field(default_factory=dict)
    instance_symbol_table: dict = field(default_factory=dict)
    objclass: None = None
    parents: list = field(default_factory=list)
    func: None = None

    def __post_init__(self):
        parents_symbol_table = {}
        parents_instance_symbol_table = {}
        for parent in self.parents:
            for name, value in parent.symbol_table.items():
                parents_symbol_table[name] = value
            for name, value in parent.instance_symbol_table.items():
                parents_instance_symbol_table[name] = value
        for name, value in parents_symbol_table.items():
            if name not in self.symbol_table:
                self.symbol_table[name] = copy.copy(value)
        for name, value in parents_instance_symbol_table.items():
            if name not in self.instance_symbol_table:
                self.instance_symbol_table[name] = copy.copy(value)

class Interpreter:
    def __init__(self):
        pass

    def parse(self, source):
        return Parser(source).parse()

    def get_prelude(self):
        symbol_table = SymbolTable()
        symbol_table.symbols["print"] = InterpObj("print", func=print)
        return symbol_table

    def eval(self, ast, symbol_table=None):
        if symbol_table is None:
            symbol_table = self.get_prelude()
        return ast.eval(symbol_table)

    def run(self, source, symbol_table=None):
        return self.eval(self.parse(source), symbol_table=symbol_table)

if __name__ == "__main__":
    interp = Interpreter()
    source_text = ""
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as source_file:
            source_text = source_file.read()
        print(interp.parse(source_text).lprint())
        interp.run(source_text)
    else:
        interp_face = "<^.^>"
        print("Welcome to foxscream! This language is silly")
        print("Type 'quit' or 'exit' to leave")
        symbol_table = interp.get_prelude()
        symbol_table.symbols["quit"] = InterpObj("quit", func=interpreter_quit)
        symbol_table.symbols["exit"] = InterpObj("exit", func=interpreter_quit)
        while True:
            try:
                s = input("{} >>> ".format(interp_face))
                if s == "exit" or s == "quit":
                    print()
                    break
                try:
                    interp.run(s, symbol_table=symbol_table)
                    interp_face = "<^.^>"
                except InterpreterQuitException:
                    break
                except Exception as e:
                    print(repr(e))
                    interp_face = "<^-^;>"
            except EOFError:
                print()
                break
