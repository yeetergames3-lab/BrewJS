from __future__ import annotations

import random
import threading
import time
from collections import deque
from typing import Any, Callable, Dict

from brewjs.runtime import BrewRuntimeError, NativeFunction


ANSI_COLORS = {
    "red": "\u001b[31m",
    "green": "\u001b[32m",
    "yellow": "\u001b[33m",
    "blue": "\u001b[34m",
    "magenta": "\u001b[35m",
    "cyan": "\u001b[36m",
    "gray": "\u001b[90m",
    "reset": "\u001b[0m",
}


def colorize(text: str, color: str) -> str:
    prefix = ANSI_COLORS.get(color.lower())
    if not prefix:
        return text
    return f"{prefix}{text}{ANSI_COLORS['reset']}"


def build_console() -> Dict[str, Any]:
    def log(args: list[Any]) -> None:
        if not args:
            print()
            return
        *rest, last = args
        color = None
        if isinstance(last, dict) and "color" in last:
            color = str(last.get("color"))
            args = rest + [last.get("text", "")]
        msg = " ".join(str(a) for a in args)
        if color:
            msg = colorize(msg, color)
        print(msg)

    def info(args: list[Any]) -> None:
        print(colorize(" ".join(str(a) for a in args), "cyan"))

    def warn(args: list[Any]) -> None:
        print(colorize(" ".join(str(a) for a in args), "yellow"))

    def error(args: list[Any]) -> None:
        print(colorize(" ".join(str(a) for a in args), "red"))

    return {
        "log": NativeFunction("console.log", None, log),
        "info": NativeFunction("console.info", None, info),
        "warn": NativeFunction("console.warn", None, warn),
        "error": NativeFunction("console.error", None, error),
        "colorize": NativeFunction("console.colorize", 2, lambda a: colorize(str(a[0]), str(a[1]))),
    }


def build_random() -> Dict[str, Any]:
    def randint(args: list[Any]) -> int:
        lo, hi = int(args[0]), int(args[1])
        if lo > hi:
            lo, hi = hi, lo
        return random.randint(lo, hi)

    def pick(args: list[Any]) -> Any:
        items = args[0]
        if not items:
            raise BrewRuntimeError("random.pick called with empty array")
        return random.choice(items)

    def char(args: list[Any]) -> str:
        start, end = str(args[0]), str(args[1])
        if len(start) != 1 or len(end) != 1:
            raise BrewRuntimeError("random.char expects single-character strings")
        return chr(random.randint(ord(start), ord(end)))

    return {
        "int": NativeFunction("random.int", 2, randint),
        "pick": NativeFunction("random.pick", 1, pick),
        "char": NativeFunction("random.char", 2, char),
    }


def build_string() -> Dict[str, Any]:
    return {
        "length": NativeFunction("string.length", 1, lambda a: len(str(a[0]))),
        "charAt": NativeFunction("string.charAt", 2, lambda a: str(a[0])[int(a[1])]),
        "upper": NativeFunction("string.upper", 1, lambda a: str(a[0]).upper()),
        "lower": NativeFunction("string.lower", 1, lambda a: str(a[0]).lower()),
        "slice": NativeFunction(
            "string.slice",
            3,
            lambda a: str(a[0])[int(a[1]) : int(a[2])],
        ),
        "split": NativeFunction("string.split", 2, lambda a: str(a[0]).split(str(a[1]))),
        "join": NativeFunction("string.join", 2, lambda a: str(a[1]).join(str(x) for x in a[0])),
        "indexOf": NativeFunction("string.indexOf", 2, lambda a: str(a[0]).find(str(a[1]))),
        "codePointAt": NativeFunction("string.codePointAt", 2, lambda a: ord(str(a[0])[int(a[1])])),
    }


def build_array() -> Dict[str, Any]:
    def length(args: list[Any]) -> int:
        return len(args[0])

    def contains(args: list[Any]) -> bool:
        arr, value = args
        return value in arr

    def shift(args: list[Any]) -> Any:
        arr = args[0]
        if not arr:
            return None
        return arr.pop(0)

    return {
        "length": NativeFunction("array.length", 1, length),
        "contains": NativeFunction("array.contains", 2, contains),
        "shift": NativeFunction("array.shift", 1, shift),
    }


