from dataclasses import dataclass
from enum import Enum, auto

@dataclass
class SymbolTable:
    names: 'dict'
    parent: 'SymbolTable'

@dataclass
class ASTNode:
    #environment: 'SymbolTable' | None = None
    def eval(self):
        raise Exception("eval() for {} not yet implemented".format(type(self).__name__))
    def lprint(self):
        raise Exception("lprint() for {} not yet implemented".format(type(self).__name__))

@dataclass
class ExprList(ASTNode):
    exprs: 'list'
    def eval(self):
        last_ret = None
        for expression in self.exprs:
            last_ret = expression.eval()
            print(last_ret)
        return last_ret
    def lprint(self):
        return "{}".format("\n".join([x.lprint() for x in self.exprs]))

@dataclass
class Expr(ASTNode):
    pass

@dataclass
class Primary(Expr):
    pass

@dataclass
class Name(Primary):
    name: str
    def lprint(self):
        return self.name
    def eval(self):
        return self.name

@dataclass
class Literal(Primary):
    pass

@dataclass
class StringLiteral(Literal):
    value: str
    def lprint(self):
        return '"{}"'.format(self.value)

    def eval(self, symbol_table=None):
        return self.value

@dataclass
class IntLiteral(Literal):
    value: int
    def lprint(self):
        return str(self.value)

    def eval(self, symbol_table=None):
        return self.value

@dataclass
class FloatLiteral(Literal):
    value: float
    def lprint(self):
        return str(self.value)

    def eval(self, symbol_table=None):
        return self.value

@dataclass
class Call(Expr):
    args: 'list'

@dataclass
class Slice(Expr):
    pass

@dataclass
class Field(Expr):
    pass

@dataclass
class Block(Expr):
    label: str
    exprs: ExprList
    def lprint(self):
        return "{}".format(self.exprs.lprint())
    def eval(self, symbol_table=None):
        return self.exprs.eval()

@dataclass
class Accessor(Expr):
    access_type: Call | Slice | Field
    next_accessor: 'Accessor'

@dataclass
class Primary(Expr):
    target: Name | Literal
    accessor: 'Accessor'
    def lprint(self):
        return self.target.lprint()
    def eval(self, symbol_table=None):
        return self.target.eval()

class AssignOp(Enum):
    NORMAL = auto()

@dataclass
class AssignExpr(Expr):
    target: Primary
    operator: AssignOp
    expr: Expr
    def lprint(self):
        return "({} {} {})".format(self.operator, self.target.lprint(), self.expr.lprint())
    def eval(self, symbol_table=None):
        if symbol_table is None:
            symbol_table = {}
        symbol_table[self.target.eval()] = self.expr.eval(symbol_table)
        return symbol_table[self.target.eval()]

class BinOp(Enum):
    ADD = auto()
    SUB = auto()
    EXP = auto()
    MUL = auto()
    DIV = auto()
    INTDIV = auto()
    MOD = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    BITAND = auto()
    BITXOR = auto()
    BITOR = auto()
    EQ = auto()
    NE = auto()
    GT = auto()
    LT = auto()
    GE = auto()
    LE = auto()
    IN = auto()
    HAS = auto()
    OF = auto()
    IS = auto()
    NOTIN = auto()
    NOTHAS = auto()
    NOTOF = auto()
    NOTIS = auto()
    AND = auto()
    OR = auto()

