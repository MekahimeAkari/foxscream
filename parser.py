#!/usr/bin/env python3

import sys
from dataclasses import dataclass
from enum import Enum, auto
from lex import Lexer, TokenType
import pprint
from astree import SymbolTable, ExprList, Expr, Name, Primary
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
            pprint.pp(exprs[-1])
        print("")
        return ExprList(exprs)

    def eat_terminators(self):
        while self.lexer.peek().is_op(TokenType.NEWLINE, TokenType.SEMICOLON):
            self.lexer.next_token()

    def expr(self):
        self.eat_terminators()
        expr = self.assignexpr()
        self.eat_terminators()
        return expr

    def req_expr(self):
        expr = self.expr()
        if expr is None:
            raise Exception("Expected expression")
        return expr

    def match(self, *ttypes):
        peek_distance = 0
        while self.lexer.peek(peek_distance).ttype in [TokenType.NEWLINE, TokenType.SEMICOLON]:
            peek_distance += 1
        if self.lexer.peek(peek_distance).ttype in ttypes:
            self.lexer.next_token(peek_distance)
            return True
        return False

    def assignexpr(self):
        backtrack = False
        if self.lexer.peek().is_primary():
            self.lexer.mark_backtrack()
            primary = self.primary()
            if primary:
                if self.match(TokenType.EQUAL):
                    assignop = self.getop({TokenType.EQUAL: AssignOp.NORMAL})
                    expr = self.singlekwexpr()
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
        if self.match(TokenType.IF):
            self.lexer.next_token()
            ifguard = self.arith()
            ifexpr = self.req_expr()
            elifexprs = []
            while self.match(TokenType.ELIF):
                self.lexer.next_token()
                elifexprs.append(self.elifexpr())
            elseexpr = None
            if self.match(TokenType.ELSE):
                self.lexer.next_token()
                elseexpr = self.elseexpr()
            return IfExpr(ifguard, ifexpr, elifexprs, elseexpr)
        else:
            return self.fndec()

    def elifexpr(self):
        guard = self.arith()
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
            self.lexer.next_token()
            return Block(label, ExprList(exprs))
        else:
            return self.arith()

    def arith(self):
        return self.orexpr()

    def orexpr(self):
        lhs = self.andexpr()
        if self.match(TokenType.OR):
            op = self.getop({TokenType.OR: BinOp.OR})
            rhs = self.orexpr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def andexpr(self):
        lhs = self.notexpr()
        if self.match(TokenType.AND):
            op = self.getop({TokenType.AND: BinOp.AND})
            rhs = self.andexpr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def notexpr(self):
        if self.lexer.match(TokenType.NOT):
            op = self.getop({TokenType.NOT: UnOp.NOT})
            expr = self.notexpr()
            return UnExpr(op, expr)
        else:
            return self.compexpr()

    def getop(self, opdict):
        optok = self.lexer.next_token().ttype
        if optok not in opdict.keys():
            raise Exception("Expected operator from {}".format(opdict.keys()))
        return opdict[optok]

    def compexpr(self):
        lhs = self.bitor()
        compops = {TokenType.GE: BinOp.GE, TokenType.LE: BinOp.LE,
                   TokenType.GT: BinOp.GT, TokenType.LT: BinOp.LT,
                   TokenType.EQUALEQUAL: BinOp.EQ, TokenType.BANGEQUAL: BinOp.NE}
        if self.match(*compops.keys()):
            op = self.getop(compops)
            rhs = self.compexpr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def bitor(self):
        lhs = self.bitxor()
        if self.match(TokenType.PIPE):
            op = self.getop({TokenType.PIPE: BinOp.BITOR})
            rhs = self.bitor()
            return BinExpr(lhs, op, rhs)
        return lhs

    def bitxor(self):
        lhs = self.bitand()
        if self.lexer.peek().ttype == TokenType.CARET:
            op = self.getop({TokenType.CARET, BinOp.BITXOR})
            rhs = self.bitxor()
            return BinExpr(lhs, op, rhs)
        return lhs

    def bitand(self):
        lhs = self.shiftexpr()
        if self.match(TokenType.AMP):
            op = self.getop({TokenType.AMP, BinOp.BITAND})
            rhs = self.bitand()
            return BinExpr(lhs, op, rhs)
        return lhs

    def shiftexpr(self):
        lhs = self.sumexpr()
        if self.match(TokenType.LSHIFT, TokenType.RSHIFT):
            op = self.getop({TokenType.LSHIFT: BinOp.LSHIFT, TokenType.RSHIFT: BinOp.RSHIFT})
            rhs = self.shiftexpr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def sumexpr(self):
        lhs = self.termexpr()
        if self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.getop({TokenType.PLUS: BinOp.ADD, TokenType.MINUS: BinOp.SUB})
            rhs = self.sumexpr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def termexpr(self):
        lhs = self.factorexpr()
        if self.match(TokenType.STAR, TokenType.SLASH, TokenType.SLASHSLASH, TokenType.PERCENT):
            op = self.getop({TokenType.STAR: BinOp.MUL, TokenType.SLASH: BinOp.DIV,
                             TokenType.SLASHSLASH: BinOp.INTDIV,
                             TokenType.PERCENT: BinOp.MOD})
            rhs = self.termexpr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def factorexpr(self):
        if self.match(TokenType.MINUS, TokenType.PLUS, TokenType.TILDE):
            op = self.getop({TokenType.MINUS: UnOp.NEG, TokenType.PLUS: UnOp.POS,
                             TokenType.TILDE: UnOp.INV})
            return UnExpr(op, self.powerexpr())
        return self.powerexpr()

    def powerexpr(self):
        lhs = self.primary()
        if self.match(TokenType.STARSTAR):
            op = self.getop({TokenType.STARSTART: BinOp.EXP})
            rhs = self.powerexpr()
            return BinExpr(lhs, op, rhs)
        return lhs

    def primary(self):
        atom = self.atom()
        access = self.access()
        return Primary(atom, access)

    def atom(self):
        if self.match(TokenType.NAME):
            return self.nameexpr()
        elif self.match(TokenType.INT):
            return self.litint()
        elif self.match(TokenType.FLOAT):
            return self.litfloat()
        elif self.match(TokenType.STRING):
            return self.litstring()
        else:
            raise Exception("Unexpected {}".format(self.lexer.peek()))

    def nameexpr(self):
        return Name(self.lexer.next_token().lexeme)

    def litint(self):
        return IntLiteral(int(self.lexer.next_token().lexeme))

    def litfloat(self):
        return FloatLiteral(float(self.lexer.next_token().lexeme))

    def litstring(self):
        return StringLiteral(self.lexer.next_token().lexeme)

    def access(self):
        root_accessor = Accessor(None, None)
        cur_access = root_accessor
        while self.lexer.peek().is_op(TokenType.OPEN_PAREN, TokenType.DOT, TokenType.OPEN_SQUARE):
            if self.match(TokenType.OPEN_PAREN):
                cur_access.access_type = self.fncall()
            elif self.match(TokenType.DOT):
                cur_access.access_type = self.field_access()
            elif self.match(TokenType.OPEN_SQUARE):
                cur_access.access_type = self.slice()
            else:
                break

            cur_access.next_accessor = Accessor(None, None)
            cur_access = cur_access.next_accessor

        return root_accessor

    def fieldaccess(self):
        self.lexer.next_token()
        pass

    def slice(self):
        self.lexer.next_token()
        pass

    def fncall(self):
        self.lexer.next_token()
        pass

if __name__ == "__main__":
    expr_list = []
    source_text = ""
    with open(sys.argv[1]) as source_file:
        source_text = source_file.read()
    parser = Parser(source_text)
    pprint.pp(parser.parse())
