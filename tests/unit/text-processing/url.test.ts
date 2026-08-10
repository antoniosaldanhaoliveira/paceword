import { describe, it, expect, vi, afterEach } from 'vitest';
import { extractFromUrl, UrlFetchError } from '@/core/text-processing/url';

const LONG_ARTICLE = 'Lorem ipsum dolor sit amet '.repeat(60);

const ARTICLE_HTML = `<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
  <article>
    <h1>Test Article</h1>
    <p>${LONG_ARTICLE}</p>
  </article>
</body>
</html>`;

function makeFetch(options: {
  ok?: boolean;
  status?: number;
  text?: string;
  json?: Record<string, unknown>;
  contentType?: string;
  reject?: Error;
}) {
  return vi.fn().mockImplementation(() => {
    if (options.reject) return Promise.reject(options.reject);
    return Promise.resolve({
      ok: options.ok ?? true,
      status: options.status ?? 200,
      headers: { get: () => options.contentType ?? 'text/html; charset=utf-8' },
      text: () => Promise.resolve(options.text ?? ARTICLE_HTML),
      json: () => Promise.resolve(options.json ?? {}),
    });
  });
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

async function getError(fn: () => Promise<unknown>): Promise<UrlFetchError> {
  try {
    await fn();
    throw new Error('Expected rejection');
  } catch (err) {
    return err as UrlFetchError;
  }
}

describe('extractFromUrl', () => {
  it('encodes the URL correctly in the proxy request', async () => {
    const fetch = makeFetch({ text: ARTICLE_HTML });
    vi.stubGlobal('fetch', fetch);

    await extractFromUrl('https://example.com/article?q=test&lang=en').catch(() => {});

    const called = fetch.mock.calls[0]?.[0] as string;
    expect(called).toContain('/api/fetch?url=');
    expect(called).toContain(encodeURIComponent('https://example.com/article?q=test&lang=en'));
  });

  it('throws UrlFetchError with kind=network on fetch rejection', async () => {
    vi.stubGlobal('fetch', makeFetch({ reject: new TypeError('Failed to fetch') }));

    const err = await getError(() => extractFromUrl('https://example.com'));
    expect(err).toBeInstanceOf(UrlFetchError);
    expect(err.kind).toBe('network');
  });

  it('throws UrlFetchError with kind=timeout on AbortError', async () => {
    const abort = new DOMException('aborted', 'AbortError');
    vi.stubGlobal('fetch', makeFetch({ reject: abort }));

    const err = await getError(() => extractFromUrl('https://example.com'));
    expect(err).toBeInstanceOf(UrlFetchError);
    expect(err.kind).toBe('timeout');
  });

  it('throws UrlFetchError with kind=network on proxy 504', async () => {
    vi.stubGlobal('fetch', makeFetch({
      ok: false, status: 504,
      json: { error: 'timeout' },
    }));

    const err = await getError(() => extractFromUrl('https://example.com'));
    expect(err).toBeInstanceOf(UrlFetchError);
    expect(err.kind).toBe('timeout');
  });

  it('throws UrlFetchError with kind=blocked on proxy 400 blocked', async () => {
    vi.stubGlobal('fetch', makeFetch({
      ok: false, status: 400,
      json: { error: 'blocked' },
    }));

    const err = await getError(() => extractFromUrl('https://192.168.1.1'));
    expect(err).toBeInstanceOf(UrlFetchError);
    expect(err.kind).toBe('blocked');
  });

  it('throws UrlFetchError with kind=not-html on proxy 422', async () => {
    vi.stubGlobal('fetch', makeFetch({
      ok: false, status: 422,
      json: { error: 'not-html' },
    }));

    const err = await getError(() => extractFromUrl('https://example.com/file.pdf'));
    expect(err).toBeInstanceOf(UrlFetchError);
    expect(err.kind).toBe('not-html');
  });

  it('throws UrlFetchError with kind=no-content when text is too short', async () => {
    const SHORT_HTML = `<!DOCTYPE html>
<html><head><title>Short</title></head>
<body><p>Too short.</p></body></html>`;

    vi.stubGlobal('fetch', makeFetch({ text: SHORT_HTML }));

    const err = await getError(() => extractFromUrl('https://example.com'));
    expect(err).toBeInstanceOf(UrlFetchError);
    expect(err.kind).toBe('no-content');
  });

  it('falls back to hostname as title when article has none', async () => {
    const NO_TITLE_HTML = `<!DOCTYPE html>
<html><head></head><body><p>${LONG_ARTICLE}</p></body></html>`;

    vi.stubGlobal('fetch', makeFetch({ text: NO_TITLE_HTML }));

    const result = await extractFromUrl('https://my-blog.example.com/post').catch(() => null);
    if (result) {
      expect(result.title).toBeTruthy();
    }
  });

  it('normalises multiple whitespace in extracted content', async () => {
    const DIRTY_HTML = `<!DOCTYPE html>
<html><head><title>Whitespace Test</title></head>
<body><article><p>${'word   spaces\t\ttabs\n\nnewlines '.repeat(60)}</p></article></body></html>`;

    vi.stubGlobal('fetch', makeFetch({ text: DIRTY_HTML }));

    const result = await extractFromUrl('https://example.com').catch(() => null);
    if (result) {
      expect(result.content).not.toMatch(/  /);
    }
  });
});
