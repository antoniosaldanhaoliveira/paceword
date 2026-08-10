import { normalizeWhitespace } from './clean';

export interface ExtractedArticle {
  title: string;
  content: string;
  url: string;
}

export class UrlFetchError extends Error {
  constructor(
    message: string,
    public readonly kind: 'network' | 'timeout' | 'not-html' | 'no-content' | 'blocked',
  ) {
    super(message);
    this.name = 'UrlFetchError';
  }
}

const MIN_WORD_COUNT = 50;

function hostnameTitle(rawUrl: string): string {
  try {
    return new URL(rawUrl).hostname.replace(/^www\./, '');
  } catch {
    return rawUrl;
  }
}

export async function extractFromUrl(rawUrl: string): Promise<ExtractedArticle> {
  const proxyUrl = `/api/fetch?url=${encodeURIComponent(rawUrl)}`;

  let res: Response;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 25_000);
    res = await fetch(proxyUrl, { signal: controller.signal });
    clearTimeout(timer);
  } catch (err) {
    const isAbort = err instanceof DOMException && err.name === 'AbortError';
    throw new UrlFetchError(
      isAbort ? 'Request timed out' : 'Network error',
      isAbort ? 'timeout' : 'network',
    );
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: 'unknown' })) as { error?: string };
    const kind = body.error === 'blocked' ? 'blocked'
      : body.error === 'timeout' ? 'timeout'
      : body.error === 'not-html' ? 'not-html'
      : 'network';
    throw new UrlFetchError(`Proxy returned ${res.status}: ${body.error ?? ''}`, kind);
  }

  const html = await res.text();

  const { Readability } = await import('@mozilla/readability');
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');
  const base = doc.createElement('base');
  base.href = rawUrl;
  doc.head.prepend(base);

  const reader = new Readability(doc);
  const article = reader.parse();

  if (!article?.textContent) {
    throw new UrlFetchError('Could not extract readable content', 'no-content');
  }

  const content = normalizeWhitespace(article.textContent).replace(/[ \t]+/g, ' ');
  const wordCount = content.split(/\s+/).filter(Boolean).length;

  if (wordCount < MIN_WORD_COUNT) {
    throw new UrlFetchError('Not enough content to read', 'no-content');
  }

  return {
    title: article.title?.trim() || hostnameTitle(rawUrl),
    content,
    url: rawUrl,
  };
}
