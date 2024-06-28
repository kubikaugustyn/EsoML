#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from enum import Enum, unique, auto, StrEnum
from typing import Optional, Any

from kutil.language.AST import ASTNode

from esoml.tokens import ValueRef


@unique
class NodeType(Enum):
    # STRINGS
    SECTION_STRINGS = auto()
    STRING_ENTRY = auto()
    # ROM
    SECTION_ROM = auto()
    ROM_ENTRY = auto()
    # CODE
    SECTION_CODE = auto()
    CONTAINER = auto()
    ELEM = auto()
    RAW_VALUE = auto()
    CALL = auto()
    RENDER = auto()
    ADD_EVENT_LISTENER = auto()
    STACK_PUSH = auto()
    STACK_COPY = auto()
    STACK_POP = auto()
    STACK_SWAP = auto()
    COMPARE = auto()
    READ = auto()
    MATH_OP = auto()
    IF_STATEMENT = auto()


class LocalizedSectionNode(ASTNode):
    locale: str
    children: list[int]

    def __init__(self, kind: NodeType, locale: str):
        self.locale = locale
        self.children = []
        super().__init__(kind, (locale, self.children))


class LocalizedSectionEntryNode[TValue: Any](ASTNode):
    key: int
    value: TValue

    def __init__(self, kind: NodeType, key: int, value: TValue):
        super().__init__(kind, (key, value))
        self.key = key
        self.value = value


# STRINGS
class SectionStringsNode(LocalizedSectionNode):
    def __init__(self, locale: str):
        super().__init__(NodeType.SECTION_STRINGS, locale)


class StringEntryNode(LocalizedSectionEntryNode[str]):
    def __init__(self, key: int, value: str):
        super().__init__(NodeType.STRING_ENTRY, key, value)


# ROM
class SectionROMNode(LocalizedSectionNode):
    def __init__(self, locale: str):
        super().__init__(NodeType.SECTION_ROM, locale)


class ROMEntryNode(LocalizedSectionEntryNode[int]):
    def __init__(self, key: int, value: int):
        super().__init__(NodeType.ROM_ENTRY, key, value)


# CODE
class SectionCodeNode(ASTNode):
    label: str
    isRender: bool
    children: list[int]

    def __init__(self, label: str, isRender: bool, children: list[int]):
        super().__init__(NodeType.SECTION_CODE, (label, isRender, children))
        self.label = label
        self.isRender = isRender
        self.children = children


class ContainerNode(ASTNode):
    element: Optional[str]
    children: list[int]

    def __init__(self, element: Optional[str], children: list[int]):
        super().__init__(NodeType.CONTAINER, (element, children))
        self.element = element
        self.children = children


class ElemNode(ASTNode):
    element: str

    def __init__(self, element: str):
        super().__init__(NodeType.ELEM, element)
        self.element = element


class RawValueNode(ASTNode):
    value: ValueRef  # Reference to the value in the string table
    injectRaw: bool  # Set with innerText (False) or innerHTML (True)

    def __init__(self, value: ValueRef, injectRaw: bool):
        super().__init__(NodeType.RAW_VALUE, (value, injectRaw))
        self.value = value
        self.injectRaw = injectRaw


class CallNode(ASTNode):
    label: str

    def __init__(self, label: str):
        super().__init__(NodeType.CALL, label)
        self.label = label


class RenderNode(ASTNode):
    def __init__(self):
        super().__init__(NodeType.RENDER, None)


class AddEventListenerNode(ASTNode):
    event: str  # The event type
    listener: str  # A label to the listener

    def __init__(self, event: str, listener: str):
        super().__init__(NodeType.ADD_EVENT_LISTENER, (event, listener))
        self.event = event
        self.listener = listener


class StackPushNode(ASTNode):
    value: ValueRef

    def __init__(self, value: ValueRef):
        super().__init__(NodeType.STACK_PUSH, value)
        self.value = value


class StackCopyNode(ASTNode):
    def __init__(self):
        super().__init__(NodeType.STACK_COPY, None)


class StackPopNode(ASTNode):
    def __init__(self):
        super().__init__(NodeType.STACK_POP, None)


class StackSwapNode(ASTNode):
    offA: int
    offB: int

    def __init__(self, offA: int, offB: int):
        super().__init__(NodeType.STACK_SWAP, (offA, offB))
        self.offA = offA
        self.offB = offB


class CompareNode(ASTNode):
    def __init__(self):
        super().__init__(NodeType.COMPARE, None)


class ReadNode(ASTNode):
    def __init__(self):
        super().__init__(NodeType.READ, None)


class MathOpNode(ASTNode):
    @unique
    class Operation(StrEnum):
        ADD = "+"
        SUB = "-"
        MUL = "*"
        DIV = "//"

    operation: Operation

    def __init__(self, operation: Operation):
        super().__init__(NodeType.MATH_OP, operation)
        self.operation = operation


class IfStatementNode(ASTNode):
    children: list[int]

    def __init__(self, children: list[int]):
        super().__init__(NodeType.IF_STATEMENT, children)
        self.children = children
