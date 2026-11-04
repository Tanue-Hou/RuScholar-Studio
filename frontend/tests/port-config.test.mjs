// RS-0002：执行实际 TS 配置与 Python 解析器，验证端口来源及空值优先级。
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import test from 'node:test'
import { fileURLToPath, pathToFileURL } from 'node:url'
import ts from 'typescript'

const configPath = fileURLToPath(new URL('../vite.config.ts', import.meta.url))
const pythonConfig = fileURLToPath(new URL('../../services/config.py', import.meta.url))
const source = ts.transpileModule(readFileSync(configPath, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText
// 注入外围依赖；端口选择和 .env 解析执行仓库的真实代码，不另写一份实现。
const evaluate = new Function('defineConfig', 'react', 'readFileSync', 'fileURLToPath', 'metaURL',
  source.replace(/^import .*\n/gm, '').replace('export default ', 'return ')
    .replaceAll('import.meta.url', 'metaURL'))

const cases = [
  { name: '缺省端口', file: '', expected: 8000 },
  { name: '只读根 .env，忽略 local/mode', file: 'RUSCHOLAR_PORT=6666\n', expected: 6666 },
  { name: '命令行覆盖文件', file: 'RUSCHOLAR_PORT=6666\n', shell: '7001', expected: 7001 },
  { name: '空命令行变量仍优先于文件，回退默认', file: 'RUSCHOLAR_PORT=6666\n', shell: '', expected: 8000 },
  { name: '空文件值回退默认', file: 'RUSCHOLAR_PORT=\n', expected: 8000 },
  { name: '重复键第一次生效', file: 'RUSCHOLAR_PORT=6666\nRUSCHOLAR_PORT=7777\n', expected: 6666 },
  { name: 'export 与成对引号', file: 'export RUSCHOLAR_PORT="6666"\n', expected: 6666 },
  { name: '行尾注释', file: 'RUSCHOLAR_PORT=6666 # local\n', expected: 6666 },
]

for (const scenario of cases) {
  test(scenario.name, () => {
    const dir = mkdtempSync(join(tmpdir(), 'rs-port-'))
    const saved = process.env.RUSCHOLAR_PORT
    try {
      delete process.env.RUSCHOLAR_PORT
      if ('shell' in scenario) process.env.RUSCHOLAR_PORT = scenario.shell
      writeFileSync(join(dir, '.env'), scenario.file)
      writeFileSync(join(dir, '.env.local'), 'RUSCHOLAR_PORT=9002\n')
      writeFileSync(join(dir, '.env.development'), 'RUSCHOLAR_PORT=9003\n')
      const configure = evaluate(x => x, () => ({}), readFileSync, fileURLToPath,
        pathToFileURL(join(dir, 'frontend/vite.config.ts')).href)
      const target = configure().server.proxy['/api'].target
      assert.equal(target, `http://127.0.0.1:${scenario.expected}`)
      const code = [
        'import importlib.util, sys',
        'spec = importlib.util.spec_from_file_location("config", sys.argv[1])',
        'module = importlib.util.module_from_spec(spec)',
        'spec.loader.exec_module(module)',
        'module.load_env_file(sys.argv[2])',
        'print(module.server_port())',
      ].join('\n')
      const result = spawnSync(process.env.PYTHON_FOR_TESTS || 'python3',
        ['-B', '-c', code, pythonConfig, join(dir, '.env')], { encoding: 'utf8' })
      assert.equal(result.status, 0, result.stderr || String(result.error))
      assert.equal(Number(result.stdout.trim()), scenario.expected)
    } finally {
      if (saved === undefined) delete process.env.RUSCHOLAR_PORT
      else process.env.RUSCHOLAR_PORT = saved
      rmSync(dir, { recursive: true, force: true })
    }
  })
}
