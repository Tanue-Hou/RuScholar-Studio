import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import ts from 'typescript'

const file = new URL('../src/api/client.ts', import.meta.url)
const js = ts.transpileModule(readFileSync(file, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText
const api = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`)
const engine = { engineType: 'local', apiKey: '', baseUrl: '' }

for (const [name, invoke, body] of [
  ['classification', signal => api.detectDiscipline('synthetic', engine, signal), { discipline: 'UNIVERSAL' }],
  ['session creation', signal => api.createSession('synthetic', 'UNIVERSAL', engine, signal), { session_id: 'synthetic-id' }],
  ['reference upload', signal => api.uploadReferences('synthetic-id', null, [], signal), { status: 'ok', bibtex_keys: [], pdf_keys: [] }],
]) {
  test(`${name} forwards cancellation and preserves AbortError`, async () => {
    const previous = globalThis.fetch
    const controller = new AbortController()
    try {
      globalThis.fetch = async (_, options) => {
        assert.equal(options.signal, controller.signal)
        options.signal.throwIfAborted()
        return new Response(JSON.stringify(body), { status: 200 })
      }
      await invoke(controller.signal)
      controller.abort()
      await assert.rejects(invoke(controller.signal), { name: 'AbortError' })
    } finally {
      globalThis.fetch = previous
    }
  })
}

test('reference registration keeps metadata distinct from indexed full text', async () => {
  const previous = globalThis.fetch
  const registration = { status: 'ok', bibtex_keys: ['synthetic'], pdf_keys: [] }
  try {
    globalThis.fetch = async () => new Response(JSON.stringify(registration), { status: 200 })
    const result = await api.uploadReferences('synthetic-id', null, [])
    assert.deepEqual(result.bibtex_keys, ['synthetic'])
    assert.deepEqual(result.pdf_keys, [])
  } finally {
    globalThis.fetch = previous
  }
})

test('document upload forwards cancellation and reports backend errors', async () => {
  const previous = globalThis.fetch
  const controller = new AbortController()
  const file = new File(['synthetic manuscript'], 'synthetic.txt', { type: 'text/plain' })
  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/upload')
      assert.equal(options.method, 'POST')
      assert.equal(options.signal, controller.signal)
      assert.equal(options.body.get('file').name, 'synthetic.txt')
      return new Response(JSON.stringify({ detail: 'File exceeds upload limit' }), { status: 413 })
    }
    await assert.rejects(api.uploadDocument(file, controller.signal), /File exceeds upload limit/)
  } finally {
    globalThis.fetch = previous
  }
})

test('model download uses POST and decodes progress across chunk boundaries', async () => {
  const previous = globalThis.fetch
  const progress = []
  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(url, '/api/download_model')
      assert.equal(options.method, 'POST')
      const encoder = new TextEncoder()
      return new Response(new ReadableStream({
        start(controller) {
          for (const chunk of ['data: {"status":"downloading","progress":', '37}\r\n\r\ndata: {"status":"complete"}\n\n']) controller.enqueue(encoder.encode(chunk))
          controller.close()
        },
      }))
    }
    await api.downloadModel(percent => progress.push(percent))
    assert.deepEqual(progress, [37])
  } finally {
    globalThis.fetch = previous
  }
})
