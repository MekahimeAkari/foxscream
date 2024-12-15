#!/usr/bin/env python

import os
import sys
from lark import Lark, Token, Tree
from lark.visitors import Interpreter

class Value:
    def __init__(self, val):
        self.value = val
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return str(self.value)

class Name:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return str(self.name)

class ArgList:
    def __init__(self):
        self.args = []
    def add(self, val):
        if isinstance(val, ArgList):
            self.args.extend(val.args)
        else:
            self.args.append(val)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "({})".format(", ".join([str(x) for x in self.args]))

class Scope:
    def __init__(self):
        self.variables = [{"true": True, "false": False, "null": None, "print": print}]
        self.scope = 0

    def assign(self, name, value):
        scope = self.scope
        while scope >= 0:
            if name in self.variables[scope]:
                self.variables[scope][name] = value
                return self.variables[scope][name]
            scope -= 1
        self.variables[self.scope][name] = value
        return self.variables[self.scope][name]

    def get_value(self, name):
        scope = self.scope
        while scope >= 0:
            if name in self.variables[scope]:
                return self.variables[scope][name]
            scope -= 1
        raise Exception("No variable {}".format(name))

    def push_scope(self):
        self.variables.append({})
        self.scope += 1

    def pop_scope(self):
        self.variables.pop()
        self.scope -= 1

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        ret_str = ""
        for scope in range(0, self.scope+1):
            ret_str += " {}: {}".format(scope, self.variables[scope])
        return ret_str

