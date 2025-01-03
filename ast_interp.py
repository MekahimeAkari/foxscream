from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from enum import Enum, auto

@dataclass(kw_only=True)
class ASTNode:
    environment: Any | None = None
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
        res = obj.call(*args)
        if self.accessor is not None:
            res = self.accessor(res, environment=None, qualifiers=None)
        return res

@dataclass(kw_only=True)
class Slice(Accessor):
    slice: list[(Expression | None, Expression | None, Expression | None)] = field(default_factory=list)

@dataclass(kw_only=True)
class Field(Accessor):
    field: Name

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
        return environment.get(self.target, assignment=assignment, qualifiers=qualifiers, accessors=self.accessor.run() if self.accessor is not None else None)

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

@dataclass(kw_only=True)
class Block(Expression):
    statements: list[Statement] | None = None

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

@dataclass(kw_only=True)
class FunctionDeclaration(Expression):
    name: Name | None
    arglist: list[Primary] = field(default_factory=list)
    block: Block

@dataclass(kw_only=True)
class ReturnStatement(Expression):
    expression: Expression | None = None

@dataclass(kw_only=True)
class ArrayDeclaration(Expression):
    is_dict: bool
    items: list[Expression] | list[(Expression, Expression)]

@dataclass(kw_only=True)
class ClassDeclaration(Expression):
    class_type: ClassType
    name: str | None
    of_list: list[Name] = field(default_factory=list)
    has_list: list[Name] = field(default_factory=list)
    block: Block

@dataclass(kw_only=True)
class Statement(ASTNode):
    qualifiers: list[Qualifier] | None = None
    expression: Expression | None = None
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
