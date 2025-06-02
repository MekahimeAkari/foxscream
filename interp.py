#!/usr/bin/env python3

import sys
import copy
try:
    import readline
except ModuleNotFoundError:
    pass
from parser import Parser
from dataclasses import dataclass, field
from astree import SymbolTable, ASTNode, InterpObj, BinOp

@dataclass
class FSFunc:
    args: 'Environment'
    closure: 'Environment'
    body: ASTNode

@dataclass
class FSConstructor(FSFunc):
    ret_class: 'FSObject'

@dataclass
class FSObject:
    name: 'str'
    fsclass: 'FSObject' = None
    parents: list = field(default_factory=list)
    fields: 'Environment' = field(default_factory=dict)
    instance_fields: 'Environment' = field(default_factory=dict)
    call: 'FSFunc' = None
    operators: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.fsclass is None:
            self.fsclass = self

    def __str__(self):
        return "{}".format(self.name) + ": {}".format(self.fields["value"]) if "value" in self.fields.keys() else ""

    def __repr__(self):
        return self.__str__()

@dataclass
class Environment:
    symbols: dict = field(default_factory=dict)
    enclosing: 'Environment' = None
    lit_num: int = 0
    label: None = None
    func_scope: bool = False
    loop_scope: bool = False
    break_called: bool = False
    defer_exprs: list = field(default_factory=list)

    def get(self, name, can_fail=False):
        if name in self.symbols:
            return self.symbols[name]
        elif self.enclosing is not None:
            return self.enclosing.get(name)
        elif not can_fail:
            raise Exception("No name " + name)
        else:
            return None

    def assign(self, name, value, immediate=False):
        if name in self.symbols or self.enclosing is None or immediate:
            self.symbols[name] = value
        elif self.enclosing is not None and not self.enclosing.assign_if(name, value):
            self.symbols[name] = value
        return value

    def assign_if(self, name, value):
        success = False
        if name in self.symbols:
            self.symbols[name] = value
            success = True
        elif self.enclosing is not None:
            success = self.enclosing.assign_if(name, value)
        return success

    def get_lit_num(self):
        if self.enclosing:
            return self.enclosing.get_lit_num()
        ret_num = self.lit_num
        self.lit_num += 1
        return ret_num

    def descend(self, label=None):
        return Environment(enclosing=self, label=label)

    def ascend(self):
        return self.enclosing

    def do_break(self, label=None):
        self.break_called = True
        if label is not None:
            if self.label != label and self.enclosing is not None:
                self.enclosing.do_break(label=label)
            else:
                raise Exception("No labeled block " + label)
        elif self.enclosing is not None and self.loop_scope is False:
            self.enclosing.do_break(label=label)

    def do_leave(self, label=None):
        self.break_called = True
        if label is not None:
            if self.label != label and self.enclosing is not None:
                self.enclosing.do_leave(label=label)
            else:
                raise Exception("No labeled block " + label)

    def do_return(self):
        self.break_called = True
        if self.enclosing is not None and self.func_scope is False:
            self.enclosing.do_return()

    def add_defer(self, expr):
        self.defer_exprs.insert(0, expr)

class InterpreterQuitException(Exception):
    pass

def interpreter_quit():
    raise InterpreterQuitException()

@dataclass
class Call:
    args: list
    next: None = None

    def apply(self, callee):
        ret = callee(*self.args)
        if self.next is not None:
            ret = next.apply(ret)
        return ret

@dataclass
class Field:
    field: str

@dataclass
class Slice:
    slices: list

@dataclass
class Name:
    name: str

    def get(self, environment):
        return environment.get(self.name)

@dataclass
class Literal:
    value: None

    def get(self, environment):
        return self.value

@dataclass
class Primary:
    target: None
    accessors: None

    def get(self, environment):
        ret = self.target.get(environment)
        if self.accessors:
            for accessor in self.accessors:
                ret = accessor.apply(ret, environment)
        return ret

