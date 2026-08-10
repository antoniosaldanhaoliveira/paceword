import { useEffect, useState, type CSSProperties } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { createText } from '@/core/persistence/texts';
import type { UrlFetchError } from '@/core/text-processing/url';

const STATUS_BAR_HEIGHT = 44;

type Phase = 'idle' | 'loading' | 'done' | 'error';

const stageStyle: CSSProperties = {
  width: '100%', height: '100dvh', background: 'var(--stage)',
  display: 'flex', flexDirection: 'column', overflow: 'hidden',
};
const topBarStyle: CSSProperties = {
  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  padding: '12px 20px', flexShrink: 0,
};
const cancelButtonStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 11, letterSpacing: '0.18em',
  textTransform: 'uppercase', color: 'var(--ink-2)',
  background: 'transparent', border: 'none', padding: 0, cursor: 'pointer',
};
const titleStyle: CSSProperties = {
  fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 400,
  color: 'var(--ink)', letterSpacing: '-0.02em',
};
const bodyStyle: CSSProperties = {
  flex: 1, display: 'flex', flexDirection: 'column',
  padding: '24px 20px 32px', gap: 16,
};
const labelStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 11, letterSpacing: '0.14em',
  color: 'var(--ink-3)', fontWeight: 500,
};
const inputStyle: CSSProperties = {
  width: '100%', background: 'var(--surface-2)', border: '1px solid var(--line-2)',
  borderRadius: 'var(--r-md)', padding: '12px 14px',
  fontFamily: 'var(--font-ui)', fontSize: 14, color: 'var(--ink)',
  outline: 'none', boxSizing: 'border-box',
};
const submitButtonStyle: CSSProperties = {
  marginTop: 8, height: 44, borderRadius: 'var(--r-md)', border: 'none',
  background: 'var(--accent)', color: '#fff',
  fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 500,
  cursor: 'pointer',
};
const disabledButtonStyle: CSSProperties = {
  ...submitButtonStyle, opacity: 0.4, cursor: 'default',
};
const centreStyle: CSSProperties = {
  flex: 1, display: 'flex', flexDirection: 'column',
  alignItems: 'center', justifyContent: 'center', gap: 12, padding: '0 32px',
};
const spinnerStyle: CSSProperties = {
  width: 28, height: 28, borderRadius: '50%',
  border: '2px solid var(--line-2)', borderTopColor: 'var(--accent)',
  animation: 'pace-spin 0.8s linear infinite',
};
const errorHeadStyle: CSSProperties = {
  fontFamily: 'var(--font-display)', fontSize: 18, color: 'var(--ink)',
  textAlign: 'center', letterSpacing: '-0.01em',
};
const errorBodyStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--ink-2)',
  textAlign: 'center', lineHeight: 1.5,
};
const retryButtonStyle: CSSProperties = {
  marginTop: 8, padding: '10px 24px', borderRadius: 'var(--r-md)',
  border: '1px solid var(--line-2)', background: 'transparent',
  fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--ink-2)',
  cursor: 'pointer',
};

const FRIENDLY: Record<string, string> = {
  network: 'Could not reach that URL. Check your connection and try again.',
  timeout: 'The page took too long to load. Try again.',
  'not-html': "That URL doesn't point to a webpage we can read.",
  'no-content': "We couldn't find enough text to read on that page.",
  blocked: 'That URL is not accessible.',
};

export default function UrlImportFlow() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [url, setUrl] = useState(params.get('prefill') ?? '');
  const [phase, setPhase] = useState<Phase>('idle');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = '@keyframes pace-spin { to { transform: rotate(360deg); } }';
    document.head.appendChild(style);
    return () => { document.head.removeChild(style); };
  }, []);

  async function handleSubmit() {
    const trimmed = url.trim();
    if (!trimmed) return;
    setPhase('loading');
    try {
      const { extractFromUrl } = await import('@/core/text-processing/url');
      const article = await extractFromUrl(trimmed);
      const text = await createText({ title: article.title, content: article.content, sourceType: 'url', url: article.url });
      setPhase('done');
      navigate(`/reader/${text.id}`, { replace: true });
    } catch (err) {
      const kind = (err as UrlFetchError).kind ?? 'network';
      setErrorMsg(FRIENDLY[kind] ?? 'Something went wrong. Please try again.');
      setPhase('error');
    }
  }

  const canSubmit = url.trim().length > 0 && phase === 'idle';

  return (
    <div style={stageStyle}>
      <div style={{ height: STATUS_BAR_HEIGHT, flexShrink: 0 }} />

      <div style={topBarStyle}>
        <button type="button" style={cancelButtonStyle} onClick={() => navigate(-1)}>
          Cancel
        </button>
        <div style={titleStyle}>From a URL</div>
        <div style={{ width: 50 }} />
      </div>

      {phase === 'loading' && (
        <div style={centreStyle}>
          <div style={spinnerStyle} />
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 12, color: 'var(--ink-3)', letterSpacing: '0.14em' }}>
            EXTRACTING…
          </div>
        </div>
      )}

      {phase === 'error' && (
        <div style={centreStyle}>
          <div style={errorHeadStyle}>Couldn't load article</div>
          <div style={errorBodyStyle}>{errorMsg}</div>
          <button type="button" style={retryButtonStyle} onClick={() => setPhase('idle')}>
            Try again
          </button>
        </div>
      )}

      {(phase === 'idle' || phase === 'done') && (
        <div style={bodyStyle}>
          <div style={labelStyle}>ARTICLE URL</div>
          <input
            type="url"
            inputMode="url"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            placeholder="https://example.com/article"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && canSubmit) void handleSubmit(); }}
            style={inputStyle}
            autoFocus
          />
          <button
            type="button"
            style={canSubmit ? submitButtonStyle : disabledButtonStyle}
            disabled={!canSubmit}
            onClick={() => { void handleSubmit(); }}
          >
            Extract &amp; read
          </button>
        </div>
      )}
    </div>
  );
}
