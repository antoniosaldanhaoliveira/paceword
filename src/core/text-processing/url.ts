/**
 * URL article extraction for the Pace PWA.
 *
 * Fetches the target URL through the internal fetch proxy (which handles
 * CORS), then runs Mozilla Readability to pull the article text. Returns
 * clean plain text ready for tokenization.
 *
 * The proxy endpoint is `/api/fetch?url=<encoded>` — in production this is
 * handled by nginx → the pace-proxy sidecar; in development the Vite dev
 * server proxies it to a locally-running `node proxy/server.mjs`.
 *
 * See: .gsd/milestones/M001/slices/S07/S07-PLAN.md (share target context)
 *      and pace_dev_brief.md §8 (Text Input Pipeline).
 */

import { Readability } from '@mozilla/readability';
import { normalizeWhitespace } from './clean';

const FETCH_ENDPOINT = '/api/fetch';
const MIN_WORD_COUNT = 50;

export interface ExtractedArticle {
  title: string;
  content: string;
  author?: string;
  siteName?: string;
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

function mapProxyStatus(status: number): UrlFetchError {
  if (status === 403) return new UrlFetchError('This URL is not allowed.', 'blocked');
  if (status === 404) return new UrlFetchError('Page not found.', 'network');
  if (status === 422) return new UrlFetchError('URL does not return an HTML page.', 'not-html');
  if (status === 504) return new UrlFetchError('Request timed out — the site took too long to respond.', 'timeout');
  return new UrlFetchError(`Could not reach the page (HTTP ${status}).`, 'network');
}

export async function extractFromUrl(rawUrl: string): Promise<ExtractedArticle> {
  const url = rawUrl.trim();

  const response = await fetch(`${FETCH_ENDPOINT}?url=${encodeURIComponent(url)}`).catch(
    () => { throw new UrlFetchError('Network error — check your connection.', 'network'); },
  );

  if (!response.ok) throw mapProxyStatus(response.status);

  const html = await response.text();

  const doc = new DOMParser().parseFromString(html, 'text/html');

  // Set canonical base so Readability resolves relative links in meta correctly.
  const base = doc.createElement('base');
  base.setAttribute('href', url);
  doc.head.prepend(base);

  const reader = new Readability(doc);
  const article = reader.parse();

  if (!article?.textContent) {
    throw new UrlFetchError(
      'Could not extract readable content from this page. It may require JavaScript or a login.',
      'no-content',
    );
  }

  const content = normalizeWhitespace(article.textContent);
  const wordCount = content.trim().split(/\s+/u).filter(Boolean).length;

  if (wordCount < MIN_WORD_COUNT) {
    throw new UrlFetchError(
      'Not enough text found — the page may be behind a paywall or require a login.',
      'no-content',
    );
  }

  return {
    title: article.title || new URL(url).hostname,
    content,
    ...(article.byline ? { author: article.byline } : {}),
    ...(article.siteName ? { siteName: article.siteName } : {}),
  };
}
