#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from enum import StrEnum, Enum, unique, auto
from typing import Final

from kutil.language.Token import Token


@unique
class SectionKind(StrEnum):
    UNSAFE_MODE = "unsafe_mode"
    STRINGS = "strings"
    RENDER = "render"
    CODE = "code"
    ROM = "rom"


class Section:
    kind: SectionKind
    argument: str
    startsAtLine: int  # The line number of the first contained line!
    lines: list[str]

    def __repr__(self):
        return f"Section(kind={self.kind.name}, argument={self.argument}, line={self.startsAtLine})"


@unique
class TokenKind(Enum):
    SECTION_START = auto()
    SECTION_END = auto()
    # STRINGS
    STRING_ENTRY = auto()
    # ROM
    ROM_ENTRY = auto()
    # CODE
    START_CONTAINER = auto()
    END_CONTAINER = auto()
    ELEM = auto()
    SHOW = auto()
    TEXT = auto()
    CALL = auto()
    RENDER = auto()
    ADD_EVENT_LISTENER = auto()
    STACK_PUSH = auto()
    STACK_COPY = auto()
    STACK_POP = auto()
    STACK_SWAP = auto()
    COMPARE = auto()
    READ = auto()
    MATH_ADD = auto()
    MATH_SUB = auto()
    MATH_MUL = auto()
    MATH_DIV = auto()
    START_IF = auto()
    END_IF = auto()


rendererOnlyTokens: Final[set[TokenKind]] = {
    TokenKind.ELEM, TokenKind.SHOW, TokenKind.TEXT, TokenKind.START_CONTAINER,
    TokenKind.END_CONTAINER, TokenKind.ADD_EVENT_LISTENER
}


class ValueRef:
    @unique
    class ValueRefKind(StrEnum):
        STRING = 't'
        CONSTANT = 'c'
        STACK = 's'

    kind: ValueRefKind
    key: int

    def __init__(self, strVersion: str):
        self.parse(strVersion)

    def __str__(self):
        func: str = {
            ValueRef.ValueRefKind.STRING: 'getString',
            ValueRef.ValueRefKind.CONSTANT: 'getConstant',
            ValueRef.ValueRefKind.STACK: 'getStack',
        }[self.kind]
        return f"{func}({hex(self.key)})"

    def parse(self, strVersion: str):
        try:
            self.kind = ValueRef.ValueRefKind(strVersion[-1])
            self.key = int(strVersion[:-1])
        except (ValueError, TypeError, IndexError):
            from kutil.language.Error import LexerError
            raise LexerError(ValueError(f"Failed to parse a value reference {ascii(strVersion)}"))


class SectionStartToken(Token):
    section: Section

    def __init__(self, kind: Section):
        super().__init__(TokenKind.SECTION_START, kind)
        self.section = kind


class SectionEndToken(Token):
    def __init__(self):
        super().__init__(TokenKind.SECTION_END, None)


# STRINGS
class StringEntryToken(Token):
    key: int
    string: str

    def __init__(self, key: int, string: str):
        super().__init__(TokenKind.STRING_ENTRY, (key, string))
        self.key = key
        self.string = string


# ROM
class ROMEntryToken(Token):
    key: int
    number: int

    def __init__(self, key: int, number: int):
        super().__init__(TokenKind.ROM_ENTRY, (key, number))
        self.key = key
        self.number = number


# CODE
class StartContainerToken(Token):
    element: str | None

    def __init__(self, element: str | None):
        super().__init__(TokenKind.START_CONTAINER, element)
        self.element = element


class EndContainerToken(Token):
    def __init__(self):
        super().__init__(TokenKind.END_CONTAINER, None)


class ElemToken(Token):
    element: str

    def __init__(self, element: str):
        super().__init__(TokenKind.ELEM, element)
        self.element = element


class CallToken(Token):
    label: str  # Reference to the code section to be called

    def __init__(self, label: str):
        super().__init__(TokenKind.CALL, label)
        self.label = label


class ShowToken(Token):
    content: ValueRef

    def __init__(self, content: ValueRef):
        super().__init__(TokenKind.SHOW, content)


class TextToken(Token):
    content: ValueRef

    def __init__(self, content: ValueRef):
        super().__init__(TokenKind.TEXT, content)


class RenderToken(Token):
    def __init__(self):
        super().__init__(TokenKind.RENDER, None)


class AddEventListenerToken(Token):
    event: str  # The event type
    listener: str  # A label to the listener

    def __init__(self, event: str, listener: str):
        super().__init__(TokenKind.ADD_EVENT_LISTENER, (event, listener))
        self.event = event
        self.listener = listener


class StackPushToken(Token):
    content: ValueRef

    def __init__(self, content: ValueRef):
        super().__init__(TokenKind.STACK_PUSH, content)


class StackCopyToken(Token):
    def __init__(self):
        super().__init__(TokenKind.STACK_COPY, None)


class StackPopToken(Token):
    def __init__(self):
        super().__init__(TokenKind.STACK_POP, None)


class StackSwapToken(Token):
    offA: int
    offB: int

    def __init__(self, offA: int, offB: int):
        super().__init__(TokenKind.STACK_SWAP, (offA, offB))
        self.offA = offA
        self.offB = offB


class CompareToken(Token):
    def __init__(self):
        super().__init__(TokenKind.COMPARE, None)


class ReadToken(Token):
    def __init__(self):
        super().__init__(TokenKind.READ, None)


class MathAddToken(Token):
    def __init__(self):
        super().__init__(TokenKind.MATH_ADD, None)


class MathSubToken(Token):
    def __init__(self):
        super().__init__(TokenKind.MATH_SUB, None)


class MathMulToken(Token):
    def __init__(self):
        super().__init__(TokenKind.MATH_MUL, None)


class MathDivToken(Token):
    def __init__(self):
        super().__init__(TokenKind.MATH_DIV, None)


class StartIfToken(Token):
    def __init__(self):
        super().__init__(TokenKind.START_IF, None)


class EndIfToken(Token):
    def __init__(self):
        super().__init__(TokenKind.END_IF, None)