class Interpreter:
    def __init__(self):
        pass

    def parse(self, source):
        return Parser(source).parse()

    def get_prelude(self):
        symbol_table = SymbolTable()
        symbol_table.symbols["print"] = InterpObj("print", func=print)
        symbol_table.symbols["null"] = InterpObj("null")
        symbol_table.symbols["true"] = InterpObj("true")
        symbol_table.symbols["false"] = InterpObj("false")
        return symbol_table

    def eval(self, ast, symbol_table=None):
        if symbol_table is None:
            symbol_table = self.get_prelude()
        return ast.eval(symbol_table)

    def run(self, source, symbol_table=None):
        return self.eval(self.parse(source), symbol_table=symbol_table)

    def interpret(self, ast):
        self.environment = Environment()
        self.environment.assign("print", print)
        self.environment.assign("object", FSObject("object"))
        self.environment.assign("null", FSObject("null"))
        self.environment.assign("class", FSObject("class", parents=[self.environment.get("object")]))
        self.environment.assign("number", FSObject("number", parents=[self.environment.get("object")], fsclass=self.environment.get("class")))
        self.environment.assign("int", FSObject("int", parents=[self.environment.get("number")], fsclass=self.environment.get("class")))
        self.environment.assign("float", FSObject("float", parents=[self.environment.get("number")], fsclass=self.environment.get("class")))
        self.environment.assign("bool", FSObject("bool", parents=[self.environment.get("object")], fsclass=self.environment.get("class")))
        self.environment.assign("true", FSObject("true", parents=[self.environment.get("bool")], fsclass=self.environment.get("class")))
        self.environment.assign("false", FSObject("false", parents=[self.environment.get("bool")], fsclass=self.environment.get("class")))
        self.environment.assign("collection", FSObject("collection", parents=[self.environment.get("object")], fsclass=self.environment.get("class")))
        self.environment.assign("dict", FSObject("dict", parents=[self.environment.get("collection")], fsclass=self.environment.get("class")))
        self.environment.assign("array", FSObject("array", parents=[self.environment.get("collection")], fsclass=self.environment.get("class")))
        self.environment.assign("str", FSObject("str", parents=[self.environment.get("collection")], fsclass=self.environment.get("class")))
        res = ast.visit(self)
        print(self.environment)

    def literal_literal(self, literal_val, literal_type):
        return FSObject("{}_lit_{}".format(literal_type, self.environment.get_lit_num()),
                        fsclass=self.environment.get(literal_type),
                        fields={"value": literal_val})

    def literal(self, literal_ele, literal_type):
        return self.literal_literal(literal_ele.value, literal_type)

    def stringlit(self, string_ele):
        return self.literal(string_ele, "str")

    def intlit(self, int_ele):
        return self.literal(int_ele, "int")

    def floatlit(self, float_ele):
        return self.literal(float_ele, "float")

    def arraylit(self, array_ele):
        return self.literal_literal([x.visit(self) for x in array_ele.value], "array")

    def dictlit(self, dict_ele):
        return self.literal_literal({k:v.visit(self) for k, v in dict_ele.value.items()}, "dict")

    def boollit(self, bool_ele):
        if bool_ele.value is True:
            return self.environment.get("true")
        else:
            return self.environment.get("false")

    def nulllit(self, null_ele):
        return self.environment.get("null")

    def name(self, name_ele):
        return self.environment.get(name_ele.name)

    def primary(self, primary_ele, assign=None):
        if primary_ele.accessor is None and assign is not None:
            target = self.environment.assign(primary_ele.target.name, assign)
        target = primary_ele.target.visit(self)
        if primary_ele.accessor is not None:
            target = primary_ele.accessor.visit(self).apply(target)
        return target

    def accessor(self, accessor_ele):
        access = accessor_ele.access_type.visit(self)
        if accessor_ele.next_accessor is not None:
            access.next = accessor_ele.next_accessor.visit(self)
        return access

    def call(self, call_ele):
        ret_args = []
        for arg_expr in call_ele.args:
            ret_args.append(arg_expr.visit(self))
        return Call(ret_args)

    def exprlist(self, exprlist_ele):
        last_ret = None
        for expr in exprlist_ele.exprs:
            last_ret = expr.visit(self)
        return last_ret

    def assign(self, assign_ele):
        expr = assign_ele.expr.visit(self)
        operator = assign_ele.operator
        return assign_ele.target.visit(self, assign=expr)

    def binexpr(self, binexpr_ele):
        lhs = binexpr_ele.lhs.visit(self).fields["value"]
        operator = binexpr_ele.operator
        rhs = None
        rhs_expr = binexpr_ele.rhs
        if operator != BinOp.AND and operator != BinOp.OR:
            rhs = rhs_expr.visit(self).fields["value"]

        if operator == BinOp.ADD:
            res = lhs + rhs
        elif operator == BinOp.SUB:
            res = lhs - rhs
        elif operator == BinOp.EXP:
            res = lhs ** rhs
        elif operator == BinOp.MUL:
            res = lhs * rhs
        elif operator == BinOp.DIV:
            res = lhs / rhs
        elif operator == BinOp.INTDIV:
            res = lhs // rhs
        elif operator == BinOp.MOD:
            res = lhs % rhs
        elif operator == BinOp.LSHIFT:
            res = lhs << rhs
        elif operator == BinOp.RSHIFT:
            res = lhs >> rhs
        elif operator == BinOp.BITAND:
            res = lhs & rhs
        elif operator == BinOp.BITXOR:
            res = lhs ^ rhs
        elif operator == BinOp.BITOR:
            res = lhs | rhs
        elif operator == BinOp.EQ:
            res = lhs == rhs
        elif operator == BinOp.NE:
            res = lhs != rhs
        elif operator == BinOp.GT:
            res = lhs > rhs
        elif operator == BinOp.LT:
            res = lhs < rhs
        elif operator == BinOp.GE:
            res = lhs >= rhs
        elif operator == BinOp.LE:
            res = lhs <= rhs
        elif operator == BinOp.AND:
            res = lhs
            if lhs is True:
                rhs = rhs_expr.visit(self).fields["value"]
                res = lhs and rhs
        elif operator == BinOp.OR:
            res = lhs
            if lhs is False:
                rhs = rhs_expr.visit(self).fields["value"]
                res = lhs or rhs
        else:
            raise Exception("Unimplemented operator")

        if res is True:
            res = self.environment.get("true")
        elif res is False:
            res = self.environment.get("false")
        elif isinstance(res, float):
            res = self.literal_literal(res, "float")
        elif isinstance(res, int):
            res = self.literal_literal(res, "int")

        return res

    def ifexpr(self, ifexpr_ele):
        if ifexpr_ele.guard.visit(self) is self.environment.get("true"):
            return ifexpr_ele.expr.visit(self)
        if ifexpr_ele.elexpr is not None:
            return ifexpr_ele.elexpr.visit(self)

    def elseexpr(self, elseexpr_ele):
        return elseexpr_ele.expr.visit(self)

    def forexpr(self, forexpr_ele):
        iter_pos = 0
        iter_arr = forexpr_ele.iter_expr.visit(self).fields["value"]
        iter_name = forexpr_ele.iter_name.name
        last_expr = self.environment.get("null")
        loop_ran = False
        while iter_pos < len(iter_arr):
            loop_ran = True
            iter_val = iter_arr[iter_pos]
            self.environment.assign(iter_name, iter_val, immediate=True)
            last_expr = forexpr_ele.expr.visit(self)
            iter_pos += 1
        if not loop_ran and forexpr_ele.elexpr is not None:
            return forexpr_ele.elexpr.visit(self)
        return last_expr

    def whileexpr(self, whileexpr_ele):
        last_expr = self.environment.get("null")
        loop_ran = False
        while whileexpr_ele.guard.visit(self) is self.environment.get("true"):
            loop_ran = True
            last_expr = whileexpr_ele.expr.visit(self)
        if not loop_ran and whileexpr_ele.elexpr is not None:
            return whileexpr_ele.elexpr.visit(self)
        return last_expr

    def dowhileexpr(self, dowhileexpr_ele):
        last_expr = dowhileexpr_ele.expr.visit(self)
        while dowhileexpr_ele.guard.visit(self) is self.environment.get("true"):
            last_expr = dowhileexpr_ele.expr.visit(self)
        return last_expr

    def block(self, block_ele):
        self.environment = self.environment.descend()
        ret_expr = block_ele.exprs.visit(self)
        if len(self.environment.defer_exprs) > 0:
            for defer_expr in self.environment.defer_exprs:
                ret_expr = defer_expr.visit(self)
        self.environment = self.environment.ascend()
        return ret_expr

    def deferexpr(self, defer_ele):
        self.environment.add_defer(defer_ele.expr)

if __name__ == "__main__":
    interp = Interpreter()
    source_text = ""
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as source_file:
            source_text = source_file.read()
        print(interp.parse(source_text).lprint())
        interp.interpret(interp.parse(source_text))
        #interp.run(source_text)
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
