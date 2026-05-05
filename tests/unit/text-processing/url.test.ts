import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { extractFromUrl, UrlFetchError } from '@/core/text-processing/url';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeHtml(body: string, title = 'Test Article'): string {
  return `<!DOCTYPE html>
<html>
<head><title>${title}</title></head>
<body>
<article>
  <h1>${title}</h1>
  ${body}
</article>
</body>
</html>`;
}

/** Long enough to clear the MIN_WORD_COUNT = 50 threshold. */
const FULL_BODY = Array.from({ length: 10 }, (_, i) =>
  `<p>This is paragraph ${i + 1} with several words of content to ensure the minimum word count threshold is met.</p>`,
).join('\n');

function mockFetch(html: string, status = 200) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      headers: { get: () => 'text/html; charset=utf-8' },
      text: () => Promise.resolve(html),
    }),
  );
}

function mockFetchStatus(status: number) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status,
      headers: { get: () => 'text/plain' },
      text: () => Promise.resolve('error'),
    }),
  );
}

function mockFetchNetworkFailure() {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
}

async function getError(promise: Promise<unknown>): Promise<UrlFetchError> {
  const err = await promise.catch((e: unknown) => e);
  expect(err).toBeInstanceOf(UrlFetchError);
  return err as UrlFetchError;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('extractFromUrl', () => {
  beforeEach(() => {
    vi.stubGlobal('DOMParser', globalThis.DOMParser);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('extracts title and content from a well-formed article page', async () => {
    mockFetch(makeHtml(FULL_BODY, 'Great Article'));

    const result = await extractFromUrl('https://example.com/article');

    expect(result.title).toBe('Great Article');
    expect(result.content.length).toBeGreaterThan(0);
    expect(result.content).toContain('paragraph');
  });

  it('routes the fetch through /api/fetch with encoded url param', async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: { get: () => 'text/html; charset=utf-8' },
      text: () => Promise.resolve(makeHtml(FULL_BODY)),
    });
    vi.stubGlobal('fetch', fetchSpy);

    await extractFromUrl('https://example.com/my-article');

    const calledUrl: string = fetchSpy.mock.calls[0]?.[0] as string;
    expect(calledUrl).toContain('/api/fetch');
    expect(calledUrl).toContain(encodeURIComponent('https://example.com/my-article'));
  });

  it('throws UrlFetchError kind "network" on network failure', async () => {
    mockFetchNetworkFailure();
    const err = await getError(extractFromUrl('https://example.com'));
    expect(err.kind).toBe('network');
  });

  it('throws UrlFetchError kind "timeout" on HTTP 504', async () => {
    mockFetchStatus(504);
    const err = await getError(extractFromUrl('https://example.com'));
    expect(err.kind).toBe('timeout');
  });

  it('throws UrlFetchError kind "blocked" on HTTP 403', async () => {
    mockFetchStatus(403);
    const err = await getError(extractFromUrl('https://example.com'));
    expect(err.kind).toBe('blocked');
  });

  it('throws UrlFetchError kind "not-html" on HTTP 422', async () => {
    mockFetchStatus(422);
    const err = await getError(extractFromUrl('https://example.com'));
    expect(err.kind).toBe('not-html');
  });

  it('throws UrlFetchError kind "no-content" when extracted text is too short', async () => {
    mockFetch(makeHtml('<p>Hi.</p>'));
    const err = await getError(extractFromUrl('https://example.com'));
    expect(err.kind).toBe('no-content');
  });

  it('falls back to hostname as title when page title is absent', async () => {
    const html = `<!DOCTYPE html>
<html><head></head><body><article>
  ${FULL_BODY}
</article></body></html>`;
    mockFetch(html);

    const result = await extractFromUrl('https://example.com/no-title');
    expect(typeof result.title).toBe('string');
    expect(result.title.length).toBeGreaterThan(0);
  });

  it('trims and normalizes whitespace in the extracted content', async () => {
    mockFetch(makeHtml(FULL_BODY));

    const result = await extractFromUrl('https://example.com/article');

    expect(result.content).not.toMatch(/^\s/);
    expect(result.content).not.toMatch(/\s$/);
    expect(result.content).not.toMatch(/\n{3,}/);
  });
});
