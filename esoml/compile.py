#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from esoml.compiler import EsoMLCompiledFile

from esoml.language import EsoML

from esoml.types import EsoMLOptions

_lang: EsoML | None = None  # Reuse the instance


def compileEsoML(code: str, options: EsoMLOptions | None = None) -> EsoMLCompiledFile:
    global _lang
    if _lang is None:
        lang: EsoML = EsoML()
        _lang = lang
    else:
        lang: EsoML = _lang
    options: EsoMLOptions = options or EsoMLOptions()
    return lang.compile(code, options)
