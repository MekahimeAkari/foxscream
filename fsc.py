#!/usr/bin/env python

import os
import sys
import codecs
from lark import Lark, Token, Tree
from lark.visitors import Interpreter

class ASTNode:
    pass

class Statement(ASTNode):
    pass

class Expression(ASTNode):
    pass

class Type:
    def __init__(self, name, of_parents={}, has_parents={}, fields={}, depends_fields={}, instantiable=True, ofable=True, hasable=True, modifiable=True, variants={}, call=None, slots={}):
        self.name = name
        self.of_parents = of_parents
        self.has_parents = has_parents
        self.fields = fields
        self.depends_fields = depends_fields
        self.instantiable = instantiable
        self.ofable = ofable
        self.hasable = hasable
        self.modifiable = modifiable
        self.variables = variants
        self.call = call
        self.slots = slots
        self.type_sig = self.set_type_sig()
        self.value = None

    def set_type_sig(self):
        self.type_sig = "_".join([self.name] + [str(x) for x in self.depends_fields.get_value()])

    def get_value(self):
        return self.value

class Object:
    def __init__(self, name, obj_class):
        self.obj_class = obj_class
        self.name = name
        self.attributes = {}
        self.slots = {}
        self.call = None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{} of {}: attrs:{}; slots:{}; call:{}".format(self.name, self.obj_class, self.attributes, self.slots, self.call)

class Class:
    def __init__(self, name):
        self.name = name
        self.slots = {}

    def add_slot(self, name, val=None):
        self.slots[name] = val

    def access(self, name):
        return self.slots[name]

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "class {}: {}".format(self.name, self.slots)

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

class Function:
    def __init__(self, args, body):
        self.args = args
        self.body = body