def build_time() -> Dict[str, Any]:
    return {
        "now": NativeFunction("time.now", 0, lambda a: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    }


def build_file() -> Dict[str, Any]:
    def read(args: list[Any]) -> str:
        path = str(args[0])
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()

    def write(args: list[Any]) -> None:
        path, content = str(args[0]), str(args[1])
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return None

    def append(args: list[Any]) -> None:
        path, content = str(args[0]), str(args[1])
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(content)
        return None

    return {
        "read": NativeFunction("file.read", 1, read),
        "write": NativeFunction("file.write", 2, write),
        "append": NativeFunction("file.append", 2, append),
    }


def build_data() -> Dict[str, Any]:
    def queue(args: list[Any]) -> Dict[str, Any]:
        q: deque[Any] = deque()
        return {
            "push": NativeFunction("queue.push", 1, lambda a: q.append(a[0]) or None),
            "pop": NativeFunction("queue.pop", 0, lambda a: q.popleft() if q else None),
            "peek": NativeFunction("queue.peek", 0, lambda a: q[0] if q else None),
            "size": NativeFunction("queue.size", 0, lambda a: len(q)),
        }

    def stack(args: list[Any]) -> Dict[str, Any]:
        stack_list: list[Any] = []
        return {
            "push": NativeFunction("stack.push", 1, lambda a: stack_list.append(a[0]) or None),
            "pop": NativeFunction("stack.pop", 0, lambda a: stack_list.pop() if stack_list else None),
            "peek": NativeFunction("stack.peek", 0, lambda a: stack_list[-1] if stack_list else None),
            "size": NativeFunction("stack.size", 0, lambda a: len(stack_list)),
        }

    def set_factory(args: list[Any]) -> Dict[str, Any]:
        items = set(args)
        return {
            "add": NativeFunction("set.add", 1, lambda a: items.add(a[0]) or None),
            "has": NativeFunction("set.has", 1, lambda a: a[0] in items),
            "delete": NativeFunction("set.delete", 1, lambda a: items.discard(a[0]) or None),
            "size": NativeFunction("set.size", 0, lambda a: len(items)),
            "values": NativeFunction("set.values", 0, lambda a: list(items)),
        }

    def map_factory(args: list[Any]) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        return {
            "set": NativeFunction("map.set", 2, lambda a: data.__setitem__(str(a[0]), a[1]) or None),
            "get": NativeFunction("map.get", 1, lambda a: data.get(str(a[0]))),
            "has": NativeFunction("map.has", 1, lambda a: str(a[0]) in data),
            "delete": NativeFunction("map.delete", 1, lambda a: data.pop(str(a[0]), None)),
            "keys": NativeFunction("map.keys", 0, lambda a: list(data.keys())),
            "values": NativeFunction("map.values", 0, lambda a: list(data.values())),
        }

    return {
        "queue": NativeFunction("data.queue", 0, queue),
        "stack": NativeFunction("data.stack", 0, stack),
        "set": NativeFunction("data.set", None, set_factory),
        "map": NativeFunction("data.map", 0, map_factory),
    }


def build_thread() -> Dict[str, Any]:
    def run(args: list[Any]) -> Dict[str, Any]:
        fn = args[0]
        handle: dict[str, Any] = {"done": False, "result": None, "error": None}

        def target():
            try:
                handle["result"] = fn([])
            except Exception as exc:  # pragma: no cover - only on user failure
                handle["error"] = str(exc)
            handle["done"] = True

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        handle["join"] = NativeFunction("thread.join", 0, lambda a: thread.join() or handle.get("result"))
        return handle

    def sleep(args: list[Any]) -> None:
        time.sleep(float(args[0]) / 1000.0)

    return {
        "run": NativeFunction("thread.run", 1, run),
        "sleep": NativeFunction("thread.sleep", 1, sleep),
    }


def default_globals() -> Dict[str, Any]:
    return {
        "console": build_console(),
        "random": build_random(),
        "string": build_string(),
        "array": build_array(),
        "time": build_time(),
        "file": build_file(),
        "data": build_data(),
        "thread": build_thread(),
        "pauseExecution": NativeFunction("pauseExecution", 1, lambda a: time.sleep(float(a[0]) / 1000.0)),
    }