@dataclass
class BinExpr(Expr):
    lhs: Expr
    operator: BinOp
    rhs: Expr
    def lprint(self):
        return "({} {} {})".format(self.operator, self.lhs.lprint(), self.rhs.lprint())

    def eval(self, symbol_table=None):
        if self.operator == BinOp.ADD:
            return self.lhs.eval() + self.rhs.eval()
        elif self.operator == BinOp.SUB:
            return self.lhs.eval() - self.rhs.eval()
        elif self.operator == BinOp.EXP:
            return self.lhs.eval() ** self.rhs.eval()
        elif self.operator == BinOp.MUL:
            return self.lhs.eval() * self.rhs.eval()
        elif self.operator == BinOp.DIV:
            return self.lhs.eval() / self.rhs.eval()
        elif self.operator == BinOp.INTDIV:
            return self.lhs.eval() // self.rhs.eval()
        elif self.operator == BinOp.MOD:
            return self.lhs.eval() % self.rhs.eval()
        elif self.operator == BinOp.LSHIFT:
            return self.lhs.eval() << self.rhs.eval()
        elif self.operator == BinOp.RSHIFT:
            return self.lhs.eval() >> self.rhs.eval()
        elif self.operator == BinOp.BITAND:
            return self.lhs.eval() & self.rhs.eval()
        elif self.operator == BinOp.BITXOR:
            return self.lhs.eval() ^ self.rhs.eval()
        elif self.operator == BinOp.BITOR:
            return self.lhs.eval() | self.rhs.eval()
        elif self.operator == BinOp.EQ:
            return self.lhs.eval() == self.rhs.eval()
        elif self.operator == BinOp.NE:
            return self.lhs.eval() != self.rhs.eval()
        elif self.operator == BinOp.GT:
            return self.lhs.eval() > self.rhs.eval()
        elif self.operator == BinOp.LT:
            return self.lhs.eval() < self.rhs.eval()
        elif self.operator == BinOp.GE:
            return self.lhs.eval() >= self.rhs.eval()
        elif self.operator == BinOp.LE:
            return self.lhs.eval() <= self.rhs.eval()
        elif self.operator == BinOp.AND:
            return self.lhs.eval() and self.rhs.eval()
        elif self.operator == BinOp.OR:
            return self.lhs.eval() or self.rhs.eval()
        else:
            raise Exception("unimplemented")

class UnOp(Enum):
    NEG = auto()
    POS = auto()
    INV = auto()
    NOT = auto()

@dataclass
class UnExpr(Expr):
    operator: UnOp
    rhs: Expr

    def lprint(self):
        return "({} {})".format(self.operator, self.rhs.lprint())

    def eval(self, symbol_table=None):
        if self.operator == UnOp.NEG:
            return -self.rhs.eval()
        elif self.operator == UnOp.POS:
            return +self.rhs.eval()
        elif self.operartor == UnOp.INV:
            return ~self.rhs.eval()
        elif self.operator == UnOp.NOT:
            return not self.rhs.eval()

@dataclass
class SingleKWExpr(Expr):
    target: Expr | None
    expr: Expr | None

@dataclass
class ReturnExpr(SingleKWExpr):
    def lprint(self):
        return "({} {})".format("return", self.expr.lprint())

@dataclass
class BreakExpr(SingleKWExpr):
    def lprint(self):
        return "({} {})".format("break", self.expr.lprint())

@dataclass
class ContinueExpr(SingleKWExpr):
    def lprint(self):
        return "({} {})".format("continue", self.expr.lprint())

@dataclass
class LeaveExpr(SingleKWExpr):
    def lprint(self):
        return "({} {})".format("leave", self.expr.lprint())

@dataclass
class IfExpr(Expr):
    ifguard: Expr
    ifexpr: Expr
    elifexprs: None
    elseexpr: None
    def lprint(self):
        elif_lprint = ""
        if self.elifexprs:
            elif_lprint = " " + " ".join([x.lprint() for x in self.elifexprs])
        else_lprint = ""
        if self.elseexpr:
            else_lprint = " " + self.elseexpr.lprint()
        return "(if {} {}{}{})".format(self.ifguard.lprint(), self.ifexpr.lprint(), elif_lprint, else_lprint)

@dataclass
class ElifExpr(Expr):
    guard: Expr
    expr: Expr
    def lprint(self):
        return "elif {} {}".format(self.guard.lprint(), self.expr.lprint())

@dataclass
class ElseExpr(Expr):
    expr: Expr
    def lprint(self):
        return "else {}".format(self.expr.lprint())

@dataclass
class FnDecl(Expr):
    name: Name
    args: None
    expr: Expr
