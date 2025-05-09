from dataclasses import dataclass, field
from enum import Enum, auto
import pprint

@dataclass
class SymbolTable:
    symbols: dict = field(default_factory=dict)
    parent: 'SymbolTable' = None
    scope_label: str = None
    return_called: bool = False
    return_val_sent: bool = False
    return_val: None = None
    enclosing_function_scope: bool = False
    enclosing_loop_scope: bool = False
    loop_break_called: bool = False
    class_definition: bool = False

    def new(self, symbols=None, scope_label=None, enclosing_function_scope=False,
            enclosing_loop_scope=False, class_definition=False):
        return SymbolTable(parent=self, symbols={} if symbols is None else symbols,
                           scope_label=scope_label,
                           enclosing_function_scope=enclosing_function_scope,
                           enclosing_loop_scope=enclosing_loop_scope,
                           class_definition=class_definition)

    def find(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.find(name)
        return None

    def bind(self, name, obj):
        if name in self.symbols:
            self.symbols[name] = obj
            return obj
        elif self.parent is not None:
            if self.parent.bind(name, obj) is None:
                self.symbols[name] = obj
        return None

    def scope_return(self, return_val_sent=False, return_val=None):
        self.return_called = True
        self.return_val_sent = return_val_sent
        self.return_val = return_val
        self.loop_break_called = True
        if self.enclosing_function_scope is False and self.parent:
            self.parent.scope_return(return_val_sent, return_val)

    def scope_break(self, loop_label=None):
        self.loop_break_called = True
        if self.enclosing_loop_scope is False and self.parent:
            self.parent.scope_break(loop_label)

@dataclass
class ASTNode:
    def eval(self, symbol_table):
        raise Exception("eval() for {} not yet implemented".format(type(self).__name__))
    def lprint(self):
        raise Exception("lprint() for {} not yet implemented".format(type(self).__name__))

@dataclass
class FuncSig:
    body: ASTNode
    ret_type: None = None
    posargs: list = field(default_factory=list)
    starargs: bool = False

    def eval(self, symbol_table, *args):
        func_symbol_table = symbol_table.new()
        func_symbol_table.enclosing_function_scope = True
        if len(self.posargs) > len(args):
            raise Exception("function requires more arguments")
        elif len(self.posargs) < len(args):
            raise Exception("starargs not done yet")
        for arg in range(len(args)):
            func_symbol_table.symbols[self.posargs[arg]] = args[arg]
        return self.body.eval(func_symbol_table)

@dataclass
class ObjConstructor(FuncSig):

    def eval(self, symbol_table, parents, instance_fields, objclass, *args):
        ret_obj = InterpObj("newobj", parents=parents, fields=instance_fields, objclass=objclass)
        func_symbol_table = symbol_table.new()
        func_symbol_table.enclosing_function_scope = True
        for fieldname, fieldobj in ret_obj.fields.items():
            func_symbol_table.symbols[fieldname] = fieldobj
        if len(self.posargs) > len(args):
            raise Exception("function requires more arguments")
        elif len(self.posargs) < len(args):
            raise Exception("starargs not done yet")
        for arg in range(len(args)):
            func_symbol_table.symbols[self.posargs[arg]] = args[arg]
        self.body.eval(func_symbol_table)
        return ret_obj

@dataclass
class InterpObj:
    name: str
    value: None = None
    fields: dict = field(default_factory=dict)
    objclass: None = None
    instance_fields: dict = field(default_factory=dict)
    parents: list = field(default_factory=list)
    func: None = None

    def __post_init__(self):
        for parent in self.parents:
            for fieldname, fieldobj in parent.fields.items():
                if fieldname not in self.fields:
                    self.fields[fieldname] = fieldobj.copy()
                    if fieldname == "init":
                        self.func = fieldobj.func
            for fieldname, fieldobj in parent.instance_fields.items():
                if fieldname not in self.instance_fields:
                    self.instance_fields[fieldname] = fieldobj
            self.fields

    def assign(self, other):
        print(self.name, other)
        self.value = other.value

    def call(self, symbol_table, *args):
        if self.func is None:
            raise Exception("Cannot call {}".format(self.name))
        elif isinstance(self.func, ObjConstructor):
            return self.func.eval(symbol_table, self.parents, self.instance_fields, self, *args)
        elif isinstance(self.func, FuncSig):
            return self.func.eval(symbol_table, *args)
        else:
            return self.func(*args)

    def __str__(self):
        return str(self.value)

    def copy(self):
        return InterpObj(self.name, value=self.value, fields={k:v.copy() for k, v in self.fields.items()},
                         objclass=self.objclass, instance_fields=self.instance_fields,
                         parents=self.parents, func=self.func)

@dataclass
class ExprList(ASTNode):
    exprs: 'list'
    def eval(self, symbol_table):
        last_ret = None
        for expression in self.exprs:
            last_ret = expression.eval(symbol_table)
            if symbol_table.return_called is True or symbol_table.loop_break_called is True:
                if symbol_table.return_val_sent is True:
                    last_ret = symbol_table.return_val
                break
        return last_ret

    def lprint(self):
        return "({})".format("\n, ".join([x.lprint() for x in self.exprs]))

@dataclass
class Expr(ASTNode):
    pass

@dataclass
class EmptyExpr(Expr):
    def eval(self, symbol_table):
        print("empty")
        return

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
class ArrayLiteral(Literal):
    value: list

@dataclass
class DictLiteral(Literal):
    value: dict

@dataclass
class Call(Expr):
    args: 'list'

    def lprint(self):
        return "({})".format(",".join([x.lprint() for x in self.args]))

    def eval(self, symbol_table, parent_obj):
        call_args = [x.eval(symbol_table) for x in self.args]
        return parent_obj.call(symbol_table, *call_args)

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
        block_symbol_table = symbol_table.new(scope_label=self.label)
        ret = self.exprs.eval(block_symbol_table)
        if symbol_table.class_definition:
            for name, symbol in block_symbol_table.symbols.items():
                symbol_table.symbols[name] = symbol
        return ret

@dataclass
class Accessor(Expr):
    access_type: Call | Slice | Field
    next_accessor: 'Accessor'

    def lprint(self):
        return "{}{}".format(self.access_type.lprint(), "" if self.next_accessor is None else self.next_accessor.lprint())

    def eval(self, symbol_table, parent_obj):
        print("access", self.access_type)
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
        if symbol_table.find(name) is None:
            if assign:
                symbol_table.bind(name, InterpObj(name))
            else:
                raise Exception("No name {} known".format(name))
        obj = symbol_table.find(name) # TODO: handle call/slice
        print(name, repr(obj))
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
        print(self.expr)
        symbol_table.bind(obj.name, self.expr.eval(symbol_table))
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
        return "({} {}{})".format("return", "" if self.expr is None else self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

    def eval(self, symbol_table):
        ret_val = None
        ret_val_called = False
        if self.expr:
            ret_val_called = True
            ret_val = self.expr.eval(symbol_table)
        symbol_table.scope_return(ret_val_called, ret_val)
        return ret_val

@dataclass
class BreakExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("break", "" if self.expr is None else self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

    def eval(self, symbol_table):
        ret_val = None
        if self.expr:
            ret_val = self.expr.eval(symbol_table)
        symbol_table.scope_break()
        return ret_val

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
        if self.ifguard.eval(symbol_table).value is True:
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
        return None if self.guard.eval(symbol_table).value is not True else self.expr.eval(symbol_table.new())

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

    def eval(self, symbol_table):
        parents = []
        def_init = ObjConstructor(EmptyExpr())
        if self.parents:
            parents = [symbol_table.find(x.eval(symbol_table)) for x in self.parents]
        name = None
        if self.name:
            name = self.name.eval(symbol_table)
        class_obj = InterpObj("anonclass" if name is None else name, parents=parents)
        if class_obj.func is None:
            class_obj.func = def_init
        if name:
            symbol_table.symbols[name] = class_obj
        class_symbol_table = symbol_table.new(class_definition=True)
        self.expr.eval(class_symbol_table)
        for symname, symbol in class_symbol_table.symbols.items():
            if symname == "init":
                class_obj.func = ObjConstructor(symbol.func)
            class_obj.instance_fields[symname] = symbol
        return class_obj

@dataclass
class FnDecl(Expr):
    name: Name
    args: None
    expr: Expr

    def lprint(self):
        return "(fn {} ({}) {})".format("" if self.name is None else "{}".format(self.name.lprint()),
            "" if self.args is None else "{}".format(",".join([x.lprint() for x in self.args])),
            self.expr.lprint())

    def eval(self, symbol_table, constructor=False):
        name = None
        funcsig = FuncSig(self.expr)
        if constructor:
            funcsig = ObjConstructor(self.expr)
        funcobj = InterpObj("func", func=funcsig)
        if self.args:
            funcsig.posargs = [x.target.name for x in self.args]
        if self.name:
            name = self.name.eval(symbol_table)
            symbol_table.bind(name, funcobj)
            funcobj.name = name
        return funcobj

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
    elloops: None = None
    elseexpr: None = None

    def lprint(self):
        return "(for {} in {} {})".format(self.iter_name.lprint(), self.iter_expr, self.expr.lprint())

    def eval(self, symbol_table):
        iter_pos = 0
        iter_arr = self.iter_expr.eval(symbol_table).value
        iter_name = self.iter_name.eval(symbol_table)
        last_expr = None
        symbol_table_loop = symbol_table.new(enclosing_loop_scope=True)
        while (iter_pos < len(iter_arr) and not symbol_table_loop.loop_break_called):
            iter_val = iter_arr[iter_pos].eval(symbol_table)
            symbol_table_loop.bind(iter_name, InterpObj(iter_name, value=iter_val))
            last_expr = self.expr.eval(symbol_table_loop)
            iter_pos += 1
        return last_expr

@dataclass
class WhileExpr(Expr):
    guard: Expr
    expr: Expr
    elloops: None = None
    elseexpr: None = None

    def lprint(self):
        return "(while {} {})".format(self.guard.lprint(), self.expr.lprint())

    def eval(self, symbol_table):
        last_expr = None
        symbol_table_loop = symbol_table.new(enclosing_loop_scope=True)
        while self.guard.eval(symbol_table).value is True and not symbol_table_loop.loop_break_called:
            last_expr = self.expr.eval(symbol_table_loop)
        return last_expr

@dataclass
class DoWhileExpr(Expr):
    guard: Expr
    expr: Expr

    def lprint(self):
        return "(do {} while {})".format(self.expr.lprint(), self.guard.lprint())

    def eval(self, symbol_table):
        symbol_table_loop = symbol_table.new(enclosing_loop_scope=True)
        last_expr = self.expr.eval(symbol_table_loop)
        while self.guard.eval(symbol_table).value is True and not symbol_table_loop.loop_break_called:
            last_expr = self.expr.eval(symbol_table_loop)
        return last_expr


