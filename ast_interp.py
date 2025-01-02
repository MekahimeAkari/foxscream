from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from resolver import Environment
from enum import Enum, auto

@dataclass(kw_only=True)
class ASTNode:
    environment: Environment | None = None

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

@dataclass(kw_only=True)
class Literal(ASTNode):
    value: Any

@dataclass(kw_only=True)
class Accessor(ASTNode):
    accessor: Accessor | None = None

@dataclass(kw_only=True)
class Call(Accessor):
    args: list[Expression] = field(default_factory=list)

@dataclass(kw_only=True)
class Slice(Accessor):
    slice: list[(Expression | None, Expression | None, Expression | None)] = field(default_factory=list)

@dataclass(kw_only=True)
class Field(Accessor):
    field: Name

@dataclass(kw_only=True)
class Expression(ASTNode):
    pass

@dataclass(kw_only=True)
class TypeExpr(ASTNode):
    pass

@dataclass(kw_only=True)
class Primary(ASTNode):
    typebound: TypeExpr | None = None
    target: Name | Literal
    accessor: Accessor | None = None

@dataclass(kw_only=True)
class Assignment(Expression):
    target: Primary
    operator: AssignOp
    expression: Expression

@dataclass(kw_only=True)
class BinExpr(Expression):
    lhs: Expression
    operator: BinOp
    rhs: Expression

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

@dataclass(kw_only=True)
class Program(ASTNode):
    statements: list[Statement] = field(default_factory=list)
