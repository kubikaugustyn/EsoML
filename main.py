import os.path
import re
from typing import Final
from urllib.parse import urlparse, parse_qs
from kutil import HTTPServer, HTTPServerConnection, ProtocolConnection, readFile, writeFile
from kutil.protocol.HTTP import HTTPRequest, HTTPResponse, HTTPHeaders

from esoml.compile import compileEsoML, EsoMLOptions

print("main.py:10: You can hardcode the source EsoML file's path here! Default is 'main.eml'")
EML_PATH: Final[str] = "main.eml"
# EML_PATH: Final[str] = "examples/truth_machine.eml"
# EML_PATH: Final[str] = "examples/counter.eml"
# EML_PATH: Final[str] = "examples/layout.eml"

lastEMLContents: str | None = None
lastCompiledFile: str | None = None


def compile(locale: str | None = None) -> str:
    global lastEMLContents, lastCompiledFile

    contents: str = readFile(EML_PATH, "text")
    if lastEMLContents == contents:
        return lastCompiledFile

    print()
    print("Compiling EsoML...")

    file = compileEsoML(contents, EsoMLOptions(locale=locale))
    lastEMLContents = contents
    lastCompiledFile = file.export()
    print("Compiled:", file)
    print()
    return lastCompiledFile


def build(locale: str | None = None) -> str:
    if not os.path.exists("build"):
        os.mkdir("build")
    elif os.path.isfile("build"):
        raise OSError("The build path already exists, but is not a directory")

    # Gets the default locale if locale is None
    locale = EsoMLOptions(locale=locale).getCompilerOptions().locale

    js: str = rf'build/index.{locale}.js'
    jsFromHTML: str = f'./index.js?locale={locale}'  # The JS path on the server!
    jsFromDir: str = rf'./index.{locale}.js'  # The JS path in the directory!
    html: str = rf'build/index.{locale}.html'

    writeFile(js, compile(locale))
    templateHTML: str = readFile("index.html", "text")
    writeFile(html, templateHTML.replace("{COMPILED_SRC}", jsFromDir))
    return templateHTML.replace("{COMPILED_SRC}", jsFromHTML)


def checkLocale(locale: str | None = None) -> bool:
    if locale is None:
        return True
    pattern: re.Pattern = re.compile(r"^[a-z]{2}(_[A-Z]{2}(.[a-zA-Z0-9-]+)?)?$")
    match: re.Match | None = re.match(pattern, locale)
    return match is not None


def onData(conn: HTTPServerConnection, req: HTTPRequest):
    assert isinstance(req, HTTPRequest)
    headers = HTTPHeaders()
    headers["Cache-Control"] = "no-cache, no-store"
    uri = urlparse(req.requestURI)
    query = parse_qs(uri.query)
    print(f"{req.method.name} {req.requestURI}")

    locale: str | None = query.get("locale", [None])[0]
    headers["X-Locale"] = EsoMLOptions(locale=locale).getCompilerOptions().locale
    try:
        if not checkLocale(locale):
            resp = HTTPResponse(400, "Bad Request", headers,
                                b"The provided locale is invalidly formatted.")
        elif uri.path in {"", "/", "index.html"}:
            html: bytes = build(locale).encode("utf-8")
            resp = HTTPResponse(200, "OK", headers, html)
            headers["Content-Type"] = "text/html, encoding=utf-8"
        elif uri.path == "/index.js":
            js: bytes = compile(locale).encode("utf-8")
            resp = HTTPResponse(200, "OK", headers, js)
            headers["Content-Type"] = "application/javascript, encoding=utf-8"
        else:
            resp = HTTPResponse(404, "Not Found", headers,
                                b"The requested resource wasn't found on this server.")
    except Exception as e:
        import traceback
        trace: bytes = (b'<h1>500 - Internal Server Error</h1><p>An internal server error'
                        b' occurred (probably while compiling your EsoML code).</p>'
                        b'<pre>' + traceback.format_exc().encode("utf-8") + b'</pre>')
        resp = HTTPResponse(500, "Internal Server Error", headers, trace)
        traceback.print_exc()
    conn.sendData(resp)
    conn.close()


def onConnection(conn: ProtocolConnection):
    if not isinstance(conn, HTTPServerConnection):
        raise ValueError
    return onData


if __name__ == '__main__':
    host, port = addr = ("localhost", 5555)
    server: HTTPServer = HTTPServer(addr, onConnection)
    print(f"Server open on http://{host}:{port}")
    server.listen()
    # Go to http://localhost:5555/ and see the results
