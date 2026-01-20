from __future__ import annotations

import argparse
import sys

from brewjs.interpreter import Interpreter
from brewjs.lexer import Lexer, LexerError
from brewjs.parser import ParseError, Parser
from brewjs.runtime import BrewRuntimeError


def run(source: str) -> int:
    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        Interpreter().interpret(program)
    except (LexerError, ParseError, BrewRuntimeError) as exc:
        print(f"BrewJS error: {exc}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="BrewJS interpreter")
    parser.add_argument("path", help="BrewJS source file")
    args = parser.parse_args()
    try:
        with open(args.path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except FileNotFoundError:
        print(f"File not found: {args.path}")
        return 1
    return run(source)


if __name__ == "__main__":
    sys.exit(main())
