from __future__ import annotations

from dataclasses import dataclass
from typing import List

from brewjs.ast_nodes import SourceSpan


KEYWORDS = {
    "obj",
    "function",
    "if",
    "else",
    "while",
    "return",
    "true",
    "false",
    "null",
    "try",
    "catch",
    "finally",
    "throw",
}


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    span: SourceSpan


class LexerError(RuntimeError):
    pass


class Lexer:
    def __init__(self, source: str) -> None:
        self.source = source
        self.length = len(source)
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while not self._is_at_end():
            self._skip_whitespace()
            if self._is_at_end():
                break
            start_line = self.line
            start_col = self.column
            ch = self._advance()
            if ch.isalpha() or ch == "_":
                ident = ch + self._consume_while(lambda c: c.isalnum() or c == "_")
                kind = "KEYWORD" if ident in KEYWORDS else "IDENT"
                tokens.append(Token(kind, ident, SourceSpan(start_line, start_col)))
                continue
            if ch.isdigit():
                num = ch + self._consume_while(lambda c: c.isdigit() or c == ".")
                tokens.append(Token("NUMBER", num, SourceSpan(start_line, start_col)))
                continue
            if ch == '"':
                value = ""
                while not self._is_at_end() and self._peek() != '"':
                    if self._peek() == "\\":
                        self._advance()
                        esc = self._advance()
                        escapes = {
                            "n": "\n",
                            "t": "\t",
                            "r": "\r",
                            '"': '"',
                            "\\": "\\",
                        }
                        value += escapes.get(esc, esc)
                    else:
                        value += self._advance()
                if self._is_at_end():
                    raise LexerError("Unterminated string literal")
                self._advance()
                tokens.append(Token("STRING", value, SourceSpan(start_line, start_col)))
                continue
            two = ch + self._peek()
            if two in {"==", "!=", "<=", ">=", "&&", "||"}:
                self._advance()
                tokens.append(Token("OP", two, SourceSpan(start_line, start_col)))
                continue
            if ch in {"+", "-", "*", "/", "%", "<", ">", "=", "!", ".", ",", ";", ":", "(", ")", "{", "}", "[", "]"}:
                kind = "OP" if ch in {"+", "-", "*", "/", "%", "<", ">", "=", "!", "."} else "PUNCT"
                tokens.append(Token(kind, ch, SourceSpan(start_line, start_col)))
                continue
            raise LexerError(f"Unexpected character '{ch}' at {start_line}:{start_col}")
        tokens.append(Token("EOF", "", SourceSpan(self.line, self.column)))
        return tokens

    def _skip_whitespace(self) -> None:
        while not self._is_at_end():
            ch = self._peek()
            if ch in {" ", "\r", "\t", "\n"}:
                self._advance()
                continue
            if ch == "/" and self._peek_next() == "/":
                self._advance()
                self._advance()
                while not self._is_at_end() and self._peek() != "\n":
                    self._advance()
                continue
            if ch == "/" and self._peek_next() == "*":
                self._advance()
                self._advance()
                while not self._is_at_end() and not (self._peek() == "*" and self._peek_next() == "/"):
                    self._advance()
                if self._is_at_end():
                    raise LexerError("Unterminated block comment")
                self._advance()
                self._advance()
                continue
            break

    def _consume_while(self, predicate) -> str:
        out = ""
        while not self._is_at_end() and predicate(self._peek()):
            out += self._advance()
        return out

    def _is_at_end(self) -> bool:
        return self.index >= self.length

    def _advance(self) -> str:
        ch = self.source[self.index]
        self.index += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self.source[self.index]

    def _peek_next(self) -> str:
        if self.index + 1 >= self.length:
            return "\0"
        return self.source[self.index + 1]
