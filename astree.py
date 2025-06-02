from dataclasses import dataclass, field
from enum import Enum, auto
import pprint
import copy

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
    break_called: bool = False
    class_definition: bool = False
    registered_defers:list = field(default_factory=list)

    def new(self, symbols=None, scope_label=None, enclosing_function_scope=False,
            enclosing_loop_scope=False, class_definition=False):
        return SymbolTable(parent=self, symbols={} if symbols is None else symbols,
                           scope_label=scope_label,
                           enclosing_function_scope=enclosing_function_scope,
                           enclosing_loop_scope=enclosing_loop_scope,
                           class_definition=class_definition)

    def find(self, name, length=0, throw=False):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.find(name, length=length+1, throw=throw)
        if throw:
            raise Exception("No name {}".format(name))
        return None

    def bind(self, name, obj):
        if obj is None:
            obj = self.find("null")
        if name in self.symbols or self.class_definition or self.parent is None:
            self.symbols[name] = obj
            obj.name = name
            return obj
        elif self.parent is not None:
            if self.parent.bind(name, obj) is None:
                self.symbols[name] = obj
                obj.name = name
                return obj
            else:
                return obj
        return None

    def scope_return(self, return_val_sent=False, return_val=None):
        self.return_called = True
        self.return_val_sent = return_val_sent
        self.return_val = return_val
        self.break_called = True
        if self.enclosing_function_scope is False and self.parent:
            self.parent.scope_return(return_val_sent, return_val)

    def scope_break(self, loop_label=None):
        self.break_called = True
        if self.enclosing_loop_scope is False and self.parent:
            self.parent.scope_break(loop_label)

    def scope_continue(self, loop_label=None):
        if self.enclosing_loop_scope is False and self.parent:
            self.break_called = True
            self.parent.scope_continue(loop_label)

    def scope_leave(self, label=None):
        self.break_called = True

    def add_defer(self, expr, label=None):
        self.registered_defers.insert(0, expr)

    def print_keys(self, level=0):
        return "{}: {}{}".format(level, self.symbols.keys(), ", {}".format(self.parent.print_keys(level=level+1) if self.parent is not None else ""))

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
        res = self.body.eval(func_symbol_table)
        return res

@dataclass
class ObjConstructor(FuncSig):

    def eval(self, symbol_table, parents, objclass, *args):
        ret_obj = InterpObj("newobj of {}".format(objclass.name), parents=parents, symbol_table=symbol_table, objclass=objclass, instance=True)
        for name, symbol in ret_obj.symbol_table.symbols.items():
            symbol.symbol_table.parent = ret_obj.symbol_table
        func_symbol_table = symbol_table.new()
        func_symbol_table.enclosing_function_scope = True
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
    symbol_table: SymbolTable = field(default_factory=SymbolTable)
    instance_symbol_table: SymbolTable = field(default_factory=SymbolTable)
    objclass: None = None
    parents: list = field(default_factory=list)
    func: None = None
    instance: bool = False

    def __post_init__(self):
        parents_symbol_table = {}
        parents_instance_symbol_table = {}
        for parent in self.parents:
            for name, value in parent.symbol_table.symbols.items():
                parents_symbol_table[name] = value
            for name, value in parent.instance_symbol_table.symbols.items():
                parents_instance_symbol_table[name] = value
        if self.instance:
            for name, value in parents_instance_symbol_table.items():
                if name not in self.symbol_table.symbols:
                    self.symbol_table.symbols[name] = copy.copy(value)
                    self.symbol_table.symbols[name].parent = self.symbol_table
        else:
            for name, value in parents_symbol_table.items():
                if name not in self.symbol_table.symbols:
                    self.symbol_table.symbols[name] = copy.copy(value)
                    self.symbol_table.symbols[name].parent = self.symbol_table
            for name, value in parents_instance_symbol_table.items():
                if name not in self.instance_symbol_table.symbols:
                    self.instance_symbol_table.symbols[name] = copy.copy(value)
                    self.instance_symbol_table.symbols[name].parent = self.instance_symbol_table

    def assign(self, other):
        self.value = other.value

    def call(self, symbol_table, *args):
        if self.func is None:
            raise Exception("Cannot call {}".format(self.name))
        elif isinstance(self.func, ObjConstructor):
            return self.func.eval(copy.deepcopy(self.instance_symbol_table), self.parents, self, *args)
        elif isinstance(self.func, FuncSig):
            return self.func.eval(self.symbol_table, *args)
        else:
            return self.func(*args)

    def __str__(self):
        if self.value is None:
            return str(self.name)
        else:
            return str(self.value)

    def get_class(self):
        if self.instance:
            return self.objclass
        else:
            return self

    def get_all_classes(self):
        classes = [self.get_class()]
        for parent in self.parents:
            parent_classes = parent.get_all_classes()
            for parent_class in parent_classes:
                if parent_class not in classes:
                    classes.append(parent_class)
        return classes

    def of_op(self, other):
        other_classes = other.get_all_classes()
        self_classes = self.get_all_classes()
        for self_class in self_classes:
            if self_class in other_classes:
                return True
        return False

