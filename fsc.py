#!/usr/bin/env python

try:
    import readline
except ModuleNotFoundError:
    pass
import sys
import codecs
import copy
import pprint
from lark import Lark, Token, Tree
from lark.visitors import Interpreter
from resolver import Environment
import ast_interp

class Type:
    def __init__(self, name, **kwargs):
        self.name = name
        self.variants = kwargs.get("variants", None)
        self.set_type_sig()

    def set_type_sig(self):
        pass

    def get_attrs(self):
        ret_dict = {}
        ret_dict["name"] = self.name
        return ret_dict

class InterpException(Exception):
    pass

class ObjectType(Type):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)
        self.is_instance = kwargs.get("is_instance", False)
        self.instantiable = kwargs.get("instantiable", True)
        self.ofable = kwargs.get("ofable", True)
        self.hasable = kwargs.get("hasable", True)
        self.modifiable = kwargs.get("modifiable", True)
        self.of_parents = kwargs.get("of_parents", [])
        self.has_parents = kwargs.get("has_parents", [])
        self.class_fields = kwargs.get("class_fields", {})
        self.set_instance_fields(kwargs.get("instance_fields", {}), kwargs.get("instance_call", None))
        self.class_call = kwargs.get("class_call", None)
        self.class_index = kwargs.get("class_index", None)
        self.instance_index = kwargs.get("instance_index", None)
        self.resolve_parents()

    def set_instance_fields(self, instance_fields, instance_call):
        self.instance_fields = {}
        self.instance_call = None
        if self.is_instance:
            for name, field in instance_fields.items():
                self.instance_fields[name] = copy.copy(field)
            if instance_call is not None:
                self.instance_call = copy.copy(instance_call)
        else:
            self.instance_fields = instance_fields
            self.instance_call = instance_call

    def resolve_parents(self):
        pass

    def get_attrs(self):
        ret_dict = {}
        ret_dict["name"] = self.name
        ret_dict["is_instance"] = self.is_instance
        ret_dict["instantiable"] = self.instantiable
        ret_dict["ofable"] = self.ofable
        ret_dict["hasable"] = self.hasable
        ret_dict["modifiable"] = self.modifiable
        ret_dict["of_parents"] = self.of_parents
        ret_dict["has_parents"] = self.has_parents
        ret_dict["class_fields"] = self.class_fields
        ret_dict["instance_fields"] = self.instance_fields
        ret_dict["class_call"] = self.class_call
        ret_dict["instance_call"] = self.instance_call
        ret_dict["class_index"] = self.class_index
        ret_dict["instance_index"] = self.instance_index
        return ret_dict

    def instantiate(self):
        if self.instantiable:
            attrs = self.get_attrs()
            attrs["is_instance"] = True
            attrs["instantiable"] = False
            return ObjectType(**attrs)
        else:
            raise InterpException("Cannot instantiate {}".format(self.name))

    def add_field(self, field, class_field=False):
        if class_field:
            self.class_fields[field.name] = field
        else:
            self.instance_fields[field.name] = field

    def get_field(self, name):
        if self.is_instance:
            ret_field = self.instance_fields[name]
        else:
            ret_field = self.class_fields[name]
        ret_field.class_obj = self
        return ret_field

    def set_field(self, name, value):
        fields = self.get_fields()
        if isinstance(fields[name], ValueField) and not isinstance(value, Type):
            fields[name].value = value
        else:
            fields[name] = value

    def get_fields(self):
        if self.is_instance:
            return self.instance_fields
        else:
            return self.class_fields

    def __call__(self, *args):
        if self.instantiable:
            return self.instantiate()
        elif self.is_instance and self.instance_call is not None:
            call = self.instance_call
        elif not self.is_instance and self.class_call is not None:
            call = self.class_call(*args)
        else:
            raise InterpException("Cannot call object {}".format(self.name))
        call.class_obj = self
        return call(*args)

class TypeField:
    def __init__(self, name, field_type="Any", depends=False, inheritable=True, replaceable=True, overrideable=True, private=False, const=False, init=False, class_obj=None, **kwargs):
        self.name = name
        self.field_type = field_type
        self.inheritable = inheritable
        self.replaceable = replaceable
        self.overrideable = overrideable
        self.private = private
        self.depends = depends
        self.const = const
        self.init = init
        self.class_obj = class_obj

    def get_value_or_field(self):
        return self

