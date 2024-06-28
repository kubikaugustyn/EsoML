#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from kutil.language.Language import GenericLanguage  # Don't care it's not exported
from kutil.language import AST

from esoml.lexer import EsoMLLexer
from esoml.parser import EsoMLParser
from esoml.compiler import EsoMLCompiler, EsoMLCompiledFile
from esoml.types import EsoMLOptions


class EsoML(GenericLanguage):
    optionsClass = EsoMLOptions
    compiler: EsoMLCompiler

    def __init__(self):
        super().__init__(EsoMLLexer(), EsoMLParser())
        self.compiler = EsoMLCompiler()

    def compile(self, inputCode: str, options: EsoMLOptions) -> EsoMLCompiledFile:
        ast: AST = super().run(inputCode, options)
        return self.compileInner(ast, options)

    def run(self, inputCode: str, options: EsoMLOptions) -> \
            EsoMLCompiledFile:
        file = self.compile(inputCode, options)
        return file

    def compileInner(self, ast: AST, options: EsoMLOptions) -> EsoMLCompiledFile:
        return self.compiler.compile(ast, options)

    @staticmethod
    def name() -> str:
        return "EsoMarkupLanguage"
