from dataclasses import dataclass, field
from enum import Enum, auto

@dataclass
class SymbolTable:
    symbols: dict = field(default_factory=dict)
    parent: 'SymbolTable' = None

    def new(self):
        return SymbolTable(parent=self)

    def find(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.find(name)
        return None

    def bind(self, name, obj):
        exist_obj = self.find(name)
        if exist_obj:
            exist_obj.assign(obj)
        else:
            self.symbols[name] = obj

@dataclass
class ASTNode:
    def eval(self, symbol_table):
        raise Exception("eval() for {} not yet implemented".format(type(self).__name__))
    def lprint(self):
        raise Exception("lprint() for {} not yet implemented".format(type(self).__name__))

@dataclass
class InterpObj:
    name: str
    value: None = None
    fields: dict = field(default_factory=dict)
    func: None = None

    def assign(self, other):
        self.value = other.value

    def call(self, *args):
        if self.func is None:
            raise Exception("Cannot call {}".format(self.name))
        elif isinstance(self.func, ASTNode):
            raise Exception("You need to add function signatures, nerd")
        else:
            return self.func(*args)

    def __str__(self):
        return str(self.value)

@dataclass
class ExprList(ASTNode):
    exprs: 'list'
    def eval(self, symbol_table):
        last_ret = None
        for expression in self.exprs:
            last_ret = expression.eval(symbol_table)
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

    def eval(self, symbol_table):
        return self.name

@dataclass
class Literal(Primary):
    pass

    def lprint(self):
        return str(self.value)

    def eval(self, symbol_table):
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

    def eval(self, symbol_table, parent_obj):
        call_args = [x.eval(symbol_table) for x in self.args]
        return parent_obj.call(*call_args)

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

    def eval(self, symbol_table):
        return self.exprs.eval(symbol_table)

@dataclass
class Accessor(Expr):
    access_type: Call | Slice | Field
    next_accessor: 'Accessor'

    def lprint(self):
        return "{}{}".format(self.access_type.lprint(), "" if self.next_accessor is None else self.next_accessor.lprint())

    def eval(self, symbol_table, parent_obj):
        return self.access_type.eval(symbol_table, parent_obj)

@dataclass
class Primary(Expr):
    target: Name | Literal
    accessor: 'Accessor'

    def lprint(self):
        return "{}{}".format(self.target.lprint(), "" if self.accessor is None else self.accessor.lprint())

    def eval(self, symbol_table, assign=False):
        if isinstance(self.target, Literal):
            if assign:
                raise Exception("Cannot assign to Literal")
            else:
                return InterpObj("literal", value=self.target.eval(symbol_table))
        name = self.target.eval(symbol_table)
        obj = None
        if name not in symbol_table.symbols:
            if assign:
                symbol_table.bind(name, InterpObj(name))
            else:
                raise Exception("No name {} known".format(name))
        obj = symbol_table.find(name) # TODO: handle call/slice
        if self.accessor:
            obj = self.accessor.eval(symbol_table, obj)
        return obj

class AssignOp(Enum):
    NORMAL = auto()

@dataclass
class AssignExpr(Expr):
    target: Primary
    operator: AssignOp
    expr: Expr

    def lprint(self):
        return "({} {} {})".format(self.operator, self.target.lprint(), self.expr.lprint())

    def eval(self, symbol_table):
        obj = self.target.eval(symbol_table, assign=True)
        obj.assign(self.expr.eval(symbol_table))
        print(symbol_table)
        return obj

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

    def eval(self, symbol_table):
        res = None
        if self.operator == BinOp.ADD:
            res = self.lhs.eval(symbol_table).value + self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.SUB:
            res = self.lhs.eval(symbol_table).value - self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.EXP:
            res = self.lhs.eval(symbol_table).value ** self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.MUL:
            res = self.lhs.eval(symbol_table).value * self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.DIV:
            res = self.lhs.eval(symbol_table).value / self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.INTDIV:
            res = self.lhs.eval(symbol_table).value // self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.MOD:
            res = self.lhs.eval(symbol_table).value % self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.LSHIFT:
            res = self.lhs.eval(symbol_table).value << self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.RSHIFT:
            res = self.lhs.eval(symbol_table).value >> self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.BITAND:
            res = self.lhs.eval(symbol_table).value & self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.BITXOR:
            res = self.lhs.eval(symbol_table).value ^ self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.BITOR:
            res = self.lhs.eval(symbol_table).value | self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.EQ:
            res = self.lhs.eval(symbol_table).value == self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.NE:
            res = self.lhs.eval(symbol_table).value != self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.GT:
            res = self.lhs.eval(symbol_table).value > self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.LT:
            res = self.lhs.eval(symbol_table).value < self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.GE:
            res = self.lhs.eval(symbol_table).value >= self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.LE:
            res = self.lhs.eval(symbol_table).value <= self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.AND:
            res = self.lhs.eval(symbol_table).value and self.rhs.eval(symbol_table).value
        elif self.operator == BinOp.OR:
            res = self.lhs.eval(symbol_table).value or self.rhs.eval(symbol_table).value
        else:
            raise Exception("unimplemented")
        return InterpObj("intermediate", value=res)

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
        res = None
        if self.operator == UnOp.NEG:
            res = -self.rhs.eval().value
        elif self.operator == UnOp.POS:
            res = +self.rhs.eval().value
        elif self.operartor == UnOp.INV:
            res = ~self.rhs.eval().value
        elif self.operator == UnOp.NOT:
            res = not self.rhs.eval().value
        else:
            raise Exception("unimplemented")
        return InterpObj("intermediate", value=res)

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
class YieldExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("yield", self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

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

    def eval(self, symbol_table):
        if self.ifguard.eval(symbol_table) is True:
            return self.ifexpr.eval(symbol_table.new())
        if self.elifexprs is not None:
            for elifexpr in self.elifexprs:
                elif_res = elifexpr.eval(symbol_table)
                if elif_res is not None:
                    return elif_res
        if self.elseexpr is not None:
            return self.elseexpr.eval(symbol_table)

@dataclass
class ElifExpr(Expr):
    guard: Expr
    expr: Expr

    def lprint(self):
        return "elif {} {}".format(self.guard.lprint(), self.expr.lprint())

    def eval(self, symbol_table):
        return None if self.guard.eval(symbol_table) is not True else self.expr.eval(symbol_table.new())

@dataclass
class ElseExpr(Expr):
    expr: Expr

    def lprint(self):
        return "else {}".format(self.expr.lprint())

    def eval(self, symbol_table):
        return self.expr.eval(symbol_table.new())

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
class MatchExpr(Expr):
    init_expr: Expr
    cases: 'list'

    def lprint(self):
        return "(match {} {})".format(self.init_expr.lprint(), ", ".join([x.lprint() for x in self.cases]))

@dataclass
class CaseExpr(Expr):
    match: Expr
    expr: Expr
    default: bool = False

    def lprint(self):
        return "case {}:{}".format("default" if self.default else self.match.lprint(), self.expr.lprint())

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