@dataclass
class ExprList(ASTNode):
    exprs: 'list'
    def eval(self, symbol_table):
        last_ret = None
        for expression in self.exprs:
            last_ret = expression.eval(symbol_table)
            if symbol_table.return_called is True or symbol_table.break_called is True:
                if symbol_table.return_val_sent is True:
                    last_ret = symbol_table.return_val
                break
        for defer in symbol_table.registered_defers:
            last_ret = defer.eval(symbol_table)
        return last_ret

    def lprint(self):
        return "({})".format("\n, ".join([x.lprint() for x in self.exprs]))

    def visit(self, interp, **kwargs):
        return interp.exprlist(self, **kwargs)

@dataclass
class Expr(ASTNode):
    pass

@dataclass
class EmptyExpr(Expr):
    def eval(self, symbol_table):
        return

    def visit(self, interp, **kwargs):
        return interp.empty(self, **kwargs)

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

    def visit(self, interp, **kwargs):
        return interp.block(self, **kwargs)

class Primary(Expr):
    pass

@dataclass
class Name(Primary):
    name: str

    def lprint(self):
        return self.name

    def eval(self, symbol_table):
        return self.name

    def visit(self, interp, **kwargs):
        return interp.name(self, **kwargs)

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

    def visit(self, interp, **kwargs):
        return interp.stringlit(self, **kwargs)

@dataclass
class IntLiteral(Literal):
    value: int

    def visit(self, interp, **kwargs):
        return interp.intlit(self, **kwargs)

@dataclass
class FloatLiteral(Literal):
    value: float

    def visit(self, interp, **kwargs):
        return interp.floatlit(self, **kwargs)

@dataclass
class BoolLiteral(Literal):
    value: bool

    def visit(self, interp, **kwargs):
        return interp.boollit(self, **kwargs)

@dataclass
class NullLiteral(Literal):
    value: None

    def visit(self, interp, **kwargs):
        return interp.nulllit(self, **kwargs)

@dataclass
class ArrayLiteral(Literal):
    value: list

    def visit(self, interp, **kwargs):
        return interp.arraylit(self, **kwargs)

@dataclass
class DictLiteral(Literal):
    value: dict

    def visit(self, interp, **kwargs):
        return interp.dictlit(self, **kwargs)

@dataclass
class Call(Expr):
    args: 'list'

    def lprint(self):
        return "({})".format(",".join([x.lprint() for x in self.args]))

    def eval(self, symbol_table, obj, assign=False, assign_expr=None, parent_obj=None):
        call_args = [x.eval(symbol_table) for x in self.args]
        return obj.call(symbol_table, *call_args)

    def visit(self, interp):
        return interp.call(self)

@dataclass
class Slice(Expr):
    pass

    def visit(self, interp, **kwargs):
        return interp.slice(self, **kwargs)

