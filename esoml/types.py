#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from kutil.language.Language import CompiledLanguageOptions  # Don't care it's not exported
from locale import getdefaultlocale


class CompilerOptions:
    locale: str
    unsafeMode: bool

    def __init__(self, locale: str | None = None, unsafeMode: bool = False) -> None:
        self.locale = locale if locale is not None else getdefaultlocale()[0]
        self.unsafeMode = unsafeMode

    def __repr__(self) -> str:
        return f"CompilerOptions(locale={self.locale}, unsafeMode={self.unsafeMode})"


class EsoMLOptions(CompiledLanguageOptions[None, None, CompilerOptions]):
    compilerOptions: CompilerOptions | None

    def __init__(self, locale: str | None = None, unsafeMode: bool = False) -> None:
        self.compilerOptions = CompilerOptions(locale, unsafeMode)

    def getLexerOptions(self) -> None:
        raise NotImplementedError

    def getParserOptions(self) -> None:
        raise NotImplementedError

    def getCompilerOptions(self) -> CompilerOptions:
        return self.compilerOptions

    def __repr__(self) -> str:
        return f"EsoMLOptions(compiler={repr(self.getCompilerOptions())})"
