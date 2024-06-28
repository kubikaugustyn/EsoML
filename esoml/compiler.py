#  -*- coding: utf-8 -*-
__author__ = "kubik.augustyn@post.cz"

from kutil import readFile
from kutil.language.Error import CompilerError
from esoml.types import EsoMLOptions
from kutil.language.AST import AST
from jsbeautifier import beautify

from esoml.nodes import *


class EsoMLCompiledFile:
    unsafeMode: bool
    strings: dict[int, str]
    rom: dict[int, int]
    currentID: int
    codeSections: dict[str, str]
    codeSectionsRenderable: dict[str, bool]

    def __init__(self, unsafeMode: bool) -> None:
        self.unsafeMode = unsafeMode
        self.strings = {}
        self.rom = {}
        self.currentID = 0
        self.codeSections = {}
        self.codeSectionsRenderable = {}

    def id(self) -> str:
        self.currentID += 1
        return hex(self.currentID)

    def exportStrings(self) -> str:
        return self.exportConstants(self.strings, "strings")

    def exportROM(self) -> str:
        return self.exportConstants(self.rom, "rom")

    def exportConstants(self, constants: dict[int, Any], func: str) -> str:
        result: list[str] = []
        for key, string in constants.items():
            result.append(f"[{hex(key)},{ascii(string)}]")
        return func + "([" + ",".join(result) + "])"

    def exportCodes(self) -> str:
        result: list[str] = []
        for label, compiled in self.codeSections.items():
            renderable: bool = self.codeSectionsRenderable[label]
            result.append(f"code({ascii(label)},!{'0' if renderable else '1'},()=>{{{compiled}}})")
        return ";".join(result)

    def exportUnsafeMode(self) -> str:
        return f"setUnsafeMode(!{'0' if self.unsafeMode else '1'})"

    def export(self) -> str:
        from os.path import dirname, abspath, join
        lib = readFile(join(dirname(abspath(__file__)), "lib.js"), "text")
        code = f'{self.exportUnsafeMode()};{self.exportStrings()};{self.exportROM()};{self.exportCodes()};'
        # beautify = lambda code: code # Uncomment to temporarily disable the beautifier
        return beautify(lib.replace(r"// EsoML COMPILED CODE", code))


