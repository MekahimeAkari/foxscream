from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from enum import Enum, auto
import copy
import pprint

@dataclass(kw_only=True)
class ASTNode:
    environment: Any | None = None
    is_return: bool = False
    def run(self, environment=None):
        raise Exception("run() for {} not yet implemented".format(type(self).__name__))

class Qualifier(Enum):
    CLASSVAR = auto()
    FINAL = auto()
    COMPLETE = auto()
    FIXED = auto()
    TERMINAL = auto()
    CONST = auto()
    INIT = auto()
    PRIVATE = auto()
    NOINHERIT = auto()
    DEPENDS = auto()

class AssignOp(Enum):
    NORMAL = auto()

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

class UnOp(Enum):
    NEG = auto()
    POS = auto()
    INV = auto()
    NOT = auto()

class ClassType(Enum):
    CLASS = auto()
    STATIC = auto()
    TRAIT = auto()

@dataclass(kw_only=True)
class Name(ASTNode):
    name: str
    def run(self, **kwargs):
        return self.name

@dataclass(kw_only=True)
class Literal(ASTNode):
    value: Any
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        return environment.new_obj(value=self.value, qualifiers=qualifiers)

@dataclass(kw_only=True)
class StringLiteral(Literal):
    value: str

@dataclass(kw_only=True)
class IntLiteral(Literal):
    value: int

@dataclass(kw_only=True)
class FloatLiteral(Literal):
    value: float

@dataclass(kw_only=True)
class Accessor(ASTNode):
    accessor: Accessor | None = None

