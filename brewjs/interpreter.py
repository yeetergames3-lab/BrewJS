from __future__ import annotations

from typing import Any

from brewjs import ast_nodes as ast
from brewjs.builtins import default_globals
from brewjs.runtime import (
    BrewReturn,
    BrewRuntimeError,
    BrewThrow,
    Environment,
    FunctionValue,
    NativeFunction,
)


class Interpreter:
    def __init__(self) -> None:
        self.globals = Environment()
        for name, value in default_globals().items():
            self.globals.define(name, value)
        self.environment = self.globals

    def interpret(self, program: ast.Program) -> None:
        try:
            for stmt in program.statements:
                self.execute(stmt)
        except BrewRuntimeError as exc:
            raise
        except BrewThrow as exc:
            raise BrewRuntimeError(f"Uncaught exception: {exc.value}", exc.span)

    def execute(self, stmt: ast.Stmt) -> None:
        if isinstance(stmt, ast.ExpressionStmt):
            self.evaluate(stmt.expr)
            return
        if isinstance(stmt, ast.VarDecl):
            value = self.evaluate(stmt.initializer) if stmt.initializer else None
            self.environment.define(stmt.name, value)
            return
        if isinstance(stmt, ast.BlockStmt):
            self.execute_block(stmt.statements, Environment(self.environment))
            return
        if isinstance(stmt, ast.IfStmt):
            if self.is_truthy(self.evaluate(stmt.condition)):
                self.execute(stmt.then_branch)
            elif stmt.else_branch:
                self.execute(stmt.else_branch)
            return
        if isinstance(stmt, ast.WhileStmt):
            while self.is_truthy(self.evaluate(stmt.condition)):
                self.execute(stmt.body)
            return
        if isinstance(stmt, ast.ReturnStmt):
            value = self.evaluate(stmt.value) if stmt.value else None
            raise BrewReturn(value)
        if isinstance(stmt, ast.TryStmt):
            self._execute_try(stmt)
            return
        if isinstance(stmt, ast.ThrowStmt):
            value = self.evaluate(stmt.value)
            raise BrewThrow(value, stmt.span)
        raise BrewRuntimeError(f"Unknown statement type {type(stmt).__name__}", stmt.span)

    def execute_block(self, statements: list[ast.Stmt], env: Environment) -> None:
        previous = self.environment
        try:
            self.environment = env
            for stmt in statements:
                self.execute(stmt)
        finally:
            self.environment = previous

    def evaluate(self, expr: ast.Expr) -> Any:
        if isinstance(expr, ast.Literal):
            return expr.value
        if isinstance(expr, ast.Identifier):
            return self.environment.get(expr.name)
        if isinstance(expr, ast.ArrayLiteral):
            return [self.evaluate(item) for item in expr.items]
        if isinstance(expr, ast.ObjectLiteral):
            return {key: self.evaluate(val) for key, val in expr.pairs}
        if isinstance(expr, ast.UnaryExpr):
            right = self.evaluate(expr.right)
            if expr.op == "-":
                return -self._ensure_number(right, expr)
            if expr.op == "!":
                return not self.is_truthy(right)
        if isinstance(expr, ast.BinaryExpr):
            return self._binary(expr)
        if isinstance(expr, ast.AssignExpr):
            return self._assign(expr)
        if isinstance(expr, ast.MemberExpr):
            obj = self.evaluate(expr.obj)
            return self._get_member(obj, expr.name)
        if isinstance(expr, ast.IndexExpr):
            obj = self.evaluate(expr.obj)
            index = self.evaluate(expr.index)
            return self._get_index(obj, index, expr)
        if isinstance(expr, ast.CallExpr):
            callee = self.evaluate(expr.callee)
            args = [self.evaluate(arg) for arg in expr.args]
            return self._call(callee, args, expr)
        if isinstance(expr, ast.FunctionExpr):
            return FunctionValue(expr.name, expr.params, expr.body, self.environment, expr.span)
        raise BrewRuntimeError(f"Unknown expression type {type(expr).__name__}", expr.span)

    def _binary(self, expr: ast.BinaryExpr) -> Any:
        if expr.op == "&&":
            left = self.evaluate(expr.left)
            return self.evaluate(expr.right) if self.is_truthy(left) else left
        if expr.op == "||":
            left = self.evaluate(expr.left)
            return left if self.is_truthy(left) else self.evaluate(expr.right)
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)
        if expr.op == "+":
            return left + right
        if expr.op == "-":
            return self._ensure_number(left, expr) - self._ensure_number(right, expr)
        if expr.op == "*":
            return self._ensure_number(left, expr) * self._ensure_number(right, expr)
        if expr.op == "/":
            return self._ensure_number(left, expr) / self._ensure_number(right, expr)
        if expr.op == "%":
            return self._ensure_number(left, expr) % self._ensure_number(right, expr)
        if expr.op == "<":
            return left < right
        if expr.op == "<=":
            return left <= right
        if expr.op == ">":
            return left > right
        if expr.op == ">=":
            return left >= right
        if expr.op == "==":
            return left == right
        if expr.op == "!=":
            return left != right
        raise BrewRuntimeError(f"Unknown operator '{expr.op}'", expr.span)

    def _assign(self, expr: ast.AssignExpr) -> Any:
        value = self.evaluate(expr.value)
        target = expr.target
        if isinstance(target, ast.Identifier):
            self.environment.assign(target.name, value)
            return value
        if isinstance(target, ast.MemberExpr):
            obj = self.evaluate(target.obj)
            self._set_member(obj, target.name, value, expr)
            return value
        if isinstance(target, ast.IndexExpr):
            obj = self.evaluate(target.obj)
            index = self.evaluate(target.index)
            self._set_index(obj, index, value, expr)
            return value
        raise BrewRuntimeError("Invalid assignment target", expr.span)

    def _call(self, callee: Any, args: list[Any], expr: ast.CallExpr) -> Any:
        if isinstance(callee, FunctionValue):
            return callee(self, args)
        if isinstance(callee, NativeFunction):
            return callee(args)
        if callable(callee):
            return callee(args)
        raise BrewRuntimeError("Can only call functions", expr.span)

    def _get_member(self, obj: Any, name: str) -> Any:
        if isinstance(obj, dict):
            if name in obj:
                return obj[name]
            raise BrewRuntimeError(f"Property '{name}' not found")
        if isinstance(obj, list):
            if name == "push":
                return NativeFunction("array.push", 1, lambda a: obj.append(a[0]) or None)
            if name == "pop":
                return NativeFunction("array.pop", 0, lambda a: obj.pop() if obj else None)
            if name == "length":
                return len(obj)
        raise BrewRuntimeError(f"Property '{name}' not found")

    def _set_member(self, obj: Any, name: str, value: Any, expr: ast.AssignExpr) -> None:
        if isinstance(obj, dict):
            obj[name] = value
            return
        raise BrewRuntimeError("Cannot set property on non-object", expr.span)

    def _get_index(self, obj: Any, index: Any, expr: ast.IndexExpr) -> Any:
        try:
            return obj[index]
        except Exception as exc:
            raise BrewRuntimeError(f"Index error: {exc}", expr.span) from exc

    def _set_index(self, obj: Any, index: Any, value: Any, expr: ast.AssignExpr) -> None:
        try:
            obj[index] = value
        except Exception as exc:
            raise BrewRuntimeError(f"Index error: {exc}", expr.span) from exc

    @staticmethod
    def is_truthy(value: Any) -> bool:
        return bool(value)

    @staticmethod
    def _ensure_number(value: Any, expr: ast.Expr) -> float:
        if isinstance(value, (int, float)):
            return value
        raise BrewRuntimeError("Expected number", expr.span)

    def _execute_try(self, stmt: ast.TryStmt) -> None:
        try:
            self.execute(stmt.try_block)
        except BrewThrow as exc:
            if stmt.catch_block is None:
                raise
            env = Environment(self.environment)
            if stmt.catch_name:
                env.define(stmt.catch_name, exc.value)
            self.execute_block(stmt.catch_block.statements, env)
        finally:
            if stmt.finally_block:
                self.execute(stmt.finally_block)