class EsoMLCompiler:
    def compile(self, ast: AST, options: EsoMLOptions) -> EsoMLCompiledFile:
        locale: str = options.getCompilerOptions().locale
        unsafeMode: bool = options.getCompilerOptions().unsafeMode
        file: EsoMLCompiledFile = EsoMLCompiledFile(unsafeMode)
        print("Compiling with these compiler options:", repr(options.getCompilerOptions()))
        print(f"Compiling with the locale set to {locale} with unsafe mode set to {unsafeMode}")

        self.compileConstants(ast, locale, NodeType.SECTION_STRINGS, SectionStringsNode,
                              StringEntryNode, file.strings, "strings")
        self.compileConstants(ast, locale, NodeType.SECTION_ROM, SectionROMNode, ROMEntryNode,
                              file.rom, "rom")
        self.compileCodeSections(ast, file)

        # for label, code in file.codeSections.items():
        #     print(label + ":")
        #     print(code)

        return file

    def compileConstants(self, ast: AST, locale: str, section: NodeType,
                         sectionNodeType: type[LocalizedSectionNode],
                         entryType: type[LocalizedSectionEntryNode], targetMap: dict,
                         kind: str) -> None:
        hasLocale: bool = False

        for root in ast.rootNodes():
            if root.type is not section:
                continue
            assert isinstance(root, sectionNodeType)
            if root.locale != locale:
                continue
            if hasLocale:
                # Ik, only checks for the current locale redefinition, but that's fine
                raise CompilerError(ValueError(f"The current locale {locale} was already defined"))
            hasLocale = True
            for node in ast.getNodes(root.children):
                assert isinstance(node, entryType)
                if node.key in targetMap:
                    raise CompilerError(KeyError(f"The {kind} map key {node.key} is already defined"
                                                 f" with a value {targetMap[node.key]}"))
                targetMap[node.key] = node.value
        if not hasLocale:
            raise CompilerError(ValueError(f'No {kind} section for {locale=} found in the program'))

    def compileCodeSections(self, ast: AST, file: EsoMLCompiledFile) -> None:
        hasMain: bool = False
        for root in ast.rootNodes():
            if root.type is not NodeType.SECTION_CODE:
                continue
            assert isinstance(root, SectionCodeNode)
            if root.label == "main":
                hasMain = True
            file.codeSections[root.label] = self.compileNode(ast, root, file)
            file.codeSectionsRenderable[root.label] = root.isRender
        if not hasMain:
            raise CompilerError(ValueError(f'No "main" code section found in the program'))

    def compileNode(self, ast: AST, node: ASTNode, file: EsoMLCompiledFile) -> str:
        if node.type is NodeType.SECTION_CODE:
            assert isinstance(node, SectionCodeNode)
            return self.compileContainerNode(ast, node, file)
        elif node.type is NodeType.CONTAINER:
            assert isinstance(node, ContainerNode)
            return self.compileContainerNode(ast, node, file)
        elif node.type is NodeType.IF_STATEMENT:
            assert isinstance(node, IfStatementNode)
            return self.compileIfStatementNode(ast, node, file)
        elif node.type is NodeType.ELEM:
            assert isinstance(node, ElemNode)
            return f"elem({file.id()},{ascii(node.element)})"
        elif node.type is NodeType.RAW_VALUE:
            assert isinstance(node, RawValueNode)
            return f"rawValue({file.id()},!{0 if node.injectRaw else 1},{node.value})"
        elif node.type is NodeType.CALL:
            assert isinstance(node, CallNode)
            return f"call({file.id()},{ascii(node.label)})"
        elif node.type is NodeType.RENDER:
            assert isinstance(node, RenderNode)
            return f"scheduleRender({file.id()})"
        elif node.type is NodeType.ADD_EVENT_LISTENER:
            assert isinstance(node, AddEventListenerNode)
            return f"eventListen({file.id()},{ascii(node.event)},{ascii(node.listener)})"
        elif node.type is NodeType.STACK_PUSH:
            assert isinstance(node, StackPushNode)
            return f"stackPush({file.id()},{node.value})"
        elif node.type is NodeType.STACK_COPY:
            assert isinstance(node, StackCopyNode)
            return f"stackCopy({file.id()})"
        elif node.type is NodeType.STACK_POP:
            assert isinstance(node, StackPopNode)
            return f"stackPop({file.id()})"
        elif node.type is NodeType.STACK_SWAP:
            assert isinstance(node, StackSwapNode)
            return f"stackSwap({file.id()},{node.offA},{node.offB})"
        elif node.type is NodeType.COMPARE:
            assert isinstance(node, CompareNode)
            return f"compare({file.id()})"
        elif node.type is NodeType.READ:
            assert isinstance(node, ReadNode)
            return f"read({file.id()})"
        elif node.type is NodeType.MATH_OP:
            assert isinstance(node, MathOpNode)
            return f"calc({file.id()},{ascii(node.operation.value)})"
        else:
            raise NotImplementedError(f"Cannot compile node of type {node.type.name}")

    def compileIfStatementNode(self, ast: AST, node: IfStatementNode,
                               file: EsoMLCompiledFile) -> str:
        result: list[str] = []
        for child in ast.getNodes(node.children):
            result.append(self.compileNode(ast, child, file))
        if_true: str = ";".join(result)
        return f"ifStatement({file.id()},()=>{{{if_true}}})"

    def compileContainerNode(self, ast: AST, node: ContainerNode | SectionCodeNode,
                             file: EsoMLCompiledFile) -> str:
        result: list[str] = []
        for child in ast.getNodes(node.children):
            result.append(self.compileNode(ast, child, file))
        renderer: str = ";".join(result)
        if isinstance(node, ContainerNode):
            element: str = ',' + ascii(node.element) if node.element is not None else ''
        else:
            element: str = ",'root'"
        return f"container({file.id()},()=>{{{renderer}}}{element})"
