from __future__ import annotations

from typing import List, Optional

from brewjs.ast_nodes import (
    ArrayLiteral,
    AssignExpr,
    BinaryExpr,
    BlockStmt,
    CallExpr,
    ExpressionStmt,
    FunctionExpr,
    Identifier,
    IfStmt,
    IndexExpr,
    Literal,
    MemberExpr,
    ObjectLiteral,
    Program,
    ReturnStmt,
    SourceSpan,
    ThrowStmt,
    TryStmt,
    UnaryExpr,
    VarDecl,
    WhileStmt,
)
from brewjs.lexer import Token


class ParseError(RuntimeError):
    pass


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.index = 0

    def parse(self) -> Program:
        statements = []
        while not self._check("EOF"):
            statements.append(self._statement())
        return Program(statements)

    def _statement(self):
        if self._match_keyword("obj"):
            return self._var_decl()
        if self._match_keyword("function"):
            return self._function_decl()
        if self._match_keyword("if"):
            return self._if_stmt()
        if self._match_keyword("while"):
            return self._while_stmt()
        if self._match_keyword("return"):
            return self._return_stmt()
        if self._match_keyword("try"):
            return self._try_stmt()
        if self._match_keyword("throw"):
            return self._throw_stmt()
        if self._match_punct("{"):
            return self._block_stmt()
        expr = self._expression()
        self._consume_optional(";")
        return ExpressionStmt(expr, expr.span)

    def _block_stmt(self) -> BlockStmt:
        span = self._previous().span
        statements = []
        while not self._check_punct("}") and not self._check("EOF"):
            statements.append(self._statement())
        self._consume_punct("}")
        return BlockStmt(statements, span)

    def _var_decl(self) -> VarDecl:
        name = self._consume_ident("Expected variable name after 'obj'")
        initializer = None
        if self._match_op("="):
            initializer = self._expression()
        self._consume_optional(";")
        return VarDecl(name.value, initializer, name.span)

    def _function_decl(self) -> VarDecl:
        name = self._consume_ident("Expected function name")
        expr = self._function_expr(name)
        self._consume_optional(";")
        return VarDecl(name.value, expr, name.span)

    def _if_stmt(self) -> IfStmt:
        condition = self._expression()
        self._consume_punct("{")
        then_branch = self._block_stmt()
        else_branch = None
        if self._match_keyword("else"):
            if self._match_keyword("if"):
                else_branch = self._if_stmt()
            elif self._match_punct("{"):
                else_branch = self._block_stmt()
            else:
                raise ParseError("Expected 'if' or block after else")
        return IfStmt(condition, then_branch, else_branch, condition.span)

    def _while_stmt(self) -> WhileStmt:
        condition = self._expression()
        self._consume_punct("{")
        body = self._block_stmt()
        return WhileStmt(condition, body, condition.span)

    def _return_stmt(self) -> ReturnStmt:
        if self._check_punct(";") or self._check("EOF") or self._check_punct("}"):
            value = None
        else:
            value = self._expression()
        self._consume_optional(";")
        span = value.span if value else self._previous().span
        return ReturnStmt(value, span)

    def _try_stmt(self) -> TryStmt:
        try_span = self._previous().span
        self._consume_punct("{")
        try_block = self._block_stmt()
        catch_name = None
        catch_block = None
        finally_block = None
        if self._match_keyword("catch"):
            name = self._consume_ident("Expected name after catch")
            catch_name = name.value
            self._consume_punct("{")
            catch_block = self._block_stmt()
        if self._match_keyword("finally"):
            self._consume_punct("{")
            finally_block = self._block_stmt()
        if not catch_block and not finally_block:
            raise ParseError("try must have catch or finally")
        return TryStmt(try_block, catch_name, catch_block, finally_block, try_span)

    def _throw_stmt(self) -> ThrowStmt:
        value = self._expression()
        self._consume_optional(";")
        return ThrowStmt(value, value.span)

    def _expression(self):
        return self._assignment()

    def _assignment(self):
        expr = self._or()
        if self._match_op("="):
            value = self._assignment()
            return AssignExpr(expr, value, expr.span)
        return expr

    def _or(self):
        expr = self._and()
        while self._match_op("||"):
            op = self._previous().value
            right = self._and()
            expr = BinaryExpr(expr, op, right, expr.span)
        return expr

    def _and(self):
        expr = self._equality()
        while self._match_op("&&"):
            op = self._previous().value
            right = self._equality()
            expr = BinaryExpr(expr, op, right, expr.span)
        return expr

    def _equality(self):
        expr = self._comparison()
        while self._match_ops("==", "!="):
            op = self._previous().value
            right = self._comparison()
            expr = BinaryExpr(expr, op, right, expr.span)
        return expr

    def _comparison(self):
        expr = self._term()
        while self._match_ops("<", "<=", ">", ">="):
            op = self._previous().value
            right = self._term()
            expr = BinaryExpr(expr, op, right, expr.span)
        return expr

    def _term(self):
        expr = self._factor()
        while self._match_ops("+", "-"):
            op = self._previous().value
            right = self._factor()
            expr = BinaryExpr(expr, op, right, expr.span)
        return expr

    def _factor(self):
        expr = self._unary()
        while self._match_ops("*", "/", "%"):
            op = self._previous().value
            right = self._unary()
            expr = BinaryExpr(expr, op, right, expr.span)
        return expr

    def _unary(self):
        if self._match_ops("!", "-"):
            op = self._previous().value
            right = self._unary()
            return UnaryExpr(op, right, right.span)
        return self._call()

    def _call(self):
        expr = self._primary()
        while True:
            if self._match_punct("("):
                args = []
                if not self._check_punct(")"):
                    args.append(self._expression())
                    while self._match_punct(","):
                        args.append(self._expression())
                paren = self._consume_punct(")")
                expr = CallExpr(expr, args, paren.span)
            elif self._match_op("."):
                name = self._consume_ident("Expected property name after '.'")
                expr = MemberExpr(expr, name.value, name.span)
            elif self._match_punct("["):
                index = self._expression()
                self._consume_punct("]")
                expr = IndexExpr(expr, index, index.span)
            else:
                break
        return expr

    def _primary(self):
        if self._match("NUMBER"):
            token = self._previous()
            value = float(token.value) if "." in token.value else int(token.value)
            return Literal(value, token.span)
        if self._match("STRING"):
            token = self._previous()
            return Literal(token.value, token.span)
        if self._match_keyword("true"):
            return Literal(True, self._previous().span)
        if self._match_keyword("false"):
            return Literal(False, self._previous().span)
        if self._match_keyword("null"):
            return Literal(None, self._previous().span)
        if self._match_punct("["):
            items = []
            if not self._check_punct("]"):
                items.append(self._expression())
                while self._match_punct(","):
                    items.append(self._expression())
            end = self._consume_punct("]")
            return ArrayLiteral(items, end.span)
        if self._match_punct("{"):
            pairs = []
            if not self._check_punct("}"):
                while True:
                    key = self._consume_ident("Expected identifier key in object literal")
                    self._consume_punct(":")
                    value = self._expression()
                    pairs.append((key.value, value))
                    if not self._match_punct(","):
                        break
            end = self._consume_punct("}")
            return ObjectLiteral(pairs, end.span)
        if self._match_keyword("function"):
            return self._function_expr(None)
        if self._match("IDENT"):
            token = self._previous()
            return Identifier(token.value, token.span)
        if self._match_punct("("):
            expr = self._expression()
            self._consume_punct(")")
            return expr
        token = self._peek()
        raise ParseError(f"Unexpected token {token.kind}:{token.value} at {token.span.line}:{token.span.column}")

    def _function_expr(self, name_token: Optional[Token]):
        name = name_token.value if name_token else None
        self._consume_punct("(")
        params = []
        if not self._check_punct(")"):
            params.append(self._consume_ident("Expected parameter name"))
            while self._match_punct(","):
                params.append(self._consume_ident("Expected parameter name"))
        self._consume_punct(")")
        self._consume_punct("{")
        body = self._block_stmt()
        return FunctionExpr(name, [p.value for p in params], body.statements, body.span)

    def _consume_optional(self, punct: str) -> None:
        if self._check_punct(punct):
            self._advance()

    def _match(self, kind: str) -> bool:
        if self._check(kind):
            self._advance()
            return True
        return False

    def _match_keyword(self, keyword: str) -> bool:
        if self._check("KEYWORD") and self._peek().value == keyword:
            self._advance()
            return True
        return False

    def _match_op(self, op: str) -> bool:
        if self._check("OP") and self._peek().value == op:
            self._advance()
            return True
        return False

    def _match_ops(self, *ops: str) -> bool:
        if self._check("OP") and self._peek().value in ops:
            self._advance()
            return True
        return False

    def _match_punct(self, punct: str) -> bool:
        if self._check("PUNCT") and self._peek().value == punct:
            self._advance()
            return True
        return False

    def _consume_ident(self, message: str) -> Token:
        if self._check("IDENT"):
            return self._advance()
        token = self._peek()
        raise ParseError(f"{message} at {token.span.line}:{token.span.column}")

    def _consume_punct(self, punct: str) -> Token:
        if self._check("PUNCT") and self._peek().value == punct:
            return self._advance()
        token = self._peek()
        raise ParseError(f"Expected '{punct}' at {token.span.line}:{token.span.column}")

    def _check(self, kind: str) -> bool:
        return self._peek().kind == kind

    def _check_punct(self, punct: str) -> bool:
        return self._check("PUNCT") and self._peek().value == punct

    def _advance(self) -> Token:
        token = self._peek()
        self.index += 1
        return token

    def _peek(self) -> Token:
        return self.tokens[self.index]

    def _previous(self) -> Token:
        return self.tokens[self.index - 1]
