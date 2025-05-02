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
        for expression in self.expressions:
            last_ret = expression.eval()
        return last_ret
    def lprint(self):
        return "{}".format([x.lprint() for x in self.exprs])

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

@dataclass
class Literal(Primary):
    pass

@dataclass
class StringLiteral(Literal):
    value: str
    def lprint(self):
        return '"{}"'.format(self.value)

@dataclass
class IntLiteral(Literal):
    value: int
    def lprint(self):
        return str(self.value)

@dataclass
class FloatLiteral(Literal):
    value: float
    def lprint(self):
        return str(self.value)

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

class AssignOp(Enum):
    NORMAL = auto()

@dataclass
class AssignExpr(Expr):
    target: Primary
    operator: AssignOp
    expr: Expr
    def lprint(self):
        return "({} {} {})".format(self.operator, self.target.lprint(), self.expr.lprint())

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

@dataclass
class SingleKWExpr(Expr):
    target: Expr | None
    expr: Expr | None

@dataclass
class ReturnExpr(SingleKWExpr):
    pass

@dataclass
class BreakExpr(SingleKWExpr):
    pass

@dataclass
class ContinueExpr(SingleKWExpr):
    pass

@dataclass
class LeaveExpr(SingleKWExpr):
    pass

@dataclass
class IfExpr(Expr):
    ifguard: Expr
    ifexpr: Expr
    elifexprs: None
    elseexpr: None

@dataclass
class ElifExpr(Expr):
    guard: Expr
    expr: Expr

@dataclass
class ElseExpr(Expr):
    expr: Expr

@dataclass
class FnDecl(Expr):
    name: Name
    args: None
    expr: Expr
