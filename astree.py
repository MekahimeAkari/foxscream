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
        return "({})".format("\n, ".join([x.lprint() for x in self.exprs]))

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

    def lprint(self):
        return str(self.value)

    def eval(self, symbol_table=None):
        return self.value

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
class BoolLiteral(Literal):
    value: bool

@dataclass
class NullLiteral(Literal):
    value: None

@dataclass
class Call(Expr):
    args: 'list'

    def lprint(self):
        return "({})".format(",".join([x.lprint() for x in self.args]))

@dataclass
class Slice(Expr):
    pass

@dataclass
class Field(Expr):
    name: Name

    def lprint(self):
        return ".{}".format(self.name.lprint())

@dataclass
class Block(Expr):
    label: str
    exprs: ExprList
    def lprint(self):
        return "{}{{{}}}".format("" if self.label is None else "{}:".format(self.label), self.exprs.lprint())

@dataclass
class Accessor(Expr):
    access_type: Call | Slice | Field
    next_accessor: 'Accessor'

    def lprint(self):
        return "{}{}".format(self.access_type.lprint(), "" if self.next_accessor is None else self.next_accessor.lprint())

@dataclass
class Primary(Expr):
    target: Name | Literal
    accessor: 'Accessor'

    def lprint(self):
        return "{}{}".format(self.target.lprint(), "" if self.accessor is None else self.accessor.lprint())

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
        return "({} {}{})".format("return", self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

@dataclass
class BreakExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("break", self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

@dataclass
class ContinueExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("continue", self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

@dataclass
class LeaveExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("leave", self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

@dataclass
class DeferExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("defer", self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

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

class ClassType(Enum):
    CLASS = auto()
    STATIC = auto()
    TRAIT = auto()

@dataclass
class ClassDecl(Expr):
    class_type: ClassType
    name: Name
    parents: None
    expr: Expr

    def lprint(self):
        class_type_str = None
        if self.class_type == ClassType.CLASS:
            class_type_str = "class"
        elif self.class_type == ClassType.STATIC:
            class_type_str = "static"
        elif self.class_type == ClassType.TRAIT:
            class_type_str = "trait"
        return "({} {}{} {})".format(class_type_str,
            "" if self.name is None else "{}".format(self.name.lprint()),
            "" if self.parents is None else " of {}".format(",".join([x.lprint() for x in self.parents])),
            "" if self.expr is None else self.expr.lprint())

@dataclass
class FnDecl(Expr):
    name: Name
    args: None
    expr: Expr

    def lprint(self):
        return "(fn {} ({}) {})".format("" if self.name is None else "{}".format(self.name.lprint()),
            "" if self.args is None else "{}".format(",".join([x.lprint() for x in self.args])),
            self.expr.lprint())


@dataclass
class ForExpr(Expr):
    iter_name: Name
    iter_expr: Expr
    expr: Expr

    def lprint(self):
        return "(for {} in {} {})".format(self.iter_name.lprint(), self.iter_expr, self.expr.lprint())

@dataclass
class WhileExpr(Expr):
    guard: Expr
    expr: Expr

    def lprint(self):
        return "(while {} {})".format(self.guard.lprint(), self.expr.lprint())

@dataclass
class DoWhileExpr(Expr):
    guard: Expr
    expr: Expr

    def lprint(self):
        return "(do {} while {})".format(self.expr.lprint(), self.guard.lprint())

