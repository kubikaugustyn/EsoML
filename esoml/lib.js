const __author__ = "kubik.augustyn@post.cz"

class CallID {
    /**
     * @type {Map<number|symbol, CallID>}
     */
    static INSTANCES = new Map()

    /**
     * @type {number|symbol}
     */
    id

    /**
     * @param id {number|symbol}
     */
    constructor(id) {
        this.id = id;
    }

    toString() {
        return this.id.toString()
    }

    /**
     * @param id {number|symbol|CallID}
     * @return {CallID}
     */
    static from(id) {
        if (id instanceof CallID) return id
        else if (CallID.INSTANCES.has(id)) return CallID.INSTANCES.get(id)

        const newID = new CallID(id)
        CallID.INSTANCES.set(id, newID)
        return newID
    }
}

class CodeSection {
    /**
     * @type {string|symbol}
     */
    label
    /**
     * @type {boolean}
     */
    isRenderable
    /**
     * @type {function(): void}
     */
    rendererOrCallee

    /**
     * @param label {string|symbol}
     * @param isRenderable {boolean}
     * @param rendererOrCallee {function(): void}
     */
    constructor(label, isRenderable, rendererOrCallee) {
        this.label = label
        this.isRenderable = isRenderable
        this.rendererOrCallee = rendererOrCallee

        /*if (isRenderable) {
            log.info("Renderable", label, rendererOrCallee)
        } else {
            log.info("Callable", label, rendererOrCallee)
        }*/
    }
}

class RenderingStackEntry {
    /**
     * @type {CallID}
     */
    id
    /**
     * @type {CodeSection}
     */
    code
    /**
     * @type {HTMLElement}
     */
    element
    /**
     * @type {symbol}
     */
    kind

    /**
     * @param id {CallID}
     * @param code {CodeSection}
     * @param element {HTMLElement}
     * @param kind {symbol}
     */
    constructor(id, code, element, kind) {
        this.id = id
        this.code = code
        this.element = element
        this.kind = kind
    }
}

const root = Symbol("ROOT")
const rootID = new CallID(-1)
const MUST_BE_RENDERABLE = Symbol("MUST_BE_RENDERABLE")
const MUST_BE_CALLABLE = Symbol("MUST_BE_CALLABLE")
const CAN_BE_ANY = Symbol("CAN_BE_ANY")
const CONTAINER_KIND = Symbol("CONTAINER_KIND")
const IF_STATEMENT_KIND = Symbol("IF_STATEMENT_KIND")
const RERENDER_TIMEOUT = 100
const MAX_RE_RENDERS_PER_SECOND = 5

const log = {
    info: (...args) => !unsafeMode && console.log(...args),
    error: (...args) => !unsafeMode && console.error(...args),
    group: (...args) => !unsafeMode && console.group(...args),
    groupCollapsed: (...args) => !unsafeMode && console.groupCollapsed(...args),
    groupEnd: () => !unsafeMode && console.groupEnd(),
}

/**
 * @type {boolean}
 */
let unsafeMode = false
/**
 * @type {Map<number, string>}
 */
let stringMap = new Map()
/**
 * @type {Map<number, number>}
 */
let ROMMap = new Map()
/**
 * @type {Map<string, CodeSection>}
 */
let codeMap = new Map()
/**
 * @type {RenderingStackEntry[]}
 */
let renderingStack = []
/**
 * @type {CodeSection}
 */
let currentCodeSection = null
/**
 * @type {(number|string)[]}
 */
let valueStack = []
/**
 * @type {symbol}
 */
let currentCodeType = CAN_BE_ANY
/**
 * @type {boolean}
 */
let shouldRerender = false
/**
 * @type {number}
 */
let scheduledRendersWhileRendering = 0
/**
 * @type {HTMLElement|null}
 */
let currentTarget = null

function container(id_, renderer, tag = null) {
    const id = CallID.from(id_)
    if (!currentCodeSection.isRenderable || currentCodeType === MUST_BE_CALLABLE) {
        renderer()
        return
    }

    const info = new RenderingStackEntry(
        id,
        currentCodeSection,
        document.createElement(tag || "div"),
        CONTAINER_KIND
    )
    info.element.setAttribute("x-id", "container-".concat(id.toString()))
    renderingStack.push(info)
    const oldTarget = currentTarget
    currentTarget = info.element;
    (tag === "root" ? log.group : log.groupCollapsed)("Container:", id, tag || "div")
    log.info("Info:", info)
    renderer()
    renderingStack.pop()
    currentTarget = oldTarget
    log.groupEnd()

    const container = renderingStack[renderingStack.length - 1].element
    if (tag !== "root") container.appendChild(info.element)
    else {
        // Array.from is used because when you add the child to a different element, it is removed from the current
        // element, causing a change of info.element.children to not include the already iterated child
        for (const child of Array.from(info.element.children))
            container.appendChild(child)
    }
}

