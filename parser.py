#!/usr/bin/env python3

import sys
from dataclasses import dataclass
from enum import Enum, auto
from .lex import Lexer, TokenType

@dataclass(kw_only=True)
class SymbolTable:
    names: dict = dict()
    parent: 'SymbolTable' | None = None

@dataclass
class ASTNode:
    environment: SymbolTable | None = None
    def eval(self):
        raise Exception("eval() for {} not yet implemented".format(type(self).__name__))

@dataclass
class ExprList(ASTNode):
    expressions: list
    def eval(self):
        last_ret = None
        for expression in self.expressions:
            last_ret = expression.eval()
        return last_ret

@dataclass
class Expr(ASTNode):
    pass

class AssignOp(Enum):
    NORMAL = auto()

@dataclass
class Assignment(Expr):
    name: str
    assign_op: AssignOp
    expr: Expr



class ParseNode:
    pass

class Expression(ParseNode):
    def __init__(self, lexer):
        self.expression = None
        self.parse(lexer)

    def parse(self, lexer):
        token = lexer.next_token()

class File(ParseNode):
    def __init__(self, lexer):
        self.expressions = []
        self.parse(lexer)

    def parse(self, lexer):
        while lexer.peek().ttype != TokenType.EOF:
            self.expressions.append(Expression(lexer))
        return self.expressions

class Parser:
    def __init__(self, lexer):
        self.parse_tree = File(lexer)
