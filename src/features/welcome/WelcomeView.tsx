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
          <svg width="17" height="17" viewBox="0 0 814 1000" fill="currentColor" aria-hidden>
            <path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76 0-103.7 40.8-165.9 40.8s-105-57.8-155.5-127.4C46 790.7 0 663 0 541.8c0-207.5 135.4-317.3 269-317.3 70.1 0 128.4 46.4 172.5 46.4 42.8 0 109.7-49.1 189.2-49.1 30.3 0 130.9 2.6 198.3 99.2zm-234-181.5c31.1-36.9 53.1-88.1 53.1-139.3 0-7.1-.6-14.3-1.9-20.1-50.6 1.9-110.8 33.7-147.1 75.8-28.5 32.4-55.1 83.6-55.1 135.5 0 7.8 1.3 15.6 1.9 18.1 3.2.6 8.4 1.3 13.6 1.3 45.4 0 102.5-30.4 135.5-71.3z"/>
          </svg>
          Continue with Apple
        </button>
        <button type="button" style={{ ...primaryButtonStyle, background: 'var(--surface-2)', color: 'var(--ink)' }} onClick={handleStart}>
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
