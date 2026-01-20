# BrewJS
BrewJS is a small, dynamic scripting language focused on clarity, composability, and creative coding. It blends familiar control flow with simple primitives for strings, arrays, randomness, and time-based behavior.

## Interpreter
This repo now includes a full Python interpreter with:

- Lexer + parser (AST) pipeline.
- Closures, objects, arrays, and nested scopes.
- `try`/`catch`/`finally` and `throw` with readable error spans.
- Built-in modules: `console`, `random`, `string`, `array`, `time`, `file`, `data`, `thread`.
- Colorized console output via `console.log({ text: "...", color: "red" })` or `console.colorize(text, color)`.

### Running
```bash
python main.py path/to/script.brew
```

### Installer (adds `brew` command)
```bash
./releases/install.sh
brew path/to/script.brew
```

Set `BREW_INSTALL_DIR` to customize install location (default: `~/.local/bin`).

### Built-ins
- `console.log/info/warn/error(...)`
- `random.int(lo, hi)`, `random.pick(arr)`, `random.char("a", "z")`
- `string.length(s)`, `string.charAt(s, i)`, `string.upper(s)`, `string.lower(s)`, `string.slice(s, start, end)`
- `string.split(s, sep)`, `string.join(arr, sep)`, `string.indexOf(s, sub)`, `string.codePointAt(s, i)`
- `array.length(arr)`, `array.contains(arr, value)`, `array.shift(arr)`
- `time.now()`
- `file.read(path)`, `file.write(path, content)`, `file.append(path, content)`
- `data.queue()`, `data.stack()`, `data.set(...)`, `data.map()`
- `thread.run(fn)` returning a handle with `.join()`
- `pauseExecution(ms)`
