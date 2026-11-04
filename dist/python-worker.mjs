// KatalCode compiler: runs Python in a module Web Worker so an infinite loop can be stopped by
// terminating the worker. Pyodide (CPython compiled to WebAssembly) loads from jsDelivr, pinned
// to one version. Code and input never leave the reader's browser.

const PYODIDE = 'https://cdn.jsdelivr.net/npm/pyodide@314.0.7/'
const { loadPyodide } = await import(PYODIDE + 'pyodide.mjs')

const RUNNER = `
import sys, io, traceback, linecache

def __pg_run(code, data):
    sys.stdin = io.TextIOWrapper(io.BytesIO(data.encode()), encoding='utf-8')
    linecache.cache['main.py'] = (len(code), None, code.splitlines(True), 'main.py')
    g = {'__name__': '__main__', '__builtins__': __builtins__}
    try:
        exec(compile(code, 'main.py', 'exec'), g)
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f'Exited with code {e.code}', file=sys.stderr)
            return 1
    except BaseException as e:
        tb = e.__traceback__
        while tb is not None and tb.tb_frame.f_code.co_filename != 'main.py':
            tb = tb.tb_next
        traceback.print_exception(type(e), e, tb)
        return 1
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
    return 0
`

const decoder = new TextDecoder()
const stream = (name) => ({
  write(buf) {
    postMessage({ type: 'out', stream: name, text: decoder.decode(buf, { stream: true }) })
    return buf.length
  },
})

const ready = (async () => {
  const py = await loadPyodide({ indexURL: PYODIDE })
  py.setStdout(stream('stdout'))
  py.setStderr(stream('stderr'))
  py.runPython(RUNNER)
  postMessage({ type: 'ready', version: py.version })
  return py.globals.get('__pg_run')
})()

ready.catch((e) => postMessage({ type: 'fatal', message: String(e?.message || e) }))

onmessage = async ({ data }) => {
  if (data.type !== 'run') return
  const run = await ready
  const t0 = performance.now()
  const rc = run(data.code, data.stdin)
  postMessage({ type: 'done', id: data.id, rc, ms: Math.round(performance.now() - t0) })
}
