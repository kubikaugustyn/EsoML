#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from typing import Iterator
from kutil.language import Lexer
from kutil.language.Token import TokenOutput
from kutil.language.Error import LexerError

from esoml.tokens import *
from esoml.types import EsoMLOptions


# @formatter:off
@unique
class Instruction(Enum):
    START_CONTAINER =    "cont"  # Open a container
    END_CONTAINER =      "econ"  # Close a container
    ELEM =               "elem"  # Create an element without content
    TEXT =               "text"  # Show text
    SHOW =               "show"  # Inject raw HTML
    CALL =               "call"  # Call/inject another section
    RENDER =             "rend"  # Re-render the page
    ADD_EVENT_LISTENER = "hear"  # Listen for an event
    STACK_PUSH =         "push"  # Load a string/constant and push it to the stack
    STACK_COPY =         "copy"  # Duplicate the top stack value
    STACK_POP =          "pops"  # Pop a value from the stack, discarding it
    STACK_SWAP =         "swap"  # Swap the top 2 values of the stack
    COMPARE =            "comp"  # Pop A, then pop B from the stack and push A == B to the stack
    READ =               "read"  # Push the content of an element to the stack, then push its len()
    MATH_ADD =           "madd"  # Pop A, then pop B from the stack and push A + B to the stack
    MATH_SUB =           "msub"  # Pop A, then pop B from the stack and push A - B to the stack
    MATH_MULT =          "mmul"  # Pop A, then pop B from the stack and push A * B to the stack
    MATH_DIV =           "mdiv"  # Pop A, then pop B from the stack and push A // B to the stack
    START_IF =           "ifis"  # Pop A from the stack and execute the code only IF A == 1
    END_IF =             "endi"  # The end of an IF block
# @formatter:on


# Instruction --> Token that doesn't take any parameters
instructionToSimpleToken: Final[dict[Instruction, type[Token]]] = {
    Instruction.END_CONTAINER: EndContainerToken,
    Instruction.RENDER: RenderToken,
    Instruction.STACK_COPY: StackCopyToken,
    Instruction.STACK_POP: StackPopToken,
    Instruction.COMPARE: CompareToken,
    Instruction.READ: ReadToken,
    Instruction.MATH_ADD: MathAddToken,
    Instruction.MATH_SUB: MathSubToken,
    Instruction.MATH_MULT: MathMulToken,
    Instruction.MATH_DIV: MathDivToken,
    Instruction.START_IF: StartIfToken,
    Instruction.END_IF: EndIfToken,
}

# Instruction --> Token that takes 1 raw parameter
instructionTo1ArgToken: Final[dict[Instruction, type[Token]]] = {
    Instruction.START_CONTAINER: StartContainerToken,
    Instruction.ELEM: ElemToken,
    Instruction.CALL: CallToken,
}