function elem(id_, tag) {
    const id = CallID.from(id_)
    log.info("Elem:", id, tag)

    const container = renderingStack[renderingStack.length - 1].element
    const elem = document.createElement(tag)
    elem.setAttribute("x-id", "elem-".concat(id))
    container.appendChild(elem)
}

function call(id_, label, type = CAN_BE_ANY) {
    const id = CallID.from(id_)
    if (!codeMap.has(label)) throw new Error("Cannot call an undefined section")
    const code = codeMap.get(label);
    (type === MUST_BE_CALLABLE ? log.group : log.info)("Call:", code)
    if ((type === MUST_BE_RENDERABLE && renderingStack[renderingStack.length - 1].code.isRenderable !== code.isRenderable) ||
        (type !== CAN_BE_ANY && (type === MUST_BE_RENDERABLE ? !code.isRenderable : code.isRenderable)))
        throw new Error("Cannot directly call renderable code from a non-renderable section and vice versa")


    const oldType = currentCodeType
    const oldSection = currentCodeSection
    currentCodeType = type
    currentCodeSection = code

    code.rendererOrCallee()

    currentCodeType = oldType
    currentCodeSection = oldSection
    if (type === MUST_BE_CALLABLE) log.groupEnd()
}

function eventListen(id_, type, listener) {
    const id = CallID.from(id_)
    log.info("Event listener:", id, type, listener)
    const container = renderingStack[renderingStack.length - 1].element
    container.addEventListener(type, e => {
        const oldTarget = currentTarget
        currentTarget = e.target
        try {
            call(id, listener, MUST_BE_CALLABLE)
        } catch (e) {
            renderError(e)
        } finally {
            currentTarget = oldTarget
        }
    })
}

function calc(id_, op) {
    const id = CallID.from(id_)
    log.groupCollapsed("Calculate:", id, op)
    const A = stackPop(id)
    const B = stackPop(id)
    log.info(`Operation: result = ${A} ${op} ${B}`)
    let result
    switch (op) {
        case "+":
            result = A + B
            break
        case "-":
            result = A - B
            break
        case "*":
            result = A * B
            break
        case "//":
            result = Math.floor(A / B)
            break
        default:
            throw new Error("Unknown operator: " + op)
    }
    stackPush(id, result)
    log.info(`Result: ${A} ${op} ${B} = ${result}`)
    log.groupEnd()
}

function checkStackVal(val) {
    if (typeof val === "string") return
    if (typeof val === "number") {
        if (val < Number.MIN_SAFE_INTEGER || val > Number.MAX_SAFE_INTEGER)
            throw new Error(`Cannot have a value on the stack that is out of bounds: ${val}`)
        return
    }
    throw new Error(`Cannot have a value on the stack that is of an unknown type: ${val}`)
}

function checkStackOff(off) {
    if (off < 0 || valueStack.length <= off) throw new Error(`Stack offset ${off} out of bounds`)
}

function getStackIndex(off) {
    return valueStack.length - 1 - off
}

function stackPush(id_, val) {
    const id = CallID.from(id_)
    log.info("Push to the stack:", id, val)
    checkStackVal(val)
    valueStack.push(val)
}

function stackCopy(id_) {
    const id = CallID.from(id_)
    if (valueStack.length < 1)
        throw new Error(`Cannot duplicate the value at the top of the stack, because it's empty`)
    log.info("Duplicate the top stack entry:", id)
    valueStack.push(valueStack[valueStack.length - 1])
}

function stackPop(id_) {
    const id = CallID.from(id_)
    if (valueStack.length < 1)
        throw new Error(`Cannot pop a value off the stack, because it's empty`)
    const val = valueStack.pop()
    log.info("Pop a value from the stack:", id, val)
    return val
}

function stackSwap(id_, offA, offB) {
    const id = CallID.from(id_)
    checkStackOff(offA)
    checkStackOff(offB)
    const A = getStack(offA)
    const B = getStack(offB)
    log.info("Swap 2 values on the top of the stack:", id, A, B)
    valueStack[getStackIndex(offA)] = B
    valueStack[getStackIndex(offB)] = A
}

function compare(id_) {
    const id = CallID.from(id_)
    log.groupCollapsed("Compare:", id)
    const A = stackPop(id)
    const B = stackPop(id)
    log.info(`Compare: result = ${A} == ${B}`)
    const result = Number(A === B)
    stackPush(id, result)
    log.info(`Result: ${A} === ${B} = ${result}`)
    log.groupEnd()
}