class FoxScreamInterp(Interpreter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scope = Scope()
        self.reserved = ["true", "false", "null"]

    def visit_or_value(self, tree):
        if isinstance(tree, Tree):
            return self.visit(tree)
        elif isinstance(tree, Token):
            return self.get_value(tree.value)
        elif isinstance(tree, Value) or isinstance(tree, Name):
            return tree

    def get_value(self, value):
        if isinstance(value, Name):
            return self.scope.get_value(value.name)
        elif isinstance(value, Value):
            return value.value
        else:
            return value

    def parens(self, tree):
        if len(tree.children) == 1:
            return self.visit_or_value(tree.children[0])
        else:
            return self.visit_or_value(tree.children[1])

    def number(self, tree):
        num_type = tree.children[0].type
        num_val = tree.children[0].value
        if num_type == "INT":
            return Value(int(num_val))
        elif num_type == "FLOAT":
            return Value(float(num_val))
        elif num_type == "HEX":
            return Value(int(num_val, 16))
        elif num_type == "BIN":
            return Value(int(num_val, 2))
        elif num_type == "OCT":
            return Value(int(num_val, 8))

    def literal(self, tree):
        return self.visit(tree.children[0])

    def atom(self, tree):
        if isinstance(tree.children[0], Tree):
            return self.visit(tree.children[0])
        elif isinstance(tree.children[0], Token):
            return Name(tree.children[0].value)
        else:
            return tree

    def morearguments(self, tree):
        ret_args = ArgList()
        ret_args.add(self.visit(tree.children[1]))
        if len(tree.children) > 2:
            ret_args.add(self.visit(tree.children[2]))
        return ret_args

    def arguments(self, tree):
        ret_args = ArgList()
        ret_args.add(self.visit(tree.children[0]))
        if len(tree.children) > 1:
            ret_args.add(self.visit(tree.children[1]))
        return ret_args

    def call(self, tree):
        ret_args = ArgList()
        if len(tree.children) > 2:
            ret_args.add(self.visit(tree.children[1]))
        return ret_args

    def primary(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            accessed_ele = self.get_value(self.visit(tree.children[0]))
            if tree.children[1].data == "call":
                call_args = self.visit(tree.children[1])
                return accessed_ele(*[self.get_value(x) for x in call_args.args])
            raise Exception("wat")

    def logicnot(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            op = self.get_value(tree.children[0])
            lhs = self.visit_or_value(tree.children[1])
            lhs_value = self.get_value(lhs)
            if op == "!" or op == "not":
                return not lhs_value

    def unop(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            op = self.get_value(tree.children[0])
            lhs = self.visit_or_value(tree.children[1])
            lhs_value = self.get_value(lhs)
            if op == "+":
                return +lhs_value
            elif op == "-":
                return -lhs_value
            elif op == "~":
                return ~lhs_value

    def shift(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == ">>":
                return rhs_value >> lhs_value
            elif op == "<<":
                return rhs_value << lhs_value

    def exponent(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "**":
                return rhs_value ** lhs_value

    def bitxor(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "^":
                return rhs_value ^ lhs_value

    def bitand(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "&":
                return rhs_value & lhs_value

    def bitor(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "|":
                return rhs_value | lhs_value

    def relation(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "<=":
                return rhs_value <= lhs_value
            elif op == ">=":
                return rhs_value >= lhs_value
            elif op == ">":
                return rhs_value > lhs_value
            elif op == "<":
                return rhs_value < lhs_value
            elif op == "==":
                return rhs_value == lhs_value
            elif op == "!=":
                return rhs_value != lhs_value

    def logicand(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "&&" or op == "and":
                return rhs_value and lhs_value

    def logicor(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "||" or op == "or":
                return rhs_value or lhs_value

    def sum(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = self.get_value(tree.children[1])
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "+":
                return rhs_value + lhs_value
            elif op == "-":
                return rhs_value - lhs_value

    def product(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            rhs = self.visit_or_value(tree.children[0])
            rhs_value = self.get_value(rhs)
            op = tree.children[1]
            lhs = self.visit_or_value(tree.children[2])
            lhs_value = self.get_value(lhs)
            if op == "*":
                return rhs_value * lhs_value
            elif op == "/":
                return rhs_value / lhs_value
            elif op == "//":
                return rhs_value // lhs_value
            elif op == "%":
                return rhs_value % lhs_value

    def assign(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            lhs = self.visit(tree.children[0])
            if not isinstance(lhs, Name):
                raise Exception("{} is not a Name".format(lhs))
            if lhs.name in self.reserved:
                raise Exception("Cannot assign to {}".format(lhs))
            #lhs_value = self.scope.get(lhs.name, None)
            op = self.get_value(tree.children[1])
            rhs = self.visit(tree.children[2])
            rhs_value = self.get_value(rhs)
            return self.scope.assign(lhs.name, rhs_value)

    def block(self, tree):
        self.scope.push_scope()
        res = self.visit(tree.children[1])
        self.scope.pop_scope()
        return res

    def ifstmt(self, tree):
        if self.visit(tree.children[1]):
            self.scope.push_scope()
            res = self.visit(tree.children[2])
            self.scope.pop_scope()
            return res
        if len(tree.children) > 3:
            return self.visit(tree.children[3])

    def elifstmt(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        if self.visit(tree.children[1]):
            self.scope.push_scope()
            res = self.visit(tree.children[2])
            self.scope.pop_scope()
            return res
        if len(tree.children) > 2:
            return self.visit(tree.children[3])

    def elsestmt(self, tree):
        self.scope.push_scope()
        res = self.visit(tree.children[1])
        self.scope.pop_scope()
        return res

    def whilestmt(self, tree):
        self.scope.push_scope()
        cond = self.visit(tree.children[1])
        res = None
        while cond:
            res = self.visit(tree.children[2])
            cond = self.visit(tree.children[1])
        self.scope.pop_scope()
        return res

    def start(self, tree):
        self.visit_children(tree)
        print(self.scope)

    def statements(self, tree):
        self.visit_children(tree)

    def __default__(self, tree):
        raise Exception("No {}, tree: {}".format(tree.data, tree))

parser = Lark.open('foxscream.lark', rel_to=__file__)
prog_text = ""
with open(sys.argv[1]) as prog_file:
    prog_text = prog_file.read()
parse = parser.parse(prog_text)
print(parse.pretty())

FoxScreamInterp().visit(parse)