class FuncField(TypeField):
    def __init__(self, name, args, body, scope, visit, **kwargs):
        self.args = args
        self.body = body
        self.scope = scope
        self.visit = visit
        super().__init__(name, **kwargs)

    def __call__(self, *args):
        argument_list = {}
        for i in range(0, len(args)):
            argument_list[str(self.args[i])] = args[i]
        self.scope.push_scope(argument_list, class_obj=self.class_obj)
        res = self.visit(self.body)
        self.scope.pop_scope()
        return res

class ValueField(TypeField):
    def __init__(self, name, value, **kwargs):
        super().__init__(name, **kwargs)
        self.value = value

    def get_value_or_field(self):
        return self.value

class InterpClass:
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
        self.class_obj = []

    def print_cur_scope(self, prefix=""):
        print(prefix, "scope", self.scope, self.variables[self.scope], '\n')

    def assign(self, name, value):
        if len(self.class_obj) > 0:
            class_objs = len(self.class_obj)-1
            while class_objs >= 0:
                if name in self.class_obj[class_objs].get_fields():
                    self.class_obj[class_objs].set_field(name, value)
                    return self.class_obj[class_objs].get_field(name)
                class_objs -= 1
        scope = self.scope
        while scope >= 0:
            if name in self.variables[scope].keys():
                self.variables[scope][name] = value
                return self.variables[scope][name]
            scope -= 1
        self.variables[self.scope][name] = value
        return self.variables[self.scope][name]

    def set_variable(self, name, value):
        if len(self.class_obj) > 0:
            self.class_obj[-1].set_field[name] = value
        self.variables[self.scope][name] = value
        return self.variables[self.scope][name]

    def get_value(self, name):
        if len(self.class_obj) > 0:
            class_objs = len(self.class_obj)-1
            while class_objs >= 0:
                if name in self.class_obj[class_objs].get_fields():
                    ret_field = self.class_obj[class_objs].get_field(name)
                    if isinstance(ret_field, ValueField):
                        return ret_field.value
                    else:
                        return ret_field
                class_objs -= 1
        scope = self.scope
        while scope >= 0:
            if name in self.variables[scope]:
                return self.variables[scope][name]
            scope -= 1
        raise InterpException("No variable {}".format(name))

    def push_scope(self, new_scope={}, class_obj=None):
        if self.capture_next_scope is True:
            self.capture_scope = self.scope + 1
            self.capture_next_scope = False
            self.captured_scope = None
        if class_obj is not None:
            self.class_obj.append(class_obj)
        self.variables.append(dict(new_scope))
        self.scope += 1

    def pop_scope(self):
        if self.capture_scope == self.scope:
            self.captured_scope = dict(self.variables[-1])
            self.capture_scope = None
        if len(self.class_obj) > 0:
            self.class_obj.pop()
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

    def __init__(self, parser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scope = Scope()
        self.parser = parser
        self.reserved = ["true", "false", "null"]

    def call_function(self, name, *args):
        func_obj = self.get_value(name)
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
        elif hasattr(value, "value"):
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
        new_type = None
        if num_type == "INT":
            new_type = "int"
            new_value = int(num_val)
        elif num_type == "FLOAT":
            new_type = "float"
            new_value = float(num_val)
        elif num_type == "HEX":
            new_type = "int"
            new_value = int(num_val, 16)
        elif num_type == "BIN":
            new_type = "int"
            new_value = int(num_val, 2)
        elif num_type == "OCT":
            new_type = "int"
            new_value = int(num_val, 8)
        return Value(new_value)

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
                return self.get_value(accessed_ele).get_field(self.get_value(accessor))
            raise InterpException("Unimplemented access {}".format(tree.children[1].data))

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
                raise InterpException("{} is not a Name".format(lhs))
            if lhs.name in self.reserved:
                raise InterpException("Cannot assign to {}".format(lhs))
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
        return self.scope.set_variable(name, FuncField(name, args.args, body, self.scope, self.visit))

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
        new_class = ObjectType(new_class_name)
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
                if isinstance(member_val, TypeField):
                    new_class.add_field(member_val)
                else:
                    new_class.add_field(ValueField(member_name, member_val))
        return self.scope.set_variable(new_class_name, new_class)

    def emptystmt(self, tree):
        return

    def statement(self, tree):
        return self.visit(tree.children[0])

    def start(self, tree):
        res = self.visit_children(tree)
        pprint.pp(self.scope)
        return res

    def statements(self, tree):
        ret = None
        for child in tree.children:
            ret = self.visit(child)
            if child.data == "returnstmt":
                return ret
        return ret

    def __default__(self, tree):
        raise InterpException("Unimplemented grammar rule {}, tree: {}".format(tree.data, tree))

    def parse(self, string, print_parse=True):
        parse_res = self.parser.parse(string)
        if print_parse:
            print(parse_res.pretty())
        return self.visit(parse_res)

class FoxScreamInterpNew(Interpreter):
    def __init__(self, parser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.prog = ast_interp.Program()

    def visit_child(self, tree, num):
        return self.visit(tree.children[num])

    def visit_or_value(self, tree):
        if isinstance(tree, Tree):
            return self.visit(tree)
        elif isinstance(tree, Token):
            return tree.value

    def get_binop(self, op):
        op = op.strip()
        if len(op.split()) > 1:
            op = op.split()
        if op == "+":
            return ast_interp.BinOp.ADD
        elif op == "-":
            return ast_interp.BinOp.SUB
        elif op == "**":
            return ast_interp.BinOp.EXP
        elif op == "*":
            return ast_interp.BinOp.MUL
        elif op == "/":
            return ast_interp.BinOp.DIV
        elif op == "//":
            return ast_interp.BinOp.INTDIV
        elif op == "%":
            return ast_interp.BinOp.MOD
        elif op == "<<":
            return ast_interp.BinOp.LSHIFT
        elif op == ">>":
            return ast_interp.BinOp.RSHIFT
        elif op == "&":
            return ast_interp.BinOp.BITAND
        elif op == "^":
            return ast_interp.BinOp.BITXOR
        elif op == "|":
            return ast_interp.BinOp.BITOR
        elif op == "==":
            return ast_interp.BinOp.EQ
        elif op == "!=":
            return ast_interp.BinOp.NE
        elif op == ">":
            return ast_interp.BinOp.GT
        elif op == "<":
            return ast_interp.BinOp.LT
        elif op == ">=":
            return ast_interp.BinOp.GE
        elif op == "<=":
            return ast_interp.BinOp.LE
        elif op == "in":
            return ast_interp.BinOp.IN
        elif op == "of":
            return ast_interp.BinOp.OF
        elif op == "has":
            return ast_interp.BinOp.HAS
        elif op == "in":
            return ast_interp.BinOp.IN
        elif op == "is":
            return ast_interp.BinOp.IS
        elif op == "and" or op == "&&":
            return ast_interp.BinOp.AND
        elif op == "or" or op == "||":
            return ast_interp.BinOp.OR
        elif (op[0] == "not" or op[0] == "!"):
            if op[1] == "in":
                return ast_interp.BinOp.NOTIN
            elif op[1] == "has":
                return ast_interp.BinOp.NOTHAS
            elif op[1] == "of":
                return ast_interp.BinOp.NOTOF
            elif op[1] == "is":
                return ast_interp.BinOP.NOTIS
        raise InterpException("Unknown binop {}".format(op))

    def get_assignop(self, op):
        op = op.strip()
        if op == "=":
            return ast_interp.AssignOp.NORMAL
        raise InterpException("Unknown assignop {}".format(op))

    def get_unop(self, op):
        op = op.strip()
        if op == "-":
            return ast_interp.UnOp.NEG
        elif op == "+":
            return ast_interp.UnOp.POS
        elif op == "~":
            return ast_interp.UnOp.INV
        elif op == "!" or op == "not":
            return ast_interp.UnOp.NOT
        raise InterpException("Unknown unnop {}".format(op))

    def get_class_type(self, class_type):
        class_type = class_type.strip()
        if class_type == "class":
            return ast_interp.ClassType.CLASS
        elif class_type == "static":
            return ast_interp.ClassType.STATIC
        elif class_type == "trait":
            return ast_interp.ClassType.TRAIT
        raise InterpException("Unknown class type {}".format(class_type))

    def __default__(self, tree):
        raise InterpException("Unimplemented grammar rule {}, tree: {}".format(tree.data, tree))

    def number(self, tree):
        num_type = tree.children[0].type
        num_val = tree.children[0].value
        if num_type == "INT":
            new_value = int(num_val)
        elif num_type == "FLOAT":
            new_value = float(num_val)
        elif num_type == "HEX":
            new_value = int(num_val, 16)
        elif num_type == "BIN":
            new_value = int(num_val, 2)
        elif num_type == "OCT":
            new_value = int(num_val, 8)
        return new_value

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

    def parens(self, tree):
        return self.visit_or_value(tree.children[0])

    def unop(self, tree):
        return ast_interp.UnExpr(operator=self.get_unop(self.visit_or_value(tree.children[0])),
                                 rhs=self.visit(tree.children[1]))

    def binop(self, tree):
        return ast_interp.BinExpr(lhs=self.visit(tree.children[0]),
                                  operator=self.get_binop(self.visit_or_value(tree.children[1])),
                                  rhs=self.visit(tree.children[2]))

    def logicor(self, tree):
        return self.binop(tree)

    def logicand(self, tree):
        return self.binop(tree)

    def logicnot(self, tree):
        return self.unop(tree)

    def relation(self, tree):
        return self.binop(tree)

    def bitor(self, tree):
        return self.binop(tree)

    def bitxor(self, tree):
        return self.binop(tree)

    def bitand(self, tree):
        return self.binop(tree)

    def shift(self, tree):
        return self.binop(tree)

    def sum(self, tree):
        return self.binop(tree)

    def product(self, tree):
        return self.binop(tree)

    def exponent(self, tree):
        return self.binop(tree)

    def atom(self, tree):
        if isinstance(tree.children[0], Tree):
            return ast_interp.Literal(value=self.visit(tree.children[0]))
        else:
            return ast_interp.Name(name=self.visit_or_value(tree.children[0]))

    def classdec(self, tree):
        if len(tree.children) > 3:
            raise InterpException("Do of and has correctly")
        return ast_interp.ClassDeclaration(class_type=self.get_class_type(self.visit_or_value(tree.children[0])),
                                           name=self.visit_or_value(tree.children[1]),
                                           block=self.visit(tree.children[2]))

    def slices(self, tree): #TODO: Actually implement slicing
        return [(self.visit(tree.children[0]))]

    def dotaccess(self, tree):
        return ast_interp.Field(field=self.visit_or_value(tree.children[1]))

    def arrayaccess(self, tree):
        return ast_interp.Slice(slice=self.visit(tree.children[1]))

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
        new_arr = []
        is_dict = True
        if len(tree.children) > 2:
            cur_index = 0
            for key, value in self.visit(tree.children[1]):
                if key is None:
                    key = cur_index
                    cur_index += 1
                new_arr.append((key, value))
        return ast_interp.ArrayDeclaration(is_dict=is_dict, items=new_arr)

    def returnstmt(self, tree):
        ret_expression = None
        if len(tree.children) > 1:
            ret_expression = self.visit_or_value(tree.children[1])
        return ast_interp.ReturnStatement(expression=ret_expression)

    def funcdef(self, tree):
        name = self.visit_or_value(tree.children[1])
        args = []
        block = None
        if len(tree.children) > 5:
            args.extend(self.visit_or_value(tree.children[3]))
            block = self.visit(tree.children[5])
        else:
            block = self.visit(tree.children[4])
        return ast_interp.FunctionDeclaration(name=name, arglist=args, block=block)

    def moreargs(self, tree):
        args = [self.visit_or_value(tree.children[1])]
        if len(tree.children) > 2:
            args.extend(self.visit_or_value(tree.children[2]))
        return args

    def arglist(self, tree):
        args = [self.visit(tree.children[0])]
        if len(tree.children) > 1:
            args.add(self.visit(tree.children[1]))
        return args

    def morearguments(self, tree):
        args = [self.visit(tree.children[1])]
        if len(tree.children) > 2:
            args.extend(self.visit(tree.children[2]))
        return args

    def arguments(self, tree):
        args = [self.visit(tree.children[0])]
        if len(tree.children) > 1:
            args.extend(self.visit(tree.children[1]))
        return args

    def call(self, tree):
        args = []
        if len(tree.children) > 2:
            args.extend(self.visit(tree.children[1]))
        return ast_interp.Call(args=args)

    def subprime(self, tree):
        if len(tree.children) == 1:
            return (self.visit(tree.children[0]), None)
        else:
            target, accessor = self.visit(tree.children[0])
            new_accessor = self.visit(tree.children[1])
            if accessor is None:
                accessor = new_accessor
            else:
                accessor.accessor = new_accessor
            return target, accessor

    def primary(self, tree):
        target, accessor = self.visit(tree.children[0])
        return ast_interp.Primary(target=target, accessor=accessor)

    def whilestmt(self, tree):
        return ast_interp.WhileStatement(condition=self.visit(tree.children[1]), block=self.visit(tree.children[2]))

    def ifstmt(self, tree):
        elifs = None
        else_stmt = None
        if len(tree.children) > 3:
            elifs, else_stmt = self.visit(tree.children[3])
            if len(elifs) == 0:
                elifs = None
        return ast_interp.IfStatement(condition=self.visit(tree.children[1]), block=self.visit(tree.children[2]),
                           elifs=elifs, else_stmt = else_stmt)

    def elifstmt(self, tree):
        elifs = []
        else_stmt = None
        if len(tree.children) == 1:
            return self.visit(tree.children[0])
        elifs.append(ast_interp.ElifStatement(condition=self.visit(tree.children[1]), block=self.visit(tree.children[2])))
        if len(tree.children) == 4:
            more_elifs, else_stmt = self.visit(tree.children[3])
            elifs.extend(more_elifs)
        return (elifs, else_stmt)

    def elsestmt(self, tree):
        return ([], ast_interp.ElseStatement(block=self.visit(tree.children[1])))

    def assign(self, tree):
        return ast_interp.Assignment(target=self.visit(tree.children[0]),
                          operator=self.get_assignop(self.visit_or_value(tree.children[1])),
                          expression=self.visit(tree.children[2]))

    def block(self, tree):
        return ast_interp.Block(statements=self.visit(tree.children[1]))

    def emptystmt(self, tree):
        return None

    def statement(self, tree):
        if len(tree.children) > 1:
            raise InterpException("Handle qualifiers")
        else:
            return ast_interp.Statement(expression=self.visit(tree.children[0]))

    def statements(self, tree):
        stmts = []
        for child in tree.children:
            stmts.append(self.visit(child))
        return stmts

    def start(self, tree):
        self.prog.statements.append(self.visit(tree.children[0]))
        pprint.pp(self.prog)

    def parse(self, string, print_parse=True):
        parse_res = self.parser.parse(string)
        if print_parse:
            print(parse_res.pretty())
        return self.visit(parse_res)

parser = Lark.open('foxscream.lark', rel_to=__file__)
prog_text = ""
interp = FoxScreamInterp(parser)
interp_new = FoxScreamInterpNew(parser)
if len(sys.argv) > 1:
    with open(sys.argv[1]) as prog_file:
        prog_text = prog_file.read()
    interp.parse(prog_text)
    interp_new.parse(prog_text, print_parse=False)
else:
    interp_face = "<^.^>"
    print("Welcome to foxscream! This language is silly")
    print("Type 'quit' or 'exit' to leave")
    while True:
        try:
            s = input("{} >>> ".format(interp_face))
            if s == "exit" or s == "quit":
                print()
                break
            try:
                interp.parse(s + ";")
                interp_face = "<^.^>"
            except (InterpException, AttributeError, IndexError, KeyError, ArithmeticError, TypeError) as e:
                print(repr(e))
                interp_face = "<^-^;>"
        except EOFError:
            print()
            break
