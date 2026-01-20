from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from brewjs.ast_nodes import SourceSpan


class BrewRuntimeError(RuntimeError):
    def __init__(self, message: str, span: Optional[SourceSpan] = None) -> None:
        location = f" at {span.line}:{span.column}" if span else ""
        super().__init__(f"{message}{location}")
        self.span = span


class BrewReturn(Exception):
    def __init__(self, value: Any) -> None:
        super().__init__("return")
        self.value = value


class BrewThrow(Exception):
    def __init__(self, value: Any, span: Optional[SourceSpan]) -> None:
        super().__init__("throw")
        self.value = value
        self.span = span


@dataclass
class FunctionValue:
    name: Optional[str]
    params: list[str]
    body: list
    closure: "Environment"
    span: SourceSpan

    def __call__(self, interpreter: "Interpreter", args: list[Any]) -> Any:
        if len(args) != len(self.params):
            raise BrewRuntimeError(
                f"Function '{self.name or '<anonymous>'}' expected {len(self.params)} args, got {len(args)}",
                self.span,
            )
        env = Environment(self.closure)
        for name, value in zip(self.params, args):
            env.define(name, value)
        try:
            interpreter.execute_block(self.body, env)
        except BrewReturn as exc:
            return exc.value
        return None


@dataclass
class NativeFunction:
    name: str
    arity: Optional[int]
    func: Callable[[list[Any]], Any]

    def __call__(self, args: list[Any]) -> Any:
        if self.arity is not None and len(args) != self.arity:
            raise BrewRuntimeError(
                f"Native '{self.name}' expected {self.arity} args, got {len(args)}",
            )
        return self.func(args)


class Environment:
    def __init__(self, parent: Optional["Environment"] = None) -> None:
        self.values: Dict[str, Any] = {}
        self.parent = parent

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign(self, name: str, value: Any) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise BrewRuntimeError(f"Undefined variable '{name}'")

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        raise BrewRuntimeError(f"Undefined variable '{name}'")


class Clock:
    @staticmethod
    def now() -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Interpreter:  # forward for type checking
    pass
