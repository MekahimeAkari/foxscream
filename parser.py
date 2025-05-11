#!/usr/bin/env python3

import sys
from dataclasses import dataclass
from enum import Enum, auto
from lex import Lexer, TokenType
import pprint
from astree import SymbolTable, ExprList, Expr, Name, Primary
from astree import Literal, StringLiteral, IntLiteral, FloatLiteral, BoolLiteral, NullLiteral, ArrayLiteral, DictLiteral
from astree import Call, Slice, Field, Accessor, AssignOp, AssignExpr
from astree import BinOp, BinExpr, UnOp, UnExpr
from astree import ReturnExpr, BreakExpr, LeaveExpr, ContinueExpr, DeferExpr, YieldExpr
from astree import IfExpr, ElifExpr, ElseExpr, Block, FnDecl, WhileExpr, DoWhileExpr, ForExpr
from astree import ClassType, ClassDecl, MatchExpr, CaseExpr

class Parser:
    def __init__(self, source):
        self.lexer = Lexer(source)

    def parse(self):
        self.lexer.lex()
        return self.file()

    def getop(self, opdict):
        optok = self.lexer.next_token().ttype
        if optok not in opdict.keys():
            raise Exception("Expected operator from {}".format(opdict.keys()))
        return opdict[optok]

    def file(self):
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
        if self.lexer.peek(peek_distance).ttype in ttypes:
            self.lexer.next_token(peek_distance)
            return True
        while self.lexer.peek(peek_distance).ttype in [TokenType.NEWLINE, TokenType.SEMICOLON]:
            peek_distance += 1
        if self.lexer.peek(peek_distance).ttype in ttypes:
            self.lexer.next_token(peek_distance)
            return True
        return False

    def match_peek(self, *ttypes):
        peek_distance = 0
        for ttype in ttypes:
            if self.lexer.peek(peek_distance).ttype != ttype:
                while self.lexer.peek(peek_distance).ttype in [TokenType.NEWLINE, TokenType.SEMICOLON]:
                    peek_distance += 1
                if self.lexer.peek(peek_distance).ttype != ttype:
                    return False
            peek_distance += 1
        return True

    def assignop(self):
        if self.lexer.peek().is_assign():
            assignop = self.lexer.next_token()
            if assignop.ttype == TokenType.EQUAL:
                return AssignOp.NORMAL
        else:
            return None

    def assignexpr(self):
        backtrack = False
        if self.lexer.peek().is_primary():
            self.lexer.mark_backtrack()
            primary = self.primary()
            if primary:
                if self.match(TokenType.EQUAL):
                    assignop = self.getop({TokenType.EQUAL: AssignOp.NORMAL})
                    expr = self.req_expr()
                    return AssignExpr(primary, assignop, expr)
                else:
                    backtrack = True
            else:
                backtrack = True
        if backtrack:
            self.lexer.backtrack()
        return self.nonassignexpr()

    def nonassignexpr(self):
        if self.match(TokenType.RETURN, TokenType.BREAK, TokenType.LEAVE, TokenType.CONTINUE, TokenType.DEFER, TokenType.YIELD):
            return self.singlekwexpr()
        elif self.match(TokenType.IF):
            return self.ifexpr()
        elif self.match(TokenType.WHILE):
            return self.whileexpr()
        elif self.match(TokenType.DO):
            return self.dowhileexpr()
        elif self.match(TokenType.FOR):
            return self.forexpr()
        elif self.match(TokenType.MATCH):
            return self.matchexpr()
        elif self.match(TokenType.FN):
            return self.fndecl()
        elif self.match(TokenType.CLASS, TokenType.STATIC, TokenType.TRAIT):
            return self.classdecl()
        elif self.match(TokenType.OPEN_BRACE):
            return self.block()
        elif self.match_peek(TokenType.NAME, TokenType.COLON, TokenType.OPEN_BRACE):
            return self.labeled_block()
        elif self.match(TokenType.NAME, TokenType.INT, TokenType.FLOAT, TokenType.STRING, TokenType.TRUE, TokenType.FALSE, TokenType.NULL, TokenType.OPEN_SQUARE):
            return self.arith()
        else:
            raise Exception("Unexpected token {}".format(self.lexer.peek()))

    def singlekwexpr(self):
        singlekw_const = {
            TokenType.RETURN: ReturnExpr,
            TokenType.BREAK: BreakExpr,
            TokenType.CONTINUE: ContinueExpr,
            TokenType.LEAVE: LeaveExpr,
            TokenType.DEFER: DeferExpr,
            TokenType.YIELD: YieldExpr
        }
        singlekw = singlekw_const[self.lexer.next_token().ttype]
        target = None
        expr = None
        if not self.lexer.peek().is_end() and not self.match(TokenType.TO):
            expr = self.req_expr()
        if self.match(TokenType.TO):
            self.lexer.next_token()
            if not self.match(TokenType.NAME):
                raise Exception("Expected name")
            target = self.nameexpr()
        return singlekw(target, expr)

    def whileexpr(self):
        self.lexer.next_token()
        guard = self.arith()
        expr = self.req_expr()
        return WhileExpr(guard, expr)

    def dowhileexpr(self):
        self.lexer.next_token()
        expr = self.req_expr()
        if not self.match(TokenType.WHILE):
            raise Exception("Expected while")
        self.lexer.next_token()
        guard = self.arith()
        return DoWhileExpr(guard, expr)

    def forexpr(self):
        self.lexer.next_token()
        if not self.match(TokenType.NAME):
            raise Exception("Expected name")
        iter_name = self.nameexpr()
        if not self.match(TokenType.IN):
            raise Exception("Expected in")
        self.lexer.next_token()
        iter_expr = self.req_expr()
        expr = self.req_expr()
        return ForExpr(iter_name, iter_expr, expr)

    def matchexpr(self):
        self.lexer.next_token()
        expr = self.req_expr()
        if not self.match(TokenType.COLON):
            raise Exception("Expected :")
        self.lexer.next_token()
        if not self.match(TokenType.OPEN_BRACE):
            raise Exception("Expected {")
        self.lexer.next_token()
        cases = []
        while not self.match(TokenType.CLOSE_BRACE):
            case_guard = None
            default = False
            if self.match(TokenType.UNDERSCORE):
                default = True
                self.lexer.next_token()
            else:
                case_guard = self.arith()
            if not self.match(TokenType.COLON):
                raise Exception("Expected :")
            self.lexer.next_token()
            case_expr = self.req_expr()
            cases.append(CaseExpr(case_guard, case_expr, default))
        self.lexer.next_token()
        return MatchExpr(expr, cases)

    def ifexpr(self):
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

    def elifexpr(self):
        guard = self.arith()
        expr = self.req_expr()
        return ElifExpr(guard, expr)

    def elseexpr(self):
        expr = self.req_expr()
        return ElseExpr(expr)

    def fndecl(self):
        self.lexer.next_token()
        name = None
        if self.match(TokenType.NAME):
            name = self.nameexpr()
        if not self.match(TokenType.OPEN_PAREN):
            raise Exception("Expected (")
        self.lexer.next_token()
        args = []
        while not self.match(TokenType.CLOSE_PAREN):
            args.append(self.req_expr())
            if self.match(TokenType.CLOSE_PAREN):
                break
            elif not self.match(TokenType.COMMA):
                raise Exception("Expected , or )")
            self.lexer.next_token()
        self.lexer.next_token()
        fnexpr = self.req_expr()
        return FnDecl(name, args, fnexpr)

    def classdecl(self):
        classtype = None
        if self.match(TokenType.CLASS):
            classtype = ClassType.CLASS
        elif self.match(TokenType.STATIC):
            classtype = ClassType.STATIC
        elif self.match(TokenType.TRAIT):
            classtype = ClassType.TRAIT
        else:
            raise Exception("Expected one of class, static, trait")
        self.lexer.next_token()
        name = None
        if self.match(TokenType.NAME):
            name = self.nameexpr()
        parents = None
        if self.match(TokenType.OF):
            parents = []
            self.lexer.next_token()
            parents.append(self.nameexpr())
            while self.match(TokenType.COMMA):
                self.lexer.next_token()
                if not self.match(TokenType.NAME):
                    raise Exception("Expected name")
                parents.append(self.nameexpr())
        expr = None
        if not self.match(TokenType.SEMICOLON):
            expr = self.req_expr()
        else:
            self.lexer.next_token()
        return ClassDecl(classtype, name, parents, expr)

    def labeled_block(self):
        if not self.match(TokenType.NAME):
            raise Exception("Expected name")
        name = self.nameexpr()
        if not self.match(TokenType.COLON):
            raise Exception("Expected :")
        self.lexer.next_token()
        if not self.match(TokenType.OPEN_BRACE):
            raise Exception("Expected {")
        block = self.block()
        block.label = name
        return block

    def block(self):
        exprs = []
        self.lexer.next_token()
        while not self.match(TokenType.CLOSE_BRACE):
            exprs.append(self.expr())
        self.lexer.next_token()
        return Block(None, ExprList(exprs))

    def arith(self):
        return self.orexpr()

    def orexpr(self):
        lhs = self.andexpr()
        while self.match(TokenType.OR):
            op = self.getop({TokenType.OR: BinOp.OR})
            rhs = self.andexpr()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def andexpr(self):
        lhs = self.notexpr()
        while self.match(TokenType.AND):
            op = self.getop({TokenType.AND: BinOp.AND})
            rhs = self.notexpr()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def notexpr(self):
        if self.lexer.match(TokenType.NOT):
            op = self.getop({TokenType.NOT: UnOp.NOT})
            expr = self.notexpr()
            return UnExpr(op, expr)
        else:
            return self.compexpr()

    def compexpr(self):
        lhs = self.bitor()
        compops = {TokenType.GE: BinOp.GE, TokenType.LE: BinOp.LE,
                   TokenType.GT: BinOp.GT, TokenType.LT: BinOp.LT,
                   TokenType.EQUALEQUAL: BinOp.EQ, TokenType.BANGEQUAL: BinOp.NE}
        while self.match(*compops.keys()):
            op = self.getop(compops)
            rhs = self.bitor()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def bitor(self):
        lhs = self.bitxor()
        while self.match(TokenType.PIPE):
            op = self.getop({TokenType.PIPE: BinOp.BITOR})
            rhs = self.bitxor()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def bitxor(self):
        lhs = self.bitand()
        while self.lexer.peek().ttype == TokenType.CARET:
            op = self.getop({TokenType.CARET, BinOp.BITXOR})
            rhs = self.bitand()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def bitand(self):
        lhs = self.shiftexpr()
        while self.match(TokenType.AMP):
            op = self.getop({TokenType.AMP, BinOp.BITAND})
            rhs = self.shiftexpr()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def shiftexpr(self):
        lhs = self.sumexpr()
        while self.match(TokenType.LSHIFT, TokenType.RSHIFT):
            op = self.getop({TokenType.LSHIFT: BinOp.LSHIFT, TokenType.RSHIFT: BinOp.RSHIFT})
            rhs = self.sumexpr()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def sumexpr(self):
        lhs = self.termexpr()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.getop({TokenType.PLUS: BinOp.ADD, TokenType.MINUS: BinOp.SUB})
            rhs = self.termexpr()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def termexpr(self):
        lhs = self.factorexpr()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.SLASHSLASH, TokenType.PERCENT):
            op = self.getop({TokenType.STAR: BinOp.MUL, TokenType.SLASH: BinOp.DIV,
                             TokenType.SLASHSLASH: BinOp.INTDIV,
                             TokenType.PERCENT: BinOp.MOD})
            rhs = self.factorexpr()
            lhs = BinExpr(lhs, op, rhs)
        return lhs

    def factorexpr(self):
        if self.match(TokenType.MINUS, TokenType.PLUS, TokenType.TILDE):
            op = self.getop({TokenType.MINUS: UnOp.NEG, TokenType.PLUS: UnOp.POS,
                             TokenType.TILDE: UnOp.INV})
            return UnExpr(op, self.factorexpr())
        return self.powerexpr()

    def powerexpr(self):
        lhs = self.primary()
        while self.match(TokenType.STARSTAR):
            op = self.getop({TokenType.STARSTAR: BinOp.EXP})
            rhs = self.factorexpr()
            lhs = BinExpr(lhs, op, rhs)
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
        elif self.match(TokenType.TRUE, TokenType.FALSE):
            return self.litbool()
        elif self.match(TokenType.NULL):
            return self.litnull()
        elif self.match(TokenType.OPEN_PAREN):
            return self.parens()
        elif self.match(TokenType.OPEN_SQUARE):
            return self.litarray()
        else:
            raise Exception("Unexpected {}".format(self.lexer.peek()))

    def parens(self):
        self.lexer.next_token()
        expr = self.req_expr()
        print(expr)
        if not self.match(TokenType.CLOSE_PAREN):
            raise Exception("Expected ) not {}".format(self.lexer.peek()))
        self.lexer.next_token()
        return expr

    def nameexpr(self):
        return Name(self.lexer.next_token().lexeme)

    def litint(self):
        return IntLiteral(int(self.lexer.next_token().lexeme, 0))

    def litfloat(self):
        return FloatLiteral(float(self.lexer.next_token().lexeme))

    def litstring(self):
        return StringLiteral(self.lexer.next_token().lexeme)

    def litbool(self):
        return BoolLiteral(self.lexer.next_token().lexeme == "true")

    def litnull(self):
        return NullLiteral(None)

    def litarray(self):
        arrayconst = ArrayLiteral
        is_dict = False
        self.lexer.next_token()
        const_values = []
        if not self.match(TokenType.CLOSE_SQUARE):
            if self.match(TokenType.COLON):
                self.lexer.next_token()
                if not self.match(TokenType.CLOSE_SQUARE):
                    raise Exception("Expected ]")
                arrayconst = DictLiteral
                const_values = {}
            else:
                const_values.append(self.req_expr())
                if self.match(TokenType.COLON):
                    arrayconst = DictLiteral
                    self.lexer.next_token()
                    const_values = {const_values[0]: self.req_expr()}
                while not self.match(TokenType.CLOSE_SQUARE):
                    if self.match(TokenType.COMMA):
                        self.lexer.next_token()
                    key_or_value = self.req_expr()
                    if is_dict:
                        if not self.match(TokenType.COLON):
                            raise Exception("Expected :")
                        self.lexer.next_token()
                        const_values[key_or_value] = self.req_expr()
                    else:
                        const_values.append(key_or_value)
        self.lexer.next_token()
        return arrayconst(const_values)

    def access(self):
        if self.lexer.peek().is_op(TokenType.OPEN_PAREN, TokenType.DOT, TokenType.OPEN_SQUARE):
            if self.match(TokenType.OPEN_PAREN):
                return Accessor(self.fncall(), self.access())
            elif self.match(TokenType.DOT):
                return Accessor(self.fieldaccess(), self.access())
            elif self.match(TokenType.OPEN_SQUARE):
                return Accessor(self.slice(), self.access())
        return None

    def fieldaccess(self):
        self.lexer.next_token()
        if not self.match(TokenType.NAME):
            raise Exception("Expected name")
        return Field(self.nameexpr())

    def slice(self):
        self.lexer.next_token()
        pass

    def fncall(self):
        self.lexer.next_token()
        args = []
        while not self.match(TokenType.CLOSE_PAREN):
            args.append(self.req_expr())
            if self.match(TokenType.CLOSE_PAREN):
                break
            elif not self.match(TokenType.COMMA):
                raise Exception("Expected , or (")
            self.lexer.next_token()
        self.lexer.next_token()
        return Call(args)

if __name__ == "__main__":
    expr_list = []
    source_text = ""
    with open(sys.argv[1]) as source_file:
        source_text = source_file.read()
    parser = Parser(source_text)
    ast = parser.parse()
    print(ast.lprint())
