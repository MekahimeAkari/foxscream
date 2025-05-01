#!/usr/bin/env python3

import sys
from dataclasses import dataclass
from enum import Enum, auto
from lex import Lexer, TokenType
from astree import SymbolTable, ExprList, Expr, Name
from astree import Literal, StringLiteral, IntLiteral, FloatLiteral
from astree import Call, Slice, Field, Accessor, AssignOp, AssignExpr
from astree import BinOp, BinExpr, UnOp, UnExpr
from astree import ReturnExpr, BreakExpr, LeaveExpr, ContinueExpr
from astree import IfExpr, ElifExpr, ElseExpr, Block, FnDecl

class ParseNode:
    pass

class Parser:
    def __init__(self, source):
        self.lexer = Lexer(source)

    def parse(self):
        self.lexer.lex()
        return self.file()

    def file(self):
        label = None
        exprs = []
        while self.lexer.peek().ttype != TokenType.EOF:
            exprs.append(self.expr())
            if not self.lexer.peek().is_end():
                raise Exception("Expected end of expression, not " + str(self.lexer.peek()))
            self.lexer.next_token()
        return ExprList(self.exprs)

    def expr(self):
        return self.assignexpr()

    def req_expr(self):
        expr = self.expr()
        if expr is None:
            raise Exception("Expected expression")

    def assignexpr(self):
        backtrack = False
        if self.lexer.peek().is_primary():
            self.lexer.mark_backtrack()
            primary = self.primary()
            if primary:
                assignop = self.assignop()
                if assignop:
                    expr = self.req_expr()
                    return AssignExpr(primary, assignop, expr)
                else:
                    backtrack = True
            else:
                backtrack = True
        if backtrack:
            self.lexer.backtrack()
        return self.singlekwexpr()

    def assignop(self):
        if self.lexer.peek().is_assign():
            assignop = self.lexer.next_token()
            if assignop.ttype == TokenType.EQUAL:
                return AssignOp.NORMAL
        else:
            return None

    def singlekwexpr(self):
        if self.lexer.peek().is_singlekw():
            singlekw = self.lexer.next_token()
            singlekwexpr = None
            target = None
            if not self.lexer.peek().is_end():
                singlekwexpr = self.expr()
            if singlekw.ttype == TokenType.RETURN:
                return ReturnExpr(target, singlekwexpr)
            elif singlekw.ttype == TokenType.BREAK:
                return BreakExpr(target, singlekwexpr)
            elif singlekw.ttype == TokenType.CONTINUE:
                return ContinueExpr(target, singlekwexpr)
            elif singlekw.ttype == TokenType.LEAVE:
                return LeaveExpr(target, singlekwexpr)
            else:
                raise Exception("Unknown single keyword expression")
        else:
            return self.ifexpr()

    def ifexpr(self):
        if self.lexer.peek().ttype == TokenType.IF:
            self.lexer.next_token()
            ifguard = self.req_expr()
            ifexpr = self.req_expr()
            elifexprs = []
            while self.lexer.peek().ttype == TokenType.ELIF:
                self.lexer.next_token()
                elifexprs.append(self.elifexpr())
            elseexpr = None
            if self.lexer.peek().ttype == TokenType.ELSE:
                self.lexer.next_token()
                elseexpr = self.elseexpr()
            return IfExpr(ifguard, ifexpr, elifexprs, elseexpr)
        else:
            return self.fndec()

    def elifexpr(self):
        guard = self.req_expr()
        expr = self.req_expr()
        return ElifExpr(guard, expr)

    def elseexpr(self):
        expr = self.req_expr()
        return ElseExpr(expr)

    def fndec(self):
        if self.lexer.peek().ttype == TokenType.FN:
            self.lexer.next_token()
            name = None
            if self.lexer.peek().ttype == TokenType.NAME:
                name = self.name()
            if self.lexer.next_token() != TokenType.OPEN_PAREN:
                raise Exception("Expected (")
            args = []
            next_token = self.lexer.next_token()
            while next_token != TokenType.CLOSE_PAREN:
                args.append(self.fndeclarg())
                next_token = self.lexer.next_token()
                if next_token == TokenType.CLOSE_PAREN:
                    break
                elif next_token != TokenType.COMMA:
                    raise Exception("Expected , or )")
            fnexpr = self.req_expr()
            return FnDecl(name, args, fnexpr)
        else:
            return self.block()

    def block(self):
        if self.lexer.peek().ttype == TokenType.OPEN_BRACE:
            label = None
            exprs = []
            self.lexer.next_token()
            while self.lexer.peek().ttype != TokenType.CLOSE_BRACE:
                exprs.append(self.expr())
                if not self.lexer.next_token().is_end():
                    raise Exception("Expected end of expression")
            self.lexer.next_token()
            return Block(label, ExprList(exprs))
        else:
            return self.arith()

    def arith(self):
        return self.orexpr()

    def orexpr(self):
        lhs = self.andexpr()
        if self.lexer.peek().ttype == TokenType.OR:
            op = self.orop()
            rhs = self.req_expr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def andexpr(self):
        lhs = self.notexpr()
        if self.lexer.peek().ttype == TokenType.AND:
            op = self.andop()
            rhs = self.req_expr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def notexpr(self):
        if self.lexer.peek().ttype == TokenType.NOT:
            op = self.notop()
            expr = self.req_expr()
            return UnOp(op, expr)
        else:
            return self.compexpr()

    def orop(self):
        optok = self.lexer.next_token()
        if optok.ttype == TokenType.OR:
            return BinOp.OR
        else:
            raise Exception("Expected OR operator")

    def andop(self):
        optok = self.lexer.next_token()
        if optok.ttype == TokenType.AND:
            return BinOp.AND
        else:
            raise Exception("Expected AND operator")

    def notop(self):
        optok = self.lexer.next_token()
        if optok.ttype == TokenType.NOT:
            return BinOp.NOT
        else:
            raise Exception("Expected NOT operator")

    def compexpr(self):
        lhs = self.bitor()
        if self.lexer.peek().is_compop():
            op = self.compop()
            rhs = self.req_expr()
            return BinExpr(lhs, op, rhs)

    def compop(self):
        optok = self.lexer.next_token()
        if optok.ttype == TokenType.GE:
            return BinOp.GE
        elif optok.ttype == TokenType.LE:
            return BinOp.LE
        elif optok.ttype == TokenType.GT:
            return BinOp.GT
        elif optok.ttype == TokenType.LT:
            return BinOp.LT
        else:
            raise Exception("Expected comparison operator")

    def bitor(self):
        pass

    def bitxor(self):
        pass

    def bitand(self):
        pass

    def shiftexpr(self):
        pass

    def sum(self):
        pass

    def term(self):
        pass

    def factor(self):
        pass


    def power(self):
        pass


    def primary(self):
        pass


    def fieldaccess(self):
        pass


    def slice(self):
        pass


    def fncall(self):
        pass

if __name__ == "__main__":
    expr_list = []
    source_text = ""
    with open(sys.argv[1]) as source_file:
        source_text = source_file.read()
    parser = Parser(source_text)
    expr_list = parser.parse()
    print("\n".join([str(x) for x in expr_list]))
