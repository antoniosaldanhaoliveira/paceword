/**
 * Pace PWA — Continue Reading Card
 *
 * Hero card pinned to the top of the Library screen whenever there is at
 * least one text with in-progress reading (0 < progress < 1). Tapping the
 * card resumes the reader at the saved token position. Pure-visual: progress
 * and minutes-left are derived solely from the supplied `ReadingText` and
 * the caller-supplied `wpm` (the user's live preference). Rendered as a
 * styled `<button>` so keyboard and screen-reader users get first-class access.
 *
 * See: .gsd/milestones/M001/slices/S03/S03-PLAN.md §6.2 (Library screen —
 *      Continue card) and the design handoff at
 *      pace-design/pace/project/screens/library.jsx lines 52-86.
 */
import type { CSSProperties } from 'react';
import type { ReadingText } from '@/core/persistence/schema';

export interface ContinueCardProps {
  text: ReadingText;
  wpm: number;
  onOpen: () => void;
}

function clampProgress(value: number): number {
  if (Number.isNaN(value) || value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

const containerStyle: CSSProperties = {
  width: '100%',
  background: 'linear-gradient(145deg, #1A1418 0%, #0F0A0C 100%)',
  borderRadius: 'var(--r-lg)',
  border: '1px solid var(--line-2)',
  padding: 14,
  position: 'relative',
  overflow: 'hidden',
  cursor: 'pointer',
  textAlign: 'left',
  color: 'var(--ink)',
  font: 'inherit',
  appearance: 'none',
  WebkitAppearance: 'none',
};

const stripeStyle: CSSProperties = {
  position: 'absolute', left: 0, top: 0, bottom: 0, width: 3,
  background: 'var(--accent)',
};

const eyebrowStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 8, letterSpacing: '0.2em',
  color: 'var(--accent)', fontWeight: 500, textTransform: 'uppercase',
};

const titleStyle: CSSProperties = {
  fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 400,
  color: 'var(--ink)', marginTop: 10, letterSpacing: '-0.01em',
};

const progressRowStyle: CSSProperties = {
  display: 'flex', alignItems: 'center', marginTop: 12, gap: 10,
};

const trackStyle: CSSProperties = {
  flex: 1, height: 2, background: 'var(--line-2)',
  borderRadius: 1, overflow: 'hidden',
};

const metaStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 9, color: 'var(--ink-2)',
  letterSpacing: '0.08em', fontWeight: 500,
};

function ContinueCard({ text, wpm, onOpen }: ContinueCardProps) {
  const safeWordCount = Math.max(text.wordCount, 1);
  const progress = clampProgress(text.currentTokenIndex / safeWordCount);
  const wordsRemaining = Math.max(text.wordCount - text.currentTokenIndex, 0);
  const minsLeft = Math.ceil(wordsRemaining / wpm);
  const percent = Math.round(progress * 100);

  const fillStyle: CSSProperties = {
    width: `${progress * 100}%`,
    height: '100%',
    background: 'var(--accent)',
  };

  return (
    <button type="button" onClick={onOpen} style={containerStyle}>
      <div style={stripeStyle} />
      <div style={eyebrowStyle}>Continue reading</div>
      <div style={titleStyle}>{text.title}</div>
      <div style={progressRowStyle}>
        <div style={trackStyle}>
          <div style={fillStyle} />
        </div>
        <div style={metaStyle}>{`${percent}% · ${minsLeft} MIN LEFT`}</div>
      </div>
    </button>
  );
}

export default ContinueCard;
