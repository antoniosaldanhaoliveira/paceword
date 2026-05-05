/**
 * Pace PWA — URL import flow
 *
 * Full-screen stage for the `/new/url` route. Accepts a URL, fetches the
 * page through the internal proxy, extracts article text with Readability,
 * saves to library via `createText`, and opens the reader. Handles common
 * failure modes (timeout, paywall, non-HTML, JS-only pages) with plain-
 * language messages.
 *
 * See: pace_dev_brief.md §8 (Text Input Pipeline — URL extraction, v2 item
 *      pulled forward).
 */
import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createText } from '@/core/persistence/texts';
import { UrlFetchError } from '@/core/text-processing/url';

type FlowState =
  | 'idle'
  | 'fetching'
  | 'extracting'
  | 'success'
  | 'error';

const SUCCESS_NAV_DELAY_MS = 400;
const SPINNER_KEYFRAMES = '@keyframes pace-spin { to { transform: rotate(360deg); } }';

const stageStyle: CSSProperties = {
  width: '100%',
  height: '100dvh',
  background: 'var(--stage)',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: 24,
  gap: 16,
  textAlign: 'center',
};

const headingStyle: CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontStyle: 'italic',
  fontSize: 18,
  color: 'var(--ink)',
  margin: 0,
  maxWidth: 320,
  lineHeight: 1.4,
};

const subStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)',
  fontSize: 12,
  color: 'var(--ink-3)',
  margin: 0,
  maxWidth: 320,
};

const inputStyle: CSSProperties = {
  width: '100%',
  maxWidth: 360,
  height: 44,
  borderRadius: 'var(--r-md)',
  border: '1px solid var(--line-2)',
  background: 'var(--surface)',
  color: 'var(--ink)',
  fontFamily: 'var(--font-ui)',
  fontSize: 13,
  padding: '0 14px',
  outline: 'none',
  textAlign: 'left',
};

const primaryButtonStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)',
  fontSize: 11,
  fontWeight: 500,
  letterSpacing: '0.18em',
  textTransform: 'uppercase',
  height: 36,
  padding: '0 18px',
  borderRadius: 'var(--r-md)',
  background: 'var(--accent)',
  color: '#fff',
  border: 'none',
  cursor: 'pointer',
};

const ghostButtonStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)',
  fontSize: 11,
  letterSpacing: '0.18em',
  textTransform: 'uppercase',
  color: 'var(--ink-2)',
  background: 'transparent',
  border: 'none',
  padding: 0,
  cursor: 'pointer',
};

const spinnerStyle: CSSProperties = {
  width: 32,
  height: 32,
  borderRadius: '50%',
  border: '2px solid var(--line)',
  borderTopColor: 'var(--accent)',
  animation: 'pace-spin 0.9s linear infinite',
};

const buttonRowStyle: CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: 12,
};

const errorHeadingStyle: CSSProperties = { ...headingStyle, color: 'var(--accent)' };

function isValidUrl(raw: string): boolean {
  try {
    const { protocol } = new URL(raw.trim());
    return protocol === 'http:' || protocol === 'https:';
  } catch {
    return false;
  }
}

export default function UrlImportFlow(): JSX.Element {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [state, setState] = useState<FlowState>('idle');
  const [urlInput, setUrlInput] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Pre-fill from /share?url= query parameter.
  useEffect(() => {
    const prefill = params.get('prefill');
    if (prefill) setUrlInput(prefill);
  }, [params]);

  const canSubmit = isValidUrl(urlInput) && state === 'idle';

  const handleExtract = async (): Promise<void> => {
    if (!canSubmit) return;
    setErrorMessage('');
    setState('fetching');

    try {
      const { extractFromUrl } = await import('@/core/text-processing/url');
      setState('extracting');
      const article = await extractFromUrl(urlInput.trim());

      const text = await createText({
        title: article.title,
        content: article.content,
        sourceType: 'url',
        ...(article.author ? { author: article.author } : {}),
        url: urlInput.trim(),
      });

      setState('success');
      window.setTimeout(
        () => navigate(`/reader/${text.id}`, { replace: true }),
        SUCCESS_NAV_DELAY_MS,
      );
    } catch (err) {
      const message =
        err instanceof UrlFetchError
          ? err.message
          : 'Something went wrong. Please try again.';
      setErrorMessage(message);
      setState('error');
    }
  };

  const resetToIdle = (): void => {
    setState('idle');
    setErrorMessage('');
  };

  return (
    <div style={stageStyle}>
      <style>{SPINNER_KEYFRAMES}</style>

      {state === 'idle' && (
        <>
          <p style={headingStyle}>Paste an article URL.</p>
          <input
            ref={inputRef}
            type="url"
            value={urlInput}
            placeholder="https://example.com/article"
            inputMode="url"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            style={inputStyle}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && canSubmit) void handleExtract(); }}
          />
          <div style={buttonRowStyle}>
            <button
              type="button"
              style={{ ...primaryButtonStyle, opacity: canSubmit ? 1 : 0.4, cursor: canSubmit ? 'pointer' : 'not-allowed' }}
              disabled={!canSubmit}
              onClick={() => { void handleExtract(); }}
            >
              Extract article
            </button>
            <button type="button" style={ghostButtonStyle} onClick={() => navigate(-1)}>
              Cancel
            </button>
          </div>
          <p style={subStyle}>Works best on text-heavy articles. Paywalled pages may not extract.</p>
        </>
      )}

      {(state === 'fetching' || state === 'extracting') && (
        <>
          <div style={spinnerStyle} />
          <p style={headingStyle}>
            {state === 'fetching' ? 'Fetching page…' : 'Extracting article…'}
          </p>
        </>
      )}

      {state === 'error' && (
        <>
          <p style={errorHeadingStyle}>¶</p>
          <p style={headingStyle}>{errorMessage}</p>
          <div style={buttonRowStyle}>
            <button type="button" style={primaryButtonStyle} onClick={resetToIdle}>
              Try another URL
            </button>
            <button type="button" style={ghostButtonStyle} onClick={() => navigate(-1)}>
              Back
            </button>
          </div>
        </>
      )}

      {state === 'success' && (
        <p style={headingStyle}>Saved. Opening reader…</p>
      )}
    </div>
  );
}
