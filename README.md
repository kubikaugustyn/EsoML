# What is EsoML

EsoML stands for ***Eso***teric ***M***arkup ***L***anguage and it is an esoteric language that allows you to write code
as if you were writing [Vue.js](https://vuejs.org/) rendering functions, but with the feel of assembly. It's a language
that lets you create awesome websites that feel like they're from the 2000s, without any attributes to elements and
styling. Raw HTML rendered using JavaScript under the hood.

The language is based on a similar concept as modern compiled languages such as Vue.js with it's `openBlock` etc.
functions, but reversed. It also resembles the feel of true assembly, although it has some big differences.

Adding attributes to elements and styling them is a TODO, it's not yet implemented.

# EsoML syntax guide

This is a simple guide on how to use EsoML.

Line numbers are counted starting with `1`. There are no explicit comments. However, you can implicitly comment
instructions. That is because very instruction has the syntax/format as described
below `<type> <argument1> <argument2>...<argumentN>`, you can use the arguments unused by the instruction to pass in
pseudo-comments (which will be treated as unused arguments for the instruction by the compiler). An example
is the following `render` section:

```eml
.render main
cont h1             This will create a h1 container tag/element
text 0s             Show the text from the top of the stack
econ                Don't forget to close it
```

## Sections

Sections are started with a so-called section header: `.<section> <argument>`

### Strings section

Format: `.strings <locale>`

This is the section where your localized strings will be stored. The `<locale>` parameter is the locale you're defining
strings for.

You write strings there in the following format: `Let <id> be translated to <text>.`. The `<id>` parameter is
the ID of the `<text>` (not the final number/key you reference in code) base-8 encoded for better readability.
See [references to values](#references-to-values-and-id-vs-key) for more info. The `<text>` parameter is the text you
want to store.

**Example:**

```eml
.strings en_US
Let 1 be translated to EsoML string example.
```

### ROM section

Format: `.rom <locale>`

This is the section where your localized read-only numbers will be stored. The `<locale>` parameter is the locale you're
defining numbers for.

You write numbers there in the following format: `Remember that <id> will always be <number>.`. The `<id>` parameter is
the ID of the `<number>` (not the final number/key you reference in code) base-8 encoded for better readability.
See [references to values](#references-to-values-and-id-vs-key) for more info. The `<number>` parameter is base-11
encoded to make
your code cleaner.

**Example:**

```eml
.rom en_US
Remember that 1 will always be 3.
```

### Code and render sections

Format:

- Code - `.code <label>`
- Render - `.render <label>`

These are the sections where your main code will be stored. The `<label>` parameter is the label you call to control the
execution flow. The difference between `.code <label>` and `.render <label>` is the fact that `.code <label>` is used to
handle events and `.code main` is used to initialize the stack, for example, whereas the `.render <label>` section is
used as a component that can simply be reused and that will be able to output elements (thus it can use
the `text`, `cont` and other render-only instructions.)

**Example:**

```eml
.render main
cont h1             Creates a container (div by default)
text 78t            Adds text to the content (equivalent to innerText)
econ                Closes the container
```

## Instructions

All instructions are exactly four characters long for better readability.
Format: `<type> <argument1> <argument2>...<argumentN>`

### Start container - `cont`

The `cont <type?|div>` instruction is used to start/open a container.

### End container - `econ`

The `econ` instruction is used to end/close a container.

### Create element - `elem`

The `elem <type>` instruction is used to create an element without the ability to set its contents.
It's an equivalent of doing this:

```eml
cont <type>
econ
```

### Render text - `text`

The `text <text>` instruction is used to inject/add/render text. Can be thought of as `elem.innerText += <text>`.

### Render raw HTML - `show`

The `show <html>` instruction is used to inject/add/render raw HTML. Can be thought of as `elem.innerHTML += <html>`.
Note that only the first HTML element the raw HTML results to when parsed is added/rendered.

### Execute/render a different section - `call`

The `call` instruction is used to either execute another `code` section if called from a `code` section, or inject
another `render` section if called from a `render` section (can be thought of as using a custom UI component). The
executed section is run from its beginning to its end, there's no conditional return instruction. The only thing you can
do is conditionally execute instructions (and potentially perform nested calls) from within the `ifis`-`endi` statement.

### Schedule a re-render - `rend`

The `rend` instruction is used to schedule a re-render. Can be used in both `code` and `render` sections, as it is
essential to create a Truth Machine. Scheduled re-renders are executed every 100ms, though that can be changed
in `lib.js --> RERENDER_TIMEOUT`

### Add event listener - `hear`

The `hear <event> <callback>` instruction is used to add an event listener to listen to any kind of event. This is the
bond of `code` and `render` sections, because it can only be used in a `render` section, but the `<callback>` must be
a `code` section.

### Push a value to the stack - `push`

The `push <value>` instruction is used to push a value to the top of the stack.

### Duplicate the top value on top of the stack - `copy`

The `copy` instruction is used to duplicate the value at the top of the stack. Technically, it is an equivalent of
doing `push 0s`.

### Pop the top value from the stack - `pops`

The `pops` instruction is used to ***pop*** a value from the ***s***tack. The value is simply discarded.

### Swap two values on the stack - `swap`

The `swap <offA?|0> <offB?|1>` instruction is used to swap the desired values on the stack. By default, it swaps the two
values at the top of the stack. To allow for complex programs, you can overwrite the offsets to your desired values.

### Compare the top two values on the stack - `comp`

The `comp` instruction is used to compare the top two values on the stack. The compared values are deleted. If they are
equal (JavaScript comparison `===`) then `1` is pushed onto the stack, otherwise `0` is pushed. The process/calculation
is the following:

- Pop A from the top of the stack
- Pop B from the top of the stack
- Push `A === B ? 1 : 0` to the top of the stack

### Read contents of an element - `read`

The `read` instruction is used to read the contents of an element. If the element is an input, it will read its value.
Otherwise, it will fall back to reading `innerHTML`. Which element are the contents read from? In the `code` section, it
is the element the event listener was bound to using the `hear` instruction. In the `render` section, the element is the
current container you're writing the instruction in. If the target element cannot be determined, an error is thrown at
runtime. See the console for the `currentTarget` variable to see the current target element (when in debug mode).

### Maths - ADD - `madd`

The `madd` instruction is used to add two numbers together. The process/calculation is the following:

- Pop A from the top of the stack
- Pop B from the top of the stack
- Push `A + B` to the top of the stack

### Maths - SUB - `msub`

The `msub` instruction is used to subtract two numbers from each other. The process/calculation is the following:

- Pop A from the top of the stack
- Pop B from the top of the stack
- Push `A - B` to the top of the stack

### Maths - MUL - `mmul`

The `mdiv` instruction is used to multiply two numbers. The process/calculation is the following:

- Pop A from the top of the stack
- Pop B from the top of the stack
- Push `A * B` to the top of the stack

### Maths - DIV - `mdiv`

The `mdiv` instruction is used to integer divide two numbers. The process/calculation is the following:

- Pop A from the top of the stack
- Pop B from the top of the stack
- Push `A // B` to the top of the stack (`//` is integer division, can be represented as JavaScript `Math.floor(A / B)`)

### Start if statement - `ifis`

The `ifis` instruction is used to start an if block. The top value is popped from the stack and if, and only if, the
value is exactly equal to `1` as an integer, the contents of the if statement are executed. You can compare two values
with the `comp` instruction before using the comparison result in an if statement.

### End if statement - `endi`

The `endi` instruction is used to end an if block.

## References to values and `id` vs `key`

There are three types/ways of referencing a value:

1. `<key>t` - reference to a key of a ***t***ext in the `strings` section, for example `69t` is a ref to a text in the
   strings with its key being 69
2. `<key>c` - reference to a key of a ***c***onstant in the `rom` section, for example `69c` is a ref to a constant in
   the rom with its key being 69
3. `<off>s` - reference to an offset from the end of the ***s***tack, for example `1s` is a ref to the second item on
   the stack counted from the top of the stack

The keys are derived from ids, using a simple mathematical formula. It depends on the offset from the start of the
section (line number offset), so you can create the same offsets for multiple localizations. The source code for the
function can be found in the `esoml.lexer` file, around line 65 of the file, it's a method of a class `EsoMLLexer`
defined as the following:

```python
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
```

To describe the algorithm, we'll use simpler notation:

```
ID = parseInt(ID_STR, base=8)
OP_ID = LINE_NUM % LEN_ID % 3
RESULT = ((ID * 3) << 2) + 0x42    for OP_ID == 0
         ((ID ^ 1337) << 3) - 5    for OP_ID == 1
         ((ID // 7) % 0x69) + 666  for OP_ID == 2
```

where:

- `LINE_NUM` is the line number offset starting with `0` from the section header (`lineNumber - section.startsAtLine`)
- `ID_STR` is the string version of the id provided in the source code, encoded in **base 8** for convenience
- `ID_LEN` is the length of the string version of `ID_STR` in characters

Absolutely do not look at the compiler output in the Python console because it would help you to figure out which id at
which line corresponds to which key.

## Examples

You can find example code together with some comments in the `examples/` folder.
