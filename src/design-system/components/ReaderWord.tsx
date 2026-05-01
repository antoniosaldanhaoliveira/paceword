import { useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { pinIndex } from '@/core/reader-engine/pin';

/**
 * Single-word reader surface. The pin character's CENTER sits on the
 * stage's vertical centerline so the eye locks onto it without drift.
 * We measure the pin glyph at runtime and translate the word container
 * left by half its width.
 *
 * The optional radial-gradient glow behind the pin character was
 * removed — the accent-colored pin glyph alone reads cleanly without
 * the extra ornament.
 *
 * See `.gsd/milestones/M001/slices/S02/tasks/T03-PLAN.md`.
 */

export interface ReaderWordProps {
  word: string;
  size?: number;
  color?: string;
  pinColor?: string;
  fontFamily?: string;
}

const FALLBACK_PIN_WIDTH_RATIO = 0.4;

export default function ReaderWord({
  word,
  size = 54,
  color = 'var(--ink)',
  pinColor = 'var(--accent)',
  fontFamily,
}: ReaderWordProps) {
  const idx = pinIndex(word);
  const left = word.slice(0, idx);
  const pin = word[idx] ?? '';
  const right = word.slice(idx + 1);

  const pinRef = useRef<HTMLSpanElement>(null);
  const [pinWidth, setPinWidth] = useState<number>(size * FALLBACK_PIN_WIDTH_RATIO);

  useLayoutEffect(() => {
    let cancelled = false;
    const measure = () => {
      if (cancelled) return;
      const el = pinRef.current;
      if (!el) return;
      setPinWidth(el.getBoundingClientRect().width);
    };
    measure();
    void document.fonts?.ready.then(measure);
    return () => {
      cancelled = true;
    };
  }, [pin, size]);

  const rootStyle: CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: `translate(-${pinWidth / 2}px, -50%)`,
    display: 'flex',
    alignItems: 'baseline',
    fontFamily: fontFamily ?? 'var(--font-reader)',
    fontWeight: 400,
    fontSize: size,
    color,
    lineHeight: 1,
    letterSpacing: '0.005em',
    pointerEvents: 'none',
  };

  const leftStyle: CSSProperties = {
    position: 'absolute',
    right: '100%',
    whiteSpace: 'pre',
  };

  const pinStyle: CSSProperties = {
    color: pinColor,
    position: 'relative',
  };

  return (
    <div style={rootStyle} aria-hidden>
      {left && <span style={leftStyle}>{left}</span>}
      <span ref={pinRef} style={pinStyle}>
        {pin}
      </span>
      {right && <span>{right}</span>}
    </div>
  );
}
