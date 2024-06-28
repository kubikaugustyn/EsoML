#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from typing import Iterator
from kutil.language import Parser, Options
from kutil.language.Token import TokenOutput, Token
from kutil.language.AST import AST, ASTNode

from esoml.tokens import *
from esoml.nodes import *


class EsoMLParser(Parser):
    def parseInner(self, tokens: TokenOutput, options: Options) -> AST:
        ast: AST = AST()

        while True:
            token = tokens.nextTokenDef(default=None)
            if token is None:
                break

            if token.kind == TokenKind.SECTION_START:
                assert isinstance(token, SectionStartToken)

                out: TokenOutput = TokenOutput()
                iterator = self.iterUntilToken(tokens, TokenKind.SECTION_END, True, False)
                out.setIterator(iterator)

                if token.section.kind is SectionKind.UNSAFE_MODE:
                    # Exhaust the tokens just to make sure
                    i = iter(out)
                    while next(i, None) is not None:
                        continue
                    continue

                section: Section = token.section
                node = self.parseSection(ast, out, section)
                ast.addRootNode(ast.addNode(node))

        return ast

    def iterUntilToken(self, tokens: TokenOutput, tokenKind: TokenKind, allowEnd: bool,
                       yieldEnd: bool) -> Iterator[Token]:
        while True:
            token = tokens.nextTokenDef(default=None)
            if token is None:
                if not allowEnd:
                    # raise ValueError("Reached the end of the token stream, which is not allowed")
                    raise ValueError(f"No matching closing token of kind: {tokenKind.name}")
                break

            if token.kind is tokenKind:
                if yieldEnd:
                    yield token
                break

            yield token

    def parseSection(self, ast: AST, tokens: TokenOutput, section: Section) -> ASTNode:
        if section.kind is SectionKind.STRINGS:
            return self.parseStringsSection(ast, tokens, section)
        elif section.kind in {SectionKind.CODE, SectionKind.RENDER}:
            print(f"Section {ascii(section.argument)}: "
                  f"{'call' if section.kind is SectionKind.CODE else 'render'} only")
            return self.parseCodeSection(ast, tokens, section)
        elif section.kind is SectionKind.ROM:
            return self.parseROMSection(ast, tokens, section)
        else:
            raise NotImplementedError(section.kind.name)

    # STRINGS
    def parseStringsSection(self, ast: AST, tokens: TokenOutput,
                            section: Section) -> SectionStringsNode:
        root = SectionStringsNode(section.argument)

        print(f"Strings for the locale {section.argument}:")
        for token in tokens:
            if token.kind is TokenKind.SECTION_END:
                continue

            assert token.kind is TokenKind.STRING_ENTRY
            assert isinstance(token, StringEntryToken)

            root.children.append(ast.addNode(
                StringEntryNode(token.key, token.string)
            ))

            print(f"    {token.key} --> {ascii(token.string)}")

        return root

    # ROM
    def parseROMSection(self, ast: AST, tokens: TokenOutput, section: Section) -> SectionROMNode:
        root = SectionROMNode(section.argument)

        print(f"ROM for the locale {section.argument}:")
        for token in tokens:
            if token.kind is TokenKind.SECTION_END:
                continue

            assert token.kind is TokenKind.ROM_ENTRY
            assert isinstance(token, ROMEntryToken)

            root.children.append(ast.addNode(
                ROMEntryNode(token.key, token.number)
            ))

            print(f"    {token.key} --> {token.number}")

        return root

    # CODE
    def parseCodeSection(self, ast: AST, tokens: TokenOutput, section: Section) -> SectionCodeNode:
        container = self.parseContainerContents(ast, tokens, section, "root")

        root = SectionCodeNode(section.argument, section.kind is SectionKind.RENDER,
                               container.children)
        return root

    def parseIfStatement(self, ast: AST, tokens: TokenOutput, section: Section) -> IfStatementNode:
        container = self.parseContainerContents(ast, tokens, section, "if")

        ifStatement = IfStatementNode(container.children)
        return ifStatement

    def parseContainerContents(self, ast: AST, tokens: TokenOutput,
                               section: Section, element: str) -> ContainerNode:
        children: list[ASTNode] = []

        for token in tokens:
            if section.kind is not SectionKind.RENDER:
                if token.kind in rendererOnlyTokens:
                    raise ValueError(f"Prohibited use of a render-section-only "
                                     f"token {token.kind.name}")

            if token.kind in {TokenKind.END_CONTAINER, TokenKind.SECTION_END, TokenKind.END_IF}:
                break
            elif token.kind is TokenKind.START_CONTAINER:
                assert isinstance(token, StartContainerToken)

                # Nested iterUntilToken were broken because the top-level (first called)
                # iterUntilToken ended first instead of the last called one ending first as needed
                # .render bug
                # cont
                # cont a
                # econ
                # cont b
                # econ
                # econ
                # out: TokenOutput = TokenOutput()
                # iterator = self.iterUntilToken(tokens, TokenKind.END_CONTAINER, False, False)
                # out.setIterator(iterator)
                out = tokens

                if token.element in {"root", "if"}:
                    raise ValueError("Cannot use neither the root nor if element LOL")
                children.append(self.parseContainerContents(ast, out, section, token.element))
            elif token.kind is TokenKind.START_IF:
                assert isinstance(token, StartIfToken)
                children.append(self.parseIfStatement(ast, tokens, section))
            elif token.kind is TokenKind.ELEM:
                assert isinstance(token, ElemToken)
                children.append(ElemNode(token.element))
            elif token.kind in {TokenKind.TEXT, TokenKind.SHOW}:
                assert isinstance(token, (TextToken, ShowToken))
                children.append(RawValueNode(token.content, token.kind is TokenKind.SHOW))
            elif token.kind is TokenKind.CALL:
                assert isinstance(token, CallToken)
                children.append(CallNode(token.label))
            elif token.kind is TokenKind.STACK_PUSH:
                assert isinstance(token, StackPushToken)
                children.append(StackPushNode(token.content))
            elif token.kind is TokenKind.STACK_COPY:
                assert isinstance(token, StackCopyToken)
                children.append(StackCopyNode())
            elif token.kind is TokenKind.STACK_POP:
                assert isinstance(token, StackPopToken)
                children.append(StackPopNode())
            elif token.kind is TokenKind.STACK_SWAP:
                assert isinstance(token, StackSwapToken)
                children.append(StackSwapNode(token.offA, token.offB))
            elif token.kind is TokenKind.COMPARE:
                assert isinstance(token, CompareToken)
                children.append(CompareNode())
            elif token.kind is TokenKind.READ:
                assert isinstance(token, ReadToken)
                children.append(ReadNode())
            elif token.kind in {TokenKind.MATH_ADD, TokenKind.MATH_SUB, TokenKind.MATH_MUL,
                                TokenKind.MATH_DIV}:
                assert isinstance(token, (MathAddToken, MathSubToken, MathMulToken, MathDivToken))
                op: MathOpNode.Operation = {
                    TokenKind.MATH_ADD: MathOpNode.Operation.ADD,
                    TokenKind.MATH_SUB: MathOpNode.Operation.SUB,
                    TokenKind.MATH_MUL: MathOpNode.Operation.MUL,
                    TokenKind.MATH_DIV: MathOpNode.Operation.DIV,
                }[token.kind]
                children.append(MathOpNode(op))
            elif token.kind is TokenKind.ADD_EVENT_LISTENER:
                assert isinstance(token, AddEventListenerToken)
                children.append(AddEventListenerNode(token.event, token.listener))
            elif token.kind is TokenKind.RENDER:
                assert isinstance(token, RenderToken)
                children.append(RenderNode())
            else:
                raise ValueError(f"Unexpected token: {token.kind.name}")

        return ContainerNode(element, ast.addNodes(children))
