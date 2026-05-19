"""Tiny FEEL-subset parser used by transition guards and gate decisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class FeelParseError(Exception):
    pass


@dataclass
class Node:
    kind: str
    children: list["Node"]
    value: Optional[str] = None


_TOKENS = ("(", ")", "==", "!=", ">=", "<=", ">", "<")


def _tokenize(expr: str) -> list[str]:
    tokens: list[str] = []
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch in ('"', "'"):
            quote = ch
            j = i + 1
            while j < len(expr) and expr[j] != quote:
                j += 1
            if j >= len(expr):
                raise FeelParseError(f"unterminated string at {i}")
            tokens.append(expr[i : j + 1])
            i = j + 1
            continue
        for token in _TOKENS:
            if expr.startswith(token, i):
                tokens.append(token)
                i += len(token)
                break
        else:
            j = i
            while j < len(expr) and (expr[j].isalnum() or expr[j] in "._-"):
                j += 1
            if j == i:
                raise FeelParseError(f"unexpected character {ch!r} at {i}")
            tokens.append(expr[i:j])
            i = j
    return tokens


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self) -> str:
        if self.pos >= len(self.tokens):
            raise FeelParseError("unexpected end of input")
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse_expr(self) -> Node:
        node = self.parse_or()
        if self.pos < len(self.tokens):
            raise FeelParseError(f"trailing tokens: {self.tokens[self.pos:]}")
        return node

    def parse_or(self) -> Node:
        left = self.parse_and()
        while self.peek() == "or":
            self.consume()
            right = self.parse_and()
            left = Node(kind="or", children=[left, right])
        return left

    def parse_and(self) -> Node:
        left = self.parse_not()
        while self.peek() == "and":
            self.consume()
            right = self.parse_not()
            left = Node(kind="and", children=[left, right])
        return left

    def parse_not(self) -> Node:
        if self.peek() == "not":
            self.consume()
            inner = self.parse_not()
            return Node(kind="not", children=[inner])
        return self.parse_primary()

    def parse_primary(self) -> Node:
        token = self.peek()
        if token is None:
            raise FeelParseError("unexpected end of input")
        if token == "(":
            self.consume()
            inner = self.parse_or()
            if self.peek() != ")":
                raise FeelParseError("expected ')'")
            self.consume()
            return inner
        if token in ("true", "false", "null"):
            self.consume()
            return Node(kind="literal", children=[], value=token)
        if token in ("defined", "undefined"):
            self.consume()
            if self.peek() != "(":
                raise FeelParseError(f"expected '(' after {token}")
            self.consume()
            ident_token = self.consume()
            if self.peek() != ")":
                raise FeelParseError(f"expected ')' after {token}({ident_token})")
            self.consume()
            return Node(kind="predicate", children=[], value=f"{token}({ident_token})")
        left = self.consume()
        op = self.peek()
        if op not in ("==", "!=", ">", "<", ">=", "<="):
            raise FeelParseError(f"expected comparison operator after {left!r}, got {op!r}")
        self.consume()
        right = self.consume()
        return Node(kind="comparison", children=[Node("ident", [], left), Node("operand", [], right)], value=op)


def parse(expr: str) -> Node:
    parser = _Parser(_tokenize(expr))
    return parser.parse_expr()


def idents_used(node: Node) -> set[str]:
    names: set[str] = set()

    def walk(n: Node) -> None:
        if n.kind == "predicate" and n.value:
            inside = n.value[n.value.index("(") + 1 : n.value.rindex(")")]
            names.add(inside.split(".")[0])
            return
        if n.kind == "comparison":
            ident_child = n.children[0]
            operand_child = n.children[1]
            names.add(ident_child.value.split(".")[0])
            if not _is_literal(operand_child.value):
                names.add(operand_child.value.split(".")[0])
            return
        for child in n.children:
            walk(child)

    def _is_literal(token: Optional[str]) -> bool:
        if token is None:
            return True
        if token in ("true", "false", "null"):
            return True
        if token[0] in ("'", '"'):
            return True
        try:
            float(token)
            return True
        except ValueError:
            return False

    walk(node)
    return names
