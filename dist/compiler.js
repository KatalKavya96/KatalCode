"use strict";

// KatalCode compiler: write code, type your own input, press Run. There are no test cases and
// no judge, on purpose. It's for reading a problem and trying an idea on the spot.
//
// Everything runs in the reader's browser, so there is no server to pay for or abuse:
//   Python  Pyodide (CPython 3.14 in WebAssembly) in a Web Worker: python-worker.mjs
//   Java    CheerpJ (OpenJDK 17 in WebAssembly), free for personal and educational use
//
// window.KatalCompiler.mount(container, { key, title, problemUrl }) builds one runner.
// Code, input and language are saved per key in localStorage.

(() => {
  const TEMPLATES = {
    python: `import sys
input = sys.stdin.readline


def main():
    n = int(input())
    arr = list(map(int, input().split()))
    print(sum(arr))


main()
`,
    java: `import java.io.*;
import java.util.*;

public class Main {
    public static void main(String[] args) throws IOException {
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        int n = Integer.parseInt(br.readLine().trim());
        StringTokenizer st = new StringTokenizer(br.readLine());
        long sum = 0;
        for (int i = 0; i < n; i++) sum += Long.parseLong(st.nextToken());
        System.out.println(sum);
    }
}
`,
  };
  const DEFAULT_STDIN = "5\n1 2 3 4 5\n";
  const LABELS = { python: "Python 3", java: "Java 17" };
  const TIME_LIMIT_S = 10;
  const MAX_OUTPUT = 100000;

  // ---------- storage (best effort: private windows can throw) ----------
  const store = {
    get(key) { try { return window.localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { window.localStorage.setItem(key, value); } catch { /* ignore */ } },
  };

  // ---------- Python runner ----------
  const python = (() => {
    let worker = null;
    let ready = null;
    let nextId = 1;
    let active = null;

    function kill() {
      if (worker) worker.terminate();
      worker = null;
      ready = null;
    }

    function boot(onStatus) {
      if (ready) return ready;
      onStatus("Loading Python (about 13 MB the first time, then cached)…");
      worker = new Worker(new URL("./python-worker.mjs?v=compiler-1", document.baseURI), { type: "module" });
      ready = new Promise((resolve, reject) => {
        worker.onmessage = ({ data }) => {
          if (data.type === "ready") return resolve();
          if (data.type === "fatal") return reject(new Error(data.message));
          if (!active) return;
          if (data.type === "out") active.onOutput(data.stream, data.text);
          if (data.type === "done" && data.id === active.id) {
            const run = active;
            active = null;
            run.resolve({ status: data.rc === 0 ? "ok" : "error", ms: data.ms });
          }
        };
        worker.onerror = (event) => {
          event.preventDefault();
          reject(new Error(event.message || "Python could not start. Check your connection."));
        };
      });
      ready.catch(kill);
      return ready;
    }

    async function run(code, stdin, onOutput, onStatus) {
      await boot(onStatus);
      onStatus("Running…");
      return new Promise((resolve) => {
        active = { id: nextId++, onOutput, resolve };
        worker.postMessage({ type: "run", id: active.id, code, stdin });
      });
    }

    function stop(status) {
      if (!active) return;
      const run = active;
      active = null;
      kill();
      run.resolve({ status });
    }

    return { run, stop };
  })();

  // ---------- Java runner ----------
  // javac compiles the reader's file plus PgRunner, which points System.in at the input file and
  // calls main(). CheerpJ prints System.out and System.err into the element with id "console".
  const java = (() => {
    const LOADER = "https://cjrtnc.leaningtech.com/5.0/loader.js";
    const RUNNER = `public class PgRunner {
  public static void main(String[] args) throws Throwable {
    System.setIn(new java.io.BufferedInputStream(new java.io.FileInputStream("/str/pg/stdin.txt")));
    java.lang.reflect.Method main;
    try {
      main = Class.forName(args[0]).getMethod("main", String[].class);
    } catch (NoSuchMethodException e) {
      System.err.println("No 'public static void main(String[] args)' in class " + args[0] + ".");
      System.exit(1);
      return;
    }
    try {
      main.invoke(null, (Object) new String[0]);
    } catch (java.lang.reflect.InvocationTargetException e) {
      System.out.flush();
      System.err.print("Exception in thread \\"main\\" ");
      e.getCause().printStackTrace();
      System.exit(1);
    }
    System.out.flush();
  }
}
`;
    let ready = null;
    let busy = false;
    let consoleElement = null;

    function loadScript(src) {
      return new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = src;
        script.onload = resolve;
        script.onerror = () => reject(new Error("Java could not load. Check your connection."));
        document.head.append(script);
      });
    }

    function boot(onStatus) {
      if (ready) return ready;
      onStatus("Loading Java 17 (the first run downloads the JVM, then it is cached)…");
      ready = (async () => {
        consoleElement = document.getElementById("console") || document.createElement("pre");
        consoleElement.id = "console";
        consoleElement.hidden = true;
        document.body.append(consoleElement);
        await loadScript(LOADER);
        await window.cheerpjInit({ version: 17, status: "none" });
      })();
      ready.catch(() => { ready = null; });
      return ready;
    }

    // The class holding main(): the public class, else the last class declared before main.
    function mainClass(code) {
      const pkg = (code.match(/^\s*package\s+([\w.]+)\s*;/m) || [])[1];
      const pub = (code.match(/public\s+(?:final\s+|abstract\s+)*class\s+(\w+)/) || [])[1];
      let name = pub;
      if (!name) {
        const at = code.search(/static\s+void\s+main\s*\(/);
        const declared = [...(at === -1 ? code : code.slice(0, at)).matchAll(/\bclass\s+(\w+)/g)];
        name = declared.length ? declared[declared.length - 1][1] : "Main";
      }
      return { file: `${pub || "Main"}.java`, cls: pkg ? `${pkg}.${name}` : name };
    }

    async function step(fn) {
      consoleElement.textContent = "";
      const rc = await fn();
      await new Promise((resolve) => setTimeout(resolve, 60));
      return { rc, text: consoleElement.textContent || "" };
    }

    async function run(code, stdin, onOutput, onStatus) {
      if (busy) {
        onOutput("stderr", "A Java program is still running. Reload the page to stop it.\n");
        return { status: "error" };
      }
      busy = true;
      try {
        await boot(onStatus);
        const encode = (text) => new TextEncoder().encode(text);
        const { file, cls } = mainClass(code);
        window.cheerpjAddStringFile(`/str/pg/${file}`, encode(code));
        window.cheerpjAddStringFile("/str/pg/PgRunner.java", encode(RUNNER));
        window.cheerpjAddStringFile("/str/pg/stdin.txt", encode(stdin));

        onStatus("Compiling… (the first compile warms up javac and is slow)");
        const compileStart = performance.now();
        const javac = await step(() => window.cheerpjRunMain("com.sun.tools.javac.Main", "/files/",
          `/str/pg/${file}`, "/str/pg/PgRunner.java", "-d", "/files/pg/", "-encoding", "UTF-8"));
        if (javac.rc !== 0) {
          onOutput("stderr", javac.text.replaceAll("/str/pg/", "") || `javac exited with code ${javac.rc}\n`);
          return { status: "compile-error" };
        }

        onStatus("Running…");
        const runStart = performance.now();
        const result = await step(() => window.cheerpjRunMain("PgRunner", "/files/pg/", cls));
        // CheerpJ merges System.out and System.err into one console.
        onOutput("stdout", result.text);
        return {
          status: result.rc === 0 ? "ok" : "error",
          ms: Math.round(performance.now() - runStart),
          compileMs: Math.round(runStart - compileStart),
        };
      } finally {
        busy = false;
      }
    }

    return { run, mainClass };
  })();

  // ---------- editor: a textarea with line numbers and code-friendly keys ----------
  function createEditor(onRun, onChange) {
    const wrap = element("div", "kc-editor");
    const gutter = element("div", "kc-gutter");
    gutter.setAttribute("aria-hidden", "true");
    const area = element("textarea", "kc-code");
    area.spellcheck = false;
    area.autocapitalize = "off";
    area.autocomplete = "off";
    area.setAttribute("autocorrect", "off");
    area.setAttribute("aria-label", "Code editor. Press Escape, then Tab, to move focus out.");
    area.wrap = "off";
    wrap.append(gutter, area);

    let escaped = false;
    const refresh = () => {
      const count = area.value.split("\n").length;
      if (gutter.childElementCount !== count) {
        gutter.textContent = Array.from({ length: count }, (_, i) => i + 1).join("\n");
      }
      gutter.scrollTop = area.scrollTop;
    };
    const replace = (start, end, text, caretStart, caretEnd = caretStart) => {
      area.setRangeText(text, start, end);
      area.setSelectionRange(caretStart, caretEnd);
      refresh();
      onChange(area.value);
    };

    area.addEventListener("input", () => { refresh(); onChange(area.value); });
    area.addEventListener("scroll", () => { gutter.scrollTop = area.scrollTop; });
    area.addEventListener("blur", () => { escaped = false; });
    area.addEventListener("keydown", (event) => {
      const { selectionStart: start, selectionEnd: end, value } = area;
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        event.preventDefault();
        onRun();
        return;
      }
      if (event.key === "Escape") { escaped = true; return; }
      if (event.key === "Tab" && !escaped && !event.altKey && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        const lineStart = value.lastIndexOf("\n", start - 1) + 1;
        if (start === end && !event.shiftKey) {
          replace(start, end, "    ", start + 4);
          return;
        }
        // Indent or dedent every selected line.
        const block = value.slice(lineStart, end);
        const lines = block.split("\n");
        const changed = lines.map((line) => event.shiftKey ? line.replace(/^ {1,4}/, "") : `    ${line}`);
        const text = changed.join("\n");
        const firstShift = changed[0].length - lines[0].length;
        replace(lineStart, end, text, Math.max(lineStart, start + firstShift), lineStart + text.length);
        return;
      }
      escaped = false;
      if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        // Keep the indentation; indent once more after ":" (Python) or "{" (Java).
        event.preventDefault();
        const lineStart = value.lastIndexOf("\n", start - 1) + 1;
        const line = value.slice(lineStart, start);
        let indent = line.match(/^[ \t]*/)[0];
        if (/[:{]\s*$/.test(line)) indent += "    ";
        const insert = `\n${indent}`;
        replace(start, end, insert, start + insert.length);
        return;
      }
      if (event.key === "Backspace" && start === end && start > 0) {
        // Delete back to the previous 4-space stop inside leading indentation.
        const lineStart = value.lastIndexOf("\n", start - 1) + 1;
        const before = value.slice(lineStart, start);
        if (before.length && /^ +$/.test(before)) {
          event.preventDefault();
          const remove = before.length % 4 || 4;
          replace(start - remove, start, "", start - remove);
        }
      }
    });

    return {
      element: wrap,
      get value() { return area.value; },
      set value(text) { area.value = text; area.scrollTop = 0; refresh(); },
      focus() { area.focus(); },
    };
  }

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function button(className, text, title) {
    const node = element("button", className, text);
    node.type = "button";
    if (title) node.title = title;
    return node;
  }

  // ---------- one runner ----------
  function mount(container, options = {}) {
    const key = `katalcode:compiler:${options.key || "scratch"}`;
    let lang = store.get(`${key}:lang`) === "java" ? "java" : "python";
    let running = false;
    let outputText = "";
    let timer = null;

    const root = element("section", "kc-runner");
    root.setAttribute("aria-label", "Code runner");

    const bar = element("div", "kc-bar");
    const tabs = element("div", "kc-tabs");
    tabs.setAttribute("role", "group");
    tabs.setAttribute("aria-label", "Language");
    const tabButtons = Object.keys(TEMPLATES).map((id) => {
      const tab = button("kc-tab", LABELS[id]);
      tab.dataset.lang = id;
      tab.addEventListener("click", () => switchLang(id));
      tabs.append(tab);
      return tab;
    });
    const actions = element("div", "kc-actions");
    const resetButton = button("kc-ghost", "↺ Reset", "Restore the starter template");
    const stopButton = button("kc-stop", "■ Stop");
    const runButton = button("kc-run", "Run ▶", "Ctrl/⌘ + Enter");
    stopButton.hidden = true;
    actions.append(resetButton, stopButton, runButton);
    bar.append(tabs, actions);

    const editor = createEditor(() => run(), (value) => store.set(`${key}:${lang}`, value));

    const io = element("div", "kc-io");
    const inputPane = element("label", "kc-pane");
    const stdin = element("textarea", "kc-stdin");
    stdin.spellcheck = false;
    stdin.rows = 6;
    stdin.placeholder = "Type the input your program reads";
    inputPane.append(element("span", "kc-label", "Input (stdin)"), stdin);
    const outputPane = element("div", "kc-pane");
    const outputLabel = element("span", "kc-label", "Output");
    const status = element("span", "kc-status");
    status.setAttribute("role", "status");
    outputLabel.append(status);
    const output = element("pre", "kc-output", "Run your code to see its output here.");
    output.tabIndex = 0;
    outputPane.append(outputLabel, output);
    io.append(inputPane, outputPane);

    const note = element("p", "kc-note");
    root.append(bar, editor.element, io, note);
    container.append(root);

    stdin.value = store.get(`${key}:stdin`) ?? DEFAULT_STDIN;
    stdin.addEventListener("input", () => store.set(`${key}:stdin`, stdin.value));
    stdin.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); run(); }
    });

    function renderLang() {
      tabButtons.forEach((tab) => tab.setAttribute("aria-pressed", String(tab.dataset.lang === lang)));
      editor.value = store.get(`${key}:${lang}`) ?? TEMPLATES[lang];
      note.textContent = lang === "python"
        ? `Runs in your browser with Pyodide; nothing is sent to a server. Time limit ${TIME_LIMIT_S} s.`
        : "Runs in your browser with CheerpJ; nothing is sent to a server. The first run is slow. A Java run can't be stopped, so reload the page if it hangs.";
    }

    function switchLang(next) {
      if (running || next === lang) return;
      lang = next;
      store.set(`${key}:lang`, lang);
      renderLang();
    }

    function setRunning(value) {
      running = value;
      runButton.disabled = value;
      resetButton.disabled = value;
      tabButtons.forEach((tab) => { tab.disabled = value; });
      runButton.textContent = value ? "Running…" : "Run ▶";
      stopButton.hidden = !(value && lang === "python");
    }

    function append(stream, text) {
      if (stream === "stderr") output.classList.add("error");
      if (outputText.length >= MAX_OUTPUT) return;
      outputText += text;
      if (outputText.length >= MAX_OUTPUT) {
        outputText = `${outputText.slice(0, MAX_OUTPUT)}\n… output cut at 100,000 characters`;
        if (lang === "python") python.stop("output-limit");
      }
      output.textContent = outputText;
    }

    function describe(result) {
      return {
        ok: `Finished in ${result.ms ?? "?"} ms${result.compileMs ? ` (compiled in ${(result.compileMs / 1000).toFixed(1)} s)` : ""}`,
        error: "Runtime error",
        "compile-error": "Compilation error",
        timeout: `Stopped after ${TIME_LIMIT_S} s. Infinite loop?`,
        stopped: "Stopped",
        "output-limit": "Stopped: too much output",
      }[result.status];
    }

    async function run() {
      if (running) return;
      setRunning(true);
      outputText = "";
      output.textContent = "";
      output.classList.remove("error");
      status.className = "kc-status";
      const showStatus = (text) => {
        status.textContent = text;
        if (text === "Running…" && lang === "python") {
          // The time limit starts once Python has loaded, not while it downloads.
          clearTimeout(timer);
          timer = setTimeout(() => python.stop("timeout"), TIME_LIMIT_S * 1000);
        }
      };
      try {
        const runner = lang === "python" ? python : java;
        const result = await runner.run(editor.value, stdin.value, append, showStatus);
        status.textContent = describe(result);
        status.classList.add(result.status === "ok" ? "ok" : "bad");
        if (!outputText) output.textContent = "(no output)";
        if (result.status === "ok") output.classList.remove("error");
      } catch (error) {
        status.textContent = "Could not start";
        status.classList.add("bad");
        append("stderr", `${error && error.message ? error.message : error}\n`);
      } finally {
        clearTimeout(timer);
        setRunning(false);
      }
    }

    resetButton.addEventListener("click", () => {
      if (!window.confirm(`Replace your ${LABELS[lang]} code with the starter template?`)) return;
      editor.value = TEMPLATES[lang];
      store.set(`${key}:${lang}`, TEMPLATES[lang]);
    });
    stopButton.addEventListener("click", () => python.stop("stopped"));
    runButton.addEventListener("click", run);

    renderLang();
    return { run, focus: () => editor.focus() };
  }

  window.KatalCompiler = { mount, mainClass: java.mainClass, TEMPLATES };
})();