@dataclass(kw_only=True)
class Call(Accessor):
    args: list[Expression] = field(default_factory=list)
    def run(self, obj, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        args = []
        for arg in self.args:
            args.append(arg.run(environment=environment, qualifiers=qualifiers))
        res = obj.call(*args, environment=environment)
        if self.accessor is not None:
            res = self.accessor.run(res, environment=environment, qualifiers=qualifiers)
        return res

@dataclass(kw_only=True)
class Slice(Accessor):
    slice: list[(Expression | None, Expression | None, Expression | None)] = field(default_factory=list)
    def run(self, obj, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        slices = []
        for slice in self.slice:
            slices.append(slice.run(environment=environment, qualifiers=qualifiers))
        res = obj.slots_access(*slices, environment=environment)
        if self.accessor is not None:
            res = self.accessor.run(res, environment=environment, qualifiers=qualifiers)
        return res

@dataclass(kw_only=True)
class Field(Accessor):
    field_name: Name
    def run(self, obj, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        field_name = self.field_name
        if isinstance(field_name, Name):
            field_name = field_name.name
        res = obj.get(field_name=field_name)
        obj_environment = environment.new_scope(new_scope_names=obj.fields)
        if self.accessor is not None:
            res = self.accessor.run(res, environment=obj_environment, qualifiers=qualifiers)
        return res

@dataclass(kw_only=True)
class Expression(ASTNode):
    pass
    def run(self, environment=None, qualifiers=None):
        raise Exception("run() for {} not yet implemented".format(type(self).__name__))

@dataclass(kw_only=True)
class TypeExpr(ASTNode):
    pass

@dataclass(kw_only=True)
class Primary(ASTNode):
    typebound: TypeExpr | None = None
    target: Name | Literal
    accessor: Accessor | None = None
    def run(self, environment=None, qualifiers=None, assignment=False):
        if environment is None:
            environment = self.environment
        return environment.get(self.target, assignment=assignment, qualifiers=qualifiers, accessors=self.accessor)

    def get_name(self):
        return self.target.name

@dataclass(kw_only=True)
class Assignment(Expression):
    target: Primary
    operator: AssignOp
    expression: Expression
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        assignment_target = self.target.run(environment=environment, qualifiers=qualifiers, assignment=True)
        assignment_value = self.expression.run(environment=environment, qualifiers=qualifiers)
        return assignment_target.assign(self.environment, self.operator, assignment_value)

@dataclass(kw_only=True)
class BinExpr(Expression):
    lhs: Expression
    operator: BinOp
    rhs: Expression
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        lhs_res = self.lhs.run(environment=environment, qualifiers=qualifiers)
        return lhs_res.run_operator(self.operator, rhs=self.rhs.run(environment=environment, qualifiers=qualifiers))

@dataclass(kw_only=True)
class UnExpr(Expression):
    operator: UnOp
    rhs: Expression
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        rhs_res = self.rhs.run(environment=environment, qualifiers=qualifiers)
        return rhs_res.run_operator(self.operator)

@dataclass(kw_only=True)
class Block(Expression):
    statements: list[Statement] | None = None
    def run(self, environment=None, qualifiers=None, add_scope=True):
        if self.statements is None:
            return
        if environment is None:
            environment = self.environment
        if add_scope is True:
            block_environment = environment.new_scope()
        else:
            block_environment = environment
        res = None
        for statement in self.statements:
            res = statement.run(environment=block_environment)
            if statement.is_return:
                return res
        return res

@dataclass(kw_only=True)
class IfStatement(Expression):
    condition: Expression
    block: Block
    elifs: list[ElifStatement] | None
    else_stmt: ElseStatement | None
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        if self.condition.run(environment=environment, qualifiers=qualifiers).to_bool():
            return self.block.run(environment=environment, qualifiers=qualifiers)
        if self.elifs is not None:
            for elif_stmt in self.elifs:
                if elif_stmt.condition.run(environment=environment, qualifiers=qualifiers).to_bool():
                    return elif_stmt.block.run(environment=environment, qualifiers=qualifiers)
        if self.else_stmt is not None:
            return self.else_stmt.block.run(environment=environment, qualifiers=qualifiers)

@dataclass(kw_only=True)
class ElifStatement(Expression):
    condition: Expression
    block: Block

@dataclass(kw_only=True)
class ElseStatement(Expression):
    block: Block

@dataclass(kw_only=True)
class WhileStatement(Expression):
    condition: Expression
    block: Block
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        loop_environment = environment.new_scope()
        loop_res = None
        while self.condition.run(environment=environment, qualifiers=qualifiers).to_bool():
            loop_res = self.block.run(environment=loop_environment, qualifiers=qualifiers, add_scope=False)
        return loop_res

@dataclass(kw_only=True)
class FunctionDeclaration(Expression):
    name: Name | None
    arglist: list[Primary] = field(default_factory=list)
    block: Block
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        name = self.name
        if isinstance(self.name, Name):
            name = self.name.run(environment=environment, qualifiers=qualifiers)
        args = [x.get_name() for x in self.arglist]
        return environment.add_func(name, self.block, *args)

@dataclass(kw_only=True)
class ReturnStatement(Expression):
    expression: Expression | None = None
    is_return: bool = True
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        if self.expression is None:
            return
        else:
            return self.expression.run(environment=environment, qualifiers=qualifiers)

@dataclass(kw_only=True)
class ArrayDeclaration(Expression):
    is_dict: bool
    items: list[Expression] | list[(Expression, Expression)]
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        ret_arr = None
        if self.is_dict:
            ret_arr = {}
            for key_expr, val_expr in self.items:
                if isinstance(key_expr, ASTNode):
                    key_expr = key_expr.run(environment=environment, qualifiers=qualifiers).get(value=True)
                if isinstance(val_expr, ASTNode):
                    val_expr = val_expr.run(environment=environment, qualifiers=qualifiers).get(value=True)
                ret_arr[key_expr] = val_expr
        else:
            raise Exception("Do arrays properly")
        return environment.new_obj(value=ret_arr)

@dataclass(kw_only=True)
class ClassDeclaration(Expression):
    class_type: ClassType
    name: str | None
    of_list: list[Name] = field(default_factory=list)
    has_list: list[Name] = field(default_factory=list)
    block: Block
    def run(self, environment=None, qualifiers=None):
        if environment is None:
            environment = self.environment
        if self.class_type == ClassType.CLASS:
            field_environment = environment.new_scope()
            self.block.run(environment=field_environment, qualifiers=qualifiers, add_scope=False)
            new_obj = environment.add_obj(self.name, is_class=True, instance_fields=copy.deepcopy(field_environment.names))
            return new_obj
        else:
            raise Exception("Other classes not done")

@dataclass(kw_only=True)
class Statement(ASTNode):
    qualifiers: list[Qualifier] | None = None
    expression: Expression | None = None
    def __post_init__(self):
        if isinstance(self.expression, ReturnStatement):
            self.is_return = True
    def run(self, environment=None):
        if environment is None:
            environment = self.environment
        return self.expression.run(environment=environment, qualifiers=self.qualifiers)

@dataclass(kw_only=True)
class Program(ASTNode):
    statements: list[Statement] = field(default_factory=list)
    def run(self, environment=None):
        results = []
        if environment is None:
            environment = self.environment
        for statement in self.statements:
            results.append(statement.run(environment=environment))
        return results
