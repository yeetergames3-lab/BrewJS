from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass(frozen=True)
class SourceSpan:
    line: int
    column: int


class Expr:
    span: SourceSpan


class Stmt:
    span: SourceSpan


@dataclass(frozen=True)
class Program:
    statements: List[Stmt]


@dataclass(frozen=True)
class Identifier(Expr):
    name: str
    span: SourceSpan


@dataclass(frozen=True)
class Literal(Expr):
    value: Any
    span: SourceSpan


@dataclass(frozen=True)
class ArrayLiteral(Expr):
    items: List[Expr]
    span: SourceSpan


@dataclass(frozen=True)
class ObjectLiteral(Expr):
    pairs: List[tuple[str, Expr]]
    span: SourceSpan


@dataclass(frozen=True)
class UnaryExpr(Expr):
    op: str
    right: Expr
    span: SourceSpan


@dataclass(frozen=True)
class BinaryExpr(Expr):
    left: Expr
    op: str
    right: Expr
    span: SourceSpan


@dataclass(frozen=True)
class AssignExpr(Expr):
    target: Expr
    value: Expr
    span: SourceSpan


@dataclass(frozen=True)
class CallExpr(Expr):
    callee: Expr
    args: List[Expr]
    span: SourceSpan


@dataclass(frozen=True)
class MemberExpr(Expr):
    obj: Expr
    name: str
    span: SourceSpan


@dataclass(frozen=True)
class IndexExpr(Expr):
    obj: Expr
    index: Expr
    span: SourceSpan


@dataclass(frozen=True)
class FunctionExpr(Expr):
    name: Optional[str]
    params: List[str]
    body: List[Stmt]
    span: SourceSpan


@dataclass(frozen=True)
class ExpressionStmt(Stmt):
    expr: Expr
    span: SourceSpan


@dataclass(frozen=True)
class VarDecl(Stmt):
    name: str
    initializer: Optional[Expr]
    span: SourceSpan


@dataclass(frozen=True)
class BlockStmt(Stmt):
    statements: List[Stmt]
    span: SourceSpan


@dataclass(frozen=True)
class IfStmt(Stmt):
    condition: Expr
    then_branch: BlockStmt
    else_branch: Optional[Stmt]
    span: SourceSpan


@dataclass(frozen=True)
class WhileStmt(Stmt):
    condition: Expr
    body: BlockStmt
    span: SourceSpan


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    value: Optional[Expr]
    span: SourceSpan


@dataclass(frozen=True)
class TryStmt(Stmt):
    try_block: BlockStmt
    catch_name: Optional[str]
    catch_block: Optional[BlockStmt]
    finally_block: Optional[BlockStmt]
    span: SourceSpan


@dataclass(frozen=True)
class ThrowStmt(Stmt):
    value: Expr
    span: SourceSpan