class Scope:
    def __init__(self):
        self.variables = [{"true": True, "false": False, "null": None, "print": print}]
        self.scope = 0
        self.capture_next_scope = False
        self.capture_scope = None
        self.captured_scope = None

    def print_cur_scope(self, prefix=""):
        print(prefix, "scope", self.scope, self.variables[self.scope], '\n')

    def assign(self, name, value):
        scope = self.scope
        while scope >= 0:
            if name in self.variables[scope].keys():
                self.variables[scope][name] = value
                return self.variables[scope][name]
            scope -= 1
        self.variables[self.scope][name] = value
        return self.variables[self.scope][name]

    def set_variable(self, name, value):
        self.variables[self.scope][name] = value
        return self.variables[self.scope][name]

    def get_value(self, name):
        scope = self.scope
        while scope >= 0:
            if name in self.variables[scope]:
                return self.variables[scope][name]
            scope -= 1
        raise Exception("No variable {}".format(name))

    def push_scope(self, new_scope={}, throw=False):
        if self.capture_next_scope is True:
            self.capture_scope = self.scope + 1
            self.capture_next_scope = False
            self.captured_scope = None
        self.variables.append(dict(new_scope))
        self.scope += 1

    def pop_scope(self):
        if self.capture_scope == self.scope:
            self.captured_scope = dict(self.variables[-1])
            self.capture_scope = None
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

    def call_function(self, name, *args):
        func_obj = self.get_value(name)
        if isinstance(func_obj, Function):
            argument_list = {}
            for i in range(0, len(args)):
                argument_list[str(func_obj.args[i])] = args[i]
            self.scope.push_scope(argument_list)
            res = self.visit(func_obj.body)
            self.scope.pop_scope()
            return res
        else:
            return func_obj(*args)

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

    def string(self, tree):
        is_r = False
        is_f = False
        string_val = tree.children[0].value
        while string_val[0] != "'" and string_val[0] != '"':
            if string_val[0].lower() == "r":
                is_r = True
            elif string_val[0].lower() == "f":
                is_f = True
            string_val = string_val[1:]
        if tree.children[0].type == "STRING":
            string_val = string_val[1:-1]
        if tree.children[0].type == "ML_STRING":
            string_val = string_val[3:-3]
        if not is_r:
            string_val = codecs.escape_decode(bytes(string_val, "utf-8"))[0].decode("utf-8")

        return string_val

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

    def slices(self, tree): #TODO: Actually implement slicing
        return self.visit(tree.children[0])

    def arrayaccess(self, tree):
        return self.visit(tree.children[1])

    def dotaccess(self, tree):
        return self.visit_or_value(tree.children[1])

    def primary(self, tree):
        return self.visit(tree.children[0])

    def subprime(self, tree):
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        else:
            accessed_ele = self.visit(tree.children[0])
            if tree.children[1].data == "call":
                call_args = self.visit(tree.children[1])
                return self.call_function(accessed_ele, *[self.get_value(x) for x in call_args.args])
            elif tree.children[1].data == "arrayaccess":
                accessor = self.visit(tree.children[1])
                return self.get_value(accessed_ele)[self.get_value(accessor)]
            elif tree.children[1].data == "dotaccess":
                accessor = self.visit_or_value(tree.children[1])
                return self.get_value(accessed_ele).access(self.get_value(accessor))
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

    def funcdef(self, tree):
        name = self.visit_or_value(tree.children[1])
        args = ArgList()
        body = None
        if len(tree.children) > 5:
            args.add(self.visit_or_value(tree.children[3]))
            body = tree.children[5]
        else:
            body = tree.children[4]
        return self.scope.set_variable(name, Function(args.args, body))

    def moreargs(self, tree):
        ret_args = ArgList()
        ret_args.add(self.visit_or_value(tree.children[1]))
        if len(tree.children) > 2:
            ret_args.add(self.visit_or_value(tree.children[2]))
        return ret_args

    def arglist(self, tree):
        ret_args = ArgList()
        ret_args.add(self.visit(tree.children[0]))
        if len(tree.children) > 1:
            ret_args.add(self.visit(tree.children[1]))
        return ret_args

    def returnstmt(self, tree):
        if len(tree.children) == 1:
            return
        return self.visit_or_value(tree.children[1])

    def arraykeydec(self, tree):
        return self.visit_or_value(tree.children[0])

    def arraydecele(self, tree):
        key = None
        if len(tree.children) > 1:
            key = self.visit_or_value(tree.children[0])
        val = self.visit_or_value(tree.children[-1])
        return (key, val)

    def morearraydec(self, tree):
        ret_decs = [self.visit(tree.children[1])]
        if len(tree.children) > 2:
            ret_decs.extend(self.visit(tree.children[2]))
        return ret_decs

    def arraydeclist(self, tree):
        ret_decs = [self.visit(tree.children[0])]
        if len(tree.children) > 1:
            ret_decs.extend(self.visit(tree.children[1]))
        return ret_decs

    def arraydec(self, tree):
        new_arr = {}
        if len(tree.children) > 2:
            cur_index = 0
            for key, value in self.visit(tree.children[1]):
                if key is None:
                    key = cur_index
                    cur_index += 1
                new_arr[key] = value
        return new_arr

    def get_type(self, item):
        if isinstance(item, Tree):
            return item.data
        elif isinstance(item, Token):
            return item.type
        else:
            return str(type(item))

    def classdec(self, tree):
        new_class_name = self.visit_or_value(tree.children[1])
        new_class = Class(new_class_name)
        next_index = 2
        of_list = None
        has_list = None
        class_body = []
        if self.get_type(tree.children[next_index]) == "oflist":
            of_list = self.visit(tree.children[next_index])
            next_index += 1
        if self.get_type(tree.children[next_index]) == "haslist":
            has_list = self.visit(tree.children[next_index])
            next_index += 1
        if self.get_type(tree.children[next_index]) == "block":
            self.scope.capture_next_scope = True
            self.visit(tree.children[next_index])
            class_defs = self.scope.captured_scope
            for member_name, member_val in class_defs.items():
                new_class.add_slot(member_name, member_val)
        return self.scope.set_variable(new_class_name, new_class)

    def start(self, tree):
        self.visit_children(tree)
        print(self.scope)

    def statements(self, tree):
        ret = None
        for child in tree.children:
            ret = self.visit(child)
            if child.data == "returnstmt":
                return ret
        return ret

    def __default__(self, tree):
        raise Exception("No {}, tree: {}".format(tree.data, tree))

parser = Lark.open('foxscream.lark', rel_to=__file__)
prog_text = ""
with open(sys.argv[1]) as prog_file:
    prog_text = prog_file.read()
parse = parser.parse(prog_text)
print(parse.pretty())

FoxScreamInterp().visit(parse)
