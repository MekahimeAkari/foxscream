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
    id: int
    name: 'str'
    fsclass: 'FSObject'
    parents: list = field(default_factory=list)
    fields: 'Environment' = None
    instance_fields: 'Environment' = None
    call: 'FSFunc' = None
    operators: dict = field(default_factory=dict)

@dataclass
class Environment:
    symbols: dict = field(default_factory=dict)
    enclosing: 'Environment' = None

    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.enclosing is not None:
            return self.enclosing.get(name)
        else:
            raise Exception("No name " + name)

    def assign(self, name, value):
        if name in self.symbols or self.enclosing is None:
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

class InterpreterQuitException(Exception):
    pass

def interpreter_quit():
    raise InterpreterQuitException()

@dataclass
class Call:
    args: list

    def apply(self, callee, environment):
        return callee(*[x.get(environment) for x in self.args])

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
        res = ast.visit(self)
        print(self.environment)

    def literal(self, literal_ele):
        return Literal(literal_ele.value)

    def name(self, name_ele):
        return Name(name_ele.name)

    def primary(self, primary_ele):
        target = Primary(primary_ele.target.visit(self), None)
        if primary_ele.accessor is not None:
            target.accessors = primary_ele.accessor.visit(self)
        return target

    def accessor(self, accessor_ele):
        access = [accessor_ele.access_type.visit(self)]
        if accessor_ele.next_accessor is not None:
            access.extend(accessor_ele.next_accessor.visit(self))
        return access

    def call(self, call_ele):
        ret_args = []
        for arg_expr in call_ele.args:
            ret_args.append(arg_expr.visit(self))
        return Call(ret_args)

    def exprlist(self, exprlist_ele):
        last_ret = None
        for expr in exprlist_ele.exprs:
            last_expr = expr.visit(self)
            if last_expr is not None:
                last_ret = last_expr.get(self.environment)
        return last_ret

    def assign(self, assign_ele):
        target = assign_ele.target.visit(self)
        operator = assign_ele.operator
        expr = assign_ele.expr.visit(self).get(self.environment)
        self.environment.assign(target.target.name, expr)
        return Literal(expr)

    def binexpr(self, binexpr_ele):
        lhs = binexpr_ele.lhs.visit(self).get(self.environment)
        operator = binexpr_ele.operator
        rhs = None
        rhs_expr = binexpr_ele.rhs
        if operator != BinOp.AND and operator != BinOp.OR:
            rhs = rhs_expr.visit(self).get(self.environment)

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
                rhs = rhs_expr.visit(self).get(self.environment)
                res = lhs and rhs
        elif operator == BinOp.OR:
            res = lhs
            if lhs is False:
                rhs = rhs_expr.visit(self).get(self.environment)
                res = lhs or rhs
        else:
            raise Exception("Unimplemented operator")

        return Literal(res)

    def ifexpr(self, ifexpr_ele):
        if ifexpr_ele.guard.visit(self).get(self.environment) is True:
            return ifexpr_ele.expr.visit(self)
        if ifexpr_ele.elifexprs is not None:
            for elifexpr in ifexpr_ele.elifexprs:
                if elifexpr.guard.visit(self).get(self.environment) is True:
                    return elifexpr.expr.visit(self)
        if ifexpr_ele.elseexpr is not None:
            return ifexpr_ele.elseexpr.visit(self)

    def elifexpr(self, elifexpr_ele):
        return elifexpr_ele.expr.visit(self)

    def elseexpr(self, elseexpr_ele):
        return elseexpr_ele.expr.visit(self)

    def forexpr(self, forexpr_ele):
        raise Exception("unimplemented")

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