function read(id_) {
    const id = CallID.from(id_)
    log.info("Read:", id, currentTarget)
    if (currentTarget === null) throw new Error("Cannot read the contents of an element, when there's no element currently being targeted")
    let value = null
    if (currentTarget instanceof HTMLInputElement) {
        switch (currentTarget.type) {
            case "button":
            case "color":
            case "date":
            case "datetime-local":
            case "email":
            case "file":
            case "hidden":
            case "month":
            case "number":
            case "password":
            case "radio":
            case "range":
            case "search":
            case "submit":
            case "tel":
            case "text":
            case "time":
            case "url":
            case "week":
                value = currentTarget.value
                break
            case "checkbox":
                value = currentTarget.checked
                break
            case "image":
            case "reset":
            default:
                throw new Error(`Unsupported input type="${currentTarget.type}"`)
        }
    } else value = currentTarget.innerHTML

    stackPush(id, value)
}

function ifStatement(id_, ifTrue) {
    const id = CallID.from(id_)
    const isTrue = stackPop(id_) === 1
    log.group("If statement:", id, isTrue)
    if (!isTrue) return

    const info = new RenderingStackEntry(
        id,
        currentCodeSection,
        renderingStack[renderingStack.length - 1].element, // Inherit the element from the parent
        IF_STATEMENT_KIND
    )
    renderingStack.push(info)
    log.info("Info:", info)
    ifTrue()
    renderingStack.pop()
    log.groupEnd()
}

function scheduleRender(id_) {
    const id = CallID.from(id_)
    log.info("Schedule render:", id)
    if (currentCodeType === MUST_BE_CALLABLE) {
        if (!shouldRerender) setTimeout(render, RERENDER_TIMEOUT)
    } else {
        scheduledRendersWhileRendering++
    }
    shouldRerender = true
}

function getString(key) {
    if (!stringMap.has(key)) throw new Error(`String ${key} not found`)
    return stringMap.get(key)
}

function getConstant(key) {
    if (!ROMMap.has(key)) throw new Error(`ROM constant ${key} not found`)
    return ROMMap.get(key)
}

function getStack(key) {
    checkStackOff(key)
    return valueStack[getStackIndex(key)]
}

function rawValue(id_, unsafeInnerHTML, content) {
    const id = CallID.from(id_)
    if (typeof content === "undefined" || content === null) {
        log.info("Raw value undefined, skip:", id, unsafeInnerHTML, content)
        return
    }
    content = content.toString()
    log.info("Raw value:", id, unsafeInnerHTML, content)
    const container = renderingStack[renderingStack.length - 1].element
    const elem = document.createElement("span")
    /**
     * @type {HTMLElement}
     */
    let finalContainer
    if (unsafeInnerHTML) {
        elem.innerHTML = content
        finalContainer = elem.firstChild
        if (finalContainer instanceof Text) unsafeInnerHTML = false
    }
    if (!unsafeInnerHTML) {
        elem.innerText = content
        finalContainer = elem
    }
    finalContainer.setAttribute("x-id", "rawValue-".concat(id))
    container.appendChild(finalContainer)
}

/**
 * @param newStringMap {[number, string][]}
 */
function strings(newStringMap) {
    stringMap = new Map(newStringMap)
}

/**
 * @param newROMMap {[number, number][]}
 */
function rom(newROMMap) {
    ROMMap = new Map(newROMMap)
}

function code(label, isRenderable, rendererOrCallee) {
    codeMap.set(label, new CodeSection(label, isRenderable, rendererOrCallee))
}

function setUnsafeMode(newUnsafeMode) {
    unsafeMode = newUnsafeMode
}

function main(target) {
    // EsoML COMPILED CODE

    try {
        renderingStack.push(new RenderingStackEntry(rootID, new CodeSection(root, true, null), target))

        if (codeMap.has("init")) call(rootID, "init", MUST_BE_CALLABLE)

        render()
    } catch (e) {
        renderError(e)
    } finally {

    }

    // Reset the counter every second lazily
    setInterval(() => {
        scheduledRendersWhileRendering = 0
    }, 1000)
}

function render() {
    console.time("Render")
    log.groupCollapsed("Render")
    shouldRerender = false
    renderingStack[0].element.innerHTML = "" // Could be done better, but whatever
    try {
        call(rootID, "main", MUST_BE_RENDERABLE)
        if (!unsafeMode && (scheduledRendersWhileRendering > MAX_RE_RENDERS_PER_SECOND)) {
            shouldRerender = false
            throw new Error(`The amount of scheduled re-renders from the render sections or unknown section exceeded ${MAX_RE_RENDERS_PER_SECOND} per second, infinite loop prevented.\nMaybe you want to add the unsafe_mode section to your code (will not log anything other than timing)`)
        }
    } catch (e) {
        renderError(e)
    }
    if (shouldRerender) setTimeout(render, RERENDER_TIMEOUT)
    log.groupEnd()
    console.timeEnd("Render")
}

function renderError(e) {
    for (let i = 0; i < renderingStack.length; i++) log.groupEnd()
    renderingStack[0].element.style.color = "red"
    const err = (e.stack || e.toString()).replaceAll("<", "&lt;").replaceAll("\n", "<br>")
    renderingStack[0].element.innerHTML = "<h1>An error occurred</h1>".concat(err)
    log.error(e)
}

main(document.getElementById("root"))