class EsoMLLexer(Lexer):
    @staticmethod
    def convertIDToKey(id_str: str, line: int) -> int:
        id_: int = int(id_str, 8)
        line %= len(id_str)
        line %= 3
        if line == 0:
            return ((id_ * 3) << 2) + 0x42
        elif line == 1:
            return ((id_ ^ 1337) << 3) - 5
        elif line == 2:
            return ((id_ // 7) % 0x69) + 666
        else:
            raise NotImplementedError("Huh? Math is failing?")

    def tokenizeInner(self, inputCode: str, options: EsoMLOptions, output: TokenOutput) -> \
            Iterator[Token]:
        codeLines: list[str] = inputCode.splitlines(keepends=False)
        lineNumber: int = 1
        sections: list[Section] = []

        while lineNumber <= len(codeLines):
            line = codeLines[lineNumber - 1]
            if not line:
                lineNumber += 1
                continue
            if not line.startswith("."):
                self.error("The code must start with a section", lineNumber)
            section = Section()
            if " " not in line:
                self.error("The section header must contain an argument", lineNumber)
            kind, section.argument = line[1:].split(" ", maxsplit=1)
            section.kind = SectionKind(kind)
            lineNumber += 1
            section.startsAtLine = lineNumber
            lines = section.lines = []
            yield SectionStartToken(section)
            if section.kind is SectionKind.UNSAFE_MODE:
                options.getCompilerOptions().unsafeMode = True
            while lineNumber <= len(codeLines):
                if section.kind is SectionKind.UNSAFE_MODE:
                    break

                line = codeLines[lineNumber - 1]
                if not line:
                    lineNumber += 1
                    continue
                if line.startswith("."):
                    break

                yield from self.tokenizeSectionLine(section, line, lineNumber)

                lines.append(line)
                lineNumber += 1
            yield SectionEndToken()
            sections.append(section)

    def tokenizeSectionLine(self, section: Section, line: str, lineNumber: int) -> Iterator[Token]:
        try:
            if section.kind is SectionKind.STRINGS:
                yield from self.tokenizeStringsSectionLine(line, lineNumber, section)
            elif section.kind in {SectionKind.CODE, SectionKind.RENDER}:
                yield from self.tokenizeCodeSectionLine(line, lineNumber)
            elif section.kind is SectionKind.ROM:
                yield from self.tokenizeROMSectionLine(line, lineNumber, section)
            else:
                raise NotImplementedError(f"Unknown section kind: {section.kind.name}")
        except Exception as e:
            raise LexerError([
                e,
                Exception(f"An error occurred at line {lineNumber}, see the above log")
            ])

    def tokenizeStringsSectionLine(self, line: str, lineNumber: int, section: Section) -> \
            Iterator[Token]:
        LET = "Let "
        EQUALS = " be translated to "

        if not line.startswith(LET) or EQUALS not in line or not line.endswith("."):
            self.error("Invalid string", lineNumber)
        idEnd: int = line.index(" ", len(LET))
        key = self.convertIDToKey(line[len(LET):idEnd], lineNumber - section.startsAtLine)
        value = line[idEnd + len(EQUALS):-1]
        yield StringEntryToken(key, value)

    def tokenizeROMSectionLine(self, line: str, lineNumber: int, section: Section) -> Iterator[
        Token]:
        CONST = "Remember that "
        EQUALS = " will always be "

        if not line.startswith(CONST) or EQUALS not in line or not line.endswith("."):
            self.error("Invalid ROM entry", lineNumber)
        idEnd: int = line.index(" ", len(CONST))
        key = self.convertIDToKey(line[len(CONST):idEnd], lineNumber - section.startsAtLine)
        value = int(line[idEnd + len(EQUALS):-1], 11)
        yield ROMEntryToken(key, value)

    def tokenizeCodeSectionLine(self, line: str, lineNumber: int) -> Iterator[Token]:
        instructionStr, *arguments = line.split(" ")
        instruction = Instruction(instructionStr)

        try:
            if instruction is Instruction.START_CONTAINER:
                yield StartContainerToken(arguments[0] if len(arguments) >= 1 else None)
            elif instruction in instructionToSimpleToken:
                # Just to simplify the process, ignore type errors
                yield instructionToSimpleToken[instruction]()
            elif instruction in instructionTo1ArgToken:
                # Just to simplify the process, ignore type errors
                yield instructionTo1ArgToken[instruction](arguments[0])
            elif instruction is Instruction.TEXT:
                yield TextToken(ValueRef(arguments[0]))
            elif instruction is Instruction.SHOW:
                yield ShowToken(ValueRef(arguments[0]))
            elif instruction is Instruction.STACK_PUSH:
                yield StackPushToken(ValueRef(arguments[0]))
            elif instruction is Instruction.STACK_SWAP:
                offA: int = int(arguments[0]) if len(arguments) >= 1 else 0
                offB: int = int(arguments[1]) if len(arguments) >= 2 else 1
                offA, offB = max(offA, 0), max(offB, 0)  # Must be >= 0
                yield StackSwapToken(offA, offB)
            elif instruction is Instruction.ADD_EVENT_LISTENER:
                yield AddEventListenerToken(arguments[0], arguments[1])
            else:
                raise NotImplementedError(f"Unknown instruction: {instruction.name}")
        except IndexError as e:
            raise IndexError(f"Argument index out of range. Check whether you've provided enough"
                             f" arguments to the instruction {instruction}") from e

    def error(self, message: str, lineNumber: int):
        raise LexerError(ValueError(message + " on line " + str(lineNumber)))
