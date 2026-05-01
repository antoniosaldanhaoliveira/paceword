import { useNavigate } from 'react-router-dom';
import type { CSSProperties } from 'react';
import Wordmark from '@/design-system/components/Wordmark';
import { setPreference } from '@/core/persistence/preferences';

/**
 * First-run Welcome screen. Per D022, Apple + email buttons are visible
 * for layout fidelity but all three actions route the user into
 * anonymous-start. v2 will wire real auth.
 *
 * See `.gsd/milestones/M001/slices/S03/S03-PLAN.md`.
 */

export default function WelcomeView() {
  const navigate = useNavigate();

  async function handleStart() {
    await setPreference('hasCompletedWelcome', true);
    navigate('/library', { replace: true });
  }

  const frameStyle: CSSProperties = {
    minHeight: '100dvh',
    background: 'var(--stage)',
    display: 'flex',
    flexDirection: 'column',
    padding: '54px 24px 34px',
    position: 'relative',
    overflow: 'hidden',
  };

  const heroStyle: CSSProperties = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
  };

  const subtitleStyle: CSSProperties = {
    fontFamily: 'var(--font-display)',
    fontStyle: 'italic',
    fontWeight: 300,
    fontSize: 16,
    color: 'var(--ink-2)',
    marginTop: 20,
    letterSpacing: '-0.01em',
  };

  const metaRowStyle: CSSProperties = {
    marginTop: 64,
    display: 'flex',
    gap: 14,
    alignItems: 'center',
  };

  const metaLabelStyle: CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 8.5,
    letterSpacing: '0.22em',
    color: 'var(--ink-3)',
    fontWeight: 500,
  };

  const metaDotStyle: CSSProperties = {
    width: 2,
    height: 2,
    borderRadius: '50%',
    background: 'var(--ink-3)',
  };

  const actionStackStyle: CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
    marginBottom: 14,
  };

  const primaryButtonStyle: CSSProperties = {
    height: 44,
    borderRadius: 'var(--r-md)',
    border: 'none',
    background: 'var(--ink)',
    color: '#0A0A0A',
    fontFamily: 'var(--font-ui)',
    fontSize: 13,
    fontWeight: 500,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    cursor: 'pointer',
  };

  const secondaryButtonStyle: CSSProperties = {
    height: 44,
    borderRadius: 'var(--r-md)',
    border: '1px solid var(--line-2)',
    background: 'transparent',
    color: 'var(--ink)',
    fontFamily: 'var(--font-ui)',
    fontSize: 13,
    fontWeight: 500,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    cursor: 'pointer',
  };

  const ghostButtonStyle: CSSProperties = {
    background: 'transparent',
    border: 'none',
    color: 'var(--ink-2)',
    fontFamily: 'var(--font-ui)',
    fontSize: 12,
    fontWeight: 400,
    padding: '12px 0 4px',
    cursor: 'pointer',
  };

  const legalStyle: CSSProperties = {
    fontFamily: 'var(--font-ui)',
    fontSize: 9.5,
    color: 'var(--ink-3)',
    textAlign: 'center',
    lineHeight: 1.5,
    padding: '0 20px',
  };

  return (
    <div style={frameStyle}>
      <div style={heroStyle}>
        <Wordmark size="hero" as="h1" />
        <div style={subtitleStyle}>Read one word at a time.</div>

        <div style={metaRowStyle}>
          <span style={metaLabelStyle}>FOCUSED</span>
          <span style={metaDotStyle} aria-hidden />
          <span style={metaLabelStyle}>NO STREAKS</span>
          <span style={metaDotStyle} aria-hidden />
          <span style={metaLabelStyle}>LOCAL-FIRST</span>
        </div>
      </div>

      <div style={actionStackStyle}>
        <button type="button" style={primaryButtonStyle} onClick={handleStart}>
          <svg width="13" height="15" viewBox="0 0 13 15" fill="currentColor" aria-hidden>
            <path d="M10.476 7.914c.014-1.33.712-2.563 1.85-3.265a4.09 4.09 0 0 0-3.224-1.742c-1.362-.143-2.673.812-3.365.812-.703 0-1.767-.797-2.911-.774C1.3 2.98.09 3.89-.5 5.22c-1.234 2.134-.317 5.285.882 7.017.587.845 1.28 1.793 2.192 1.759.882-.035 1.213-.567 2.28-.567 1.054 0 1.36.567 2.28.546 1.007-.018 1.605-.862 2.196-1.71a8.84 8.84 0 0 0 .963-1.975 3.96 3.96 0 0 1-2.817-3.376ZM8.41 1.94A3.938 3.938 0 0 0 9.315 0a4.01 4.01 0 0 0-2.594 1.34 3.748 3.748 0 0 0-.926 2.72A3.316 3.316 0 0 0 8.41 1.94Z" />
          </svg>
          Continue with Apple
        </button>
        <button type="button" style={secondaryButtonStyle} onClick={handleStart}>
          Continue with email
        </button>
        <button type="button" style={ghostButtonStyle} onClick={handleStart}>
          Use without an account
        </button>
      </div>

      <div style={legalStyle}>
        By continuing, you accept our{' '}
        <span style={{ color: 'var(--ink-2)', textDecoration: 'underline' }}>Terms</span>{' '}
        and{' '}
        <span style={{ color: 'var(--ink-2)', textDecoration: 'underline' }}>Privacy Notice</span>.
      </div>
    </div>
  );
}