@dataclass
class Field(Expr):
    name: Name

    def lprint(self):
        return ".{}".format(self.name.lprint())

    def eval(self, symbol_table, obj, assign=False, assign_expr=None):
        field_name = self.name.eval(symbol_table)
        obj_symbol_table = obj.symbol_table
        if assign is False:
            return obj_symbol_table.symbols[field_name]
        else:
            obj_symbol_table.symbols[field_name] = assign_expr
            return obj_symbol_table.symbols[field_name]

    def visit(self, interp, **kwargs):
        return interp.field(self, **kwargs)

@dataclass
class Accessor(Expr):
    access_type: Call | Slice | Field
    next_accessor: 'Accessor'

    def lprint(self):
        return "{}{}".format(self.access_type.lprint(), "" if self.next_accessor is None else self.next_accessor.lprint())

    def eval(self, symbol_table, obj, assign=False, assign_expr=None):
        if self.next_accessor is None:
            return self.access_type.eval(symbol_table, obj,
                                         assign=assign, assign_expr=assign_expr)
        return self.next_accessor.eval(symbol_table,
            self.access_type.eval(obj.symbol_table, obj), assign=assign,
                                                          assign_expr=assign_expr)

    def visit(self, interp, **kwargs):
        return interp.accessor(self, **kwargs)

@dataclass
class Primary(Expr):
    target: Name | Literal
    accessor: 'Accessor'

    def lprint(self):
        return "{}{}".format(self.target.lprint(), "" if self.accessor is None else self.accessor.lprint())

    def eval(self, symbol_table, assign=False, assign_expr=None):
        if not isinstance(self.target, Name):
            if assign:
                raise Exception("Cannot assign to Literal")
            else:
                value = self.target.eval(symbol_table)
                if isinstance(value, InterpObj):
                    value = value.value
                return InterpObj("literal", value=value)
        name = self.target.eval(symbol_table)
        if self.accessor is not None:
            return self.accessor.eval(symbol_table, symbol_table.find(name, throw=True), assign=assign,
                                      assign_expr=assign_expr)
        elif assign:
            return symbol_table.bind(name, assign_expr)
        else:
            return symbol_table.find(name, throw=True)

    def visit(self, interp, **kwargs):
        return interp.primary(self, **kwargs)

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
        return self.target.eval(symbol_table, assign=True,
                                assign_expr=self.expr.eval(symbol_table))

    def visit(self, interp):
        return interp.assign(self)

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
        lhs = self.lhs.eval(symbol_table)
        if self.operator != BinOp.OF and self.operator != BinOp.HAS:
            lhs = lhs.value if lhs is not None else symbol_table.find("null")
        if self.operator != BinOp.AND and self.operator != BinOp.OR:
            rhs = self.rhs.eval(symbol_table)
            if self.operator != BinOp.OF and self.operator != BinOp.HAS:
                rhs = rhs.value if rhs is not None else symbol_table.find("null")

        if self.operator == BinOp.ADD:
            res = lhs + rhs
        elif self.operator == BinOp.SUB:
            res = lhs - rhs
        elif self.operator == BinOp.EXP:
            res = lhs ** rhs
        elif self.operator == BinOp.MUL:
            res = lhs * rhs
        elif self.operator == BinOp.DIV:
            res = lhs / rhs
        elif self.operator == BinOp.INTDIV:
            res = lhs // rhs
        elif self.operator == BinOp.MOD:
            res = lhs % rhs
        elif self.operator == BinOp.LSHIFT:
            res = lhs << rhs
        elif self.operator == BinOp.RSHIFT:
            res = lhs >> rhs
        elif self.operator == BinOp.BITAND:
            res = lhs & rhs
        elif self.operator == BinOp.BITXOR:
            res = lhs ^ rhs
        elif self.operator == BinOp.BITOR:
            res = lhs | rhs
        elif self.operator == BinOp.EQ:
            res = lhs == rhs
        elif self.operator == BinOp.NE:
            res = lhs != rhs
        elif self.operator == BinOp.GT:
            res = lhs > rhs
        elif self.operator == BinOp.LT:
            res = lhs < rhs
        elif self.operator == BinOp.GE:
            res = lhs >= rhs
        elif self.operator == BinOp.LE:
            res = lhs <= rhs
        elif self.operator == BinOp.AND:
            res = lhs
            if lhs is True:
                rhs = self.rhs.eval(symbol_table)
                if rhs is None:
                    rhs = symbol_table.find("null")
                res = lhs and rhs
        elif self.operator == BinOp.OR:
            res = lhs
            if lhs is False:
                rhs = self.rhs.eval(symbol_table)
                if rhs is None:
                    rhs = symbol_table.find("null")
                res = lhs or rhs
        elif self.operator == BinOp.OF:
            return lhs.of_op(rhs)
        else:
            raise Exception("Unimplemented operator " + self.operator)
        return InterpObj("intermediate", value=res)

    def visit(self, interp):
        return interp.binexpr(self)

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

    def visit(self, interp):
        return interp.unexpr(self)

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

    def visit(self, interp):
        return interp.returnexpr(self)

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

    def visit(self, interp):
        return interp.breakexpr(self)

