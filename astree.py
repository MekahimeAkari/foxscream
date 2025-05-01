from dataclasses import dataclass
from enum import Enum, auto

@dataclass
class SymbolTable:
    names: 'dict'
    parent: 'SymbolTable'

@dataclass
class ASTNode:
    environment: 'SymbolTable'
    def eval(self):
        raise Exception("eval() for {} not yet implemented".format(type(self).__name__))

@dataclass
class ExprList(ASTNode):
    exprs: 'list'
    def eval(self):
        last_ret = None
        for expression in self.expressions:
            last_ret = expression.eval()
        return last_ret

@dataclass
class Expr(ASTNode):
    pass

@dataclass
class Name(ASTNode):
    name: str

@dataclass
class Literal(ASTNode):
    pass

@dataclass
class StringLiteral(Literal):
    value: str

@dataclass
class IntLiteral(Literal):
    value: int

@dataclass
class FloatLiteral(Literal):
    value: float

@dataclass
class Call(Expr):
    pass

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

class AssignOp(Enum):
    NORMAL = auto()

@dataclass
class AssignExpr(Expr):
    target: Primary
    operator: AssignOp
    expr: Expr

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

class UnOp(Enum):
    NEG = auto()
    POS = auto()
    INV = auto()
    NOT = auto()

@dataclass
class UnExpr(Expr):
    operator: UnOp
    rhs: Expr

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