@dataclass
class ContinueExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("continue", "" if self.expr is None else self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

    def eval(self, symbol_table):
        ret_val = None
        if self.expr:
            ret_val = self.expr.eval(symbol_table)
        symbol_table.scope_continue()
        return ret_val

    def visit(self, interp):
        return interp.continueexpr(self)

@dataclass
class LeaveExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("leave", "" if self.expr is None else self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

    def eval(self, symbol_table):
        ret_val = None
        if self.expr:
            ret_val = self.expr.eval(symbol_table)
        symbol_table.scope_leave()
        return ret_val

    def visit(self, interp):
        return interp.leaveexpr(self)

@dataclass
class DeferExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("defer", "" if self.expr is None else self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

    def eval(self, symbol_table):
        symbol_table.add_defer(self.expr)

    def visit(self, interp):
        return interp.deferexpr(self)

@dataclass
class YieldExpr(SingleKWExpr):
    def lprint(self):
        return "({} {}{})".format("yield", self.expr.lprint(), "" if self.target is None else " to {}".format(self.target.lprint()))

    def visit(self, interp):
        return interp.yieldexpr(self)

@dataclass
class IfExpr(Expr):
    guard: Expr
    expr: Expr
    elexpr: None = None

    def lprint(self):
        return "(if {} {} {})".format(self.guard.lprint(), self.expr.lprint(), self.elexpr.lprint() if self.elexpr is not None else "")

    def eval(self, symbol_table):
        if self.guard.eval(symbol_table).value is True:
            return self.expr.eval(symbol_table.new())
        if self.elifexprs is not None:
            for elifexpr in self.elifexprs:
                elif_res, el_ran = elifexpr.eval(symbol_table)
                if el_ran is True:
                    return elif_res
        if self.elseexpr is not None:
            return self.elseexpr.eval(symbol_table)

    def visit(self, interp):
        return interp.ifexpr(self)

@dataclass
class ElseExpr(Expr):
    expr: Expr

    def lprint(self):
        return "(else {})".format(self.expr.lprint())

    def eval(self, symbol_table):
        return self.expr.eval(symbol_table.new())

    def visit(self, interp):
        return interp.elseexpr(self)

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
            parents = [symbol_table.find(x.eval(symbol_table), throw=True) for x in self.parents]
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
        for name, symbol in class_symbol_table.symbols.items():
            class_obj.instance_symbol_table.symbols[name] = symbol
        for symname, symbol in class_obj.instance_symbol_table.symbols.items():
            if symname == "init":
                class_obj.func = ObjConstructor(symbol.func)
        class_obj.symbol_table.parent = symbol_table
        class_obj.instance_symbol_table.parent = symbol_table
        return class_obj

    def visit(self, interp):
        return interp.classdecl(self)

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
            funcsig = ObjConstructor(self.expr, symbol_table=symbol_table)
        funcobj = InterpObj("func", func=funcsig, symbol_table=symbol_table)
        if self.args:
            funcsig.posargs = [x.target.name for x in self.args]
        if self.name:
            name = self.name.eval(symbol_table)
            symbol_table.bind(name, funcobj)
            funcobj.name = name
        return funcobj

    def visit(self, interp):
        return interp.fndecl(self)

@dataclass
class MatchExpr(Expr):
    init_expr: Expr
    cases: 'list'

    def lprint(self):
        return "(match {} {})".format(self.init_expr.lprint(), ", ".join([x.lprint() for x in self.cases]))

    def visit(self, interp):
        return interp.matchexpr(self)

@dataclass
class CaseExpr(Expr):
    match: Expr
    expr: Expr
    default: bool = False

    def lprint(self):
        return "case {}:{}".format("default" if self.default else self.match.lprint(), self.expr.lprint())

    def visit(self, interp):
        return interp.caseexpr(self)

@dataclass
class ForExpr(Expr):
    iter_name: Name
    iter_expr: Expr
    expr: Expr
    elexpr: None = None

    def lprint(self):
        return "(for {} in {} {} {})".format(self.iter_name.lprint(), self.iter_expr, self.expr.lprint(), self.elexpr.lprint() if self.elexpr is not None else "")

    def eval(self, symbol_table):
        iter_pos = 0
        iter_arr = self.iter_expr.eval(symbol_table).value
        iter_name = self.iter_name.eval(symbol_table)
        last_expr = None
        symbol_table_loop = symbol_table.new(enclosing_loop_scope=True)
        loop_ran = False
        while (iter_pos < len(iter_arr) and not symbol_table_loop.break_called):
            loop_ran = True
            iter_val = iter_arr[iter_pos].eval(symbol_table)
            symbol_table_loop.bind(iter_name, InterpObj(iter_name, value=iter_val))
            last_expr = self.expr.eval(symbol_table_loop)
            iter_pos += 1
        if loop_ran:
            return last_expr
        if self.elifexprs is not None:
            for elexpr in self.elexprs:
                el_res, el_run = elexpr.eval(symbol_table)
                if el_run is True:
                    return el_res
        if self.elseexpr is not None:
            return self.elseexpr.eval(symbol_table)

    def visit(self, interp):
        return interp.forexpr(self)

@dataclass
class WhileExpr(Expr):
    guard: Expr
    expr: Expr
    elexpr: None = None

    def lprint(self):
        return "(while {} {} {})".format(self.guard.lprint(), self.expr.lprint(), self.elexpr.lprint() if self.elexpr is not None else "")

    def eval(self, symbol_table):
        last_expr = None
        symbol_table_loop = symbol_table.new(enclosing_loop_scope=True)
        loop_ran = False
        while self.guard.eval(symbol_table).value is True and not symbol_table_loop.break_called:
            loop_ran = True
            last_expr = self.expr.eval(symbol_table_loop)
        if loop_ran:
            return last_expr
        if self.elifexprs is not None:
            for elexpr in self.elexprs:
                el_res, el_ran = elexpr.eval(symbol_table)
                if el_ran is True:
                    return el_res
        if self.elseexpr is not None:
            return self.elseexpr.eval(symbol_table)

    def visit(self, interp):
        return interp.whileexpr(self)

@dataclass
class DoWhileExpr(Expr):
    guard: Expr
    expr: Expr

    def lprint(self):
        return "(do {} while {})".format(self.expr.lprint(), self.guard.lprint())

    def eval(self, symbol_table):
        symbol_table_loop = symbol_table.new(enclosing_loop_scope=True)
        last_expr = self.expr.eval(symbol_table_loop)
        while self.guard.eval(symbol_table).value is True and not symbol_table_loop.break_called:
            last_expr = self.expr.eval(symbol_table_loop)
        return last_expr

    def visit(self, interp):
        return interp.dowhileexpr(self)

