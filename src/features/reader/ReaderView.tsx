import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { useReaderStore } from '@/core/reader-engine/store';
import type { ReaderToken } from '@/core/reader-engine/types';
import { markCompleted, updateProgress } from '@/core/persistence/texts';
import { startSession, endSession } from '@/core/persistence/sessions';
import { db, DEFAULT_PREFERENCES } from '@/core/persistence/schema';
import { createHaptics } from '@/core/haptics/haptics';
import { useReduceMotion } from '@/core/accessibility/useReduceMotion';
import ReaderWord from '@/design-system/components/ReaderWord';
import GuideLines from '@/design-system/components/GuideLines';
import GestureLayer from './GestureLayer';
import SettingsDrawer from './SettingsDrawer';

/**
 * Full /reader surface. Wires the engine store to ReaderWord +
 * GuideLines + gesture handlers. Accepts tokens + optional textId
 * from the route loader so playback decouples from the text source.
 *
 * When textId is provided, progress writes are debounced (200 ms) and
 * persist to Dexie via updateProgress so the user resumes across
 * sessions.
 *
 * See `.gsd/milestones/M001/slices/S03/S03-PLAN.md`.
 */

const PROGRESS_WRITE_DEBOUNCE_MS = 200;

export interface ReaderViewProps {
  tokens: ReaderToken[];
  textId?: string;
  startIndex?: number;
}

function formatRemaining(index: number, totalTokens: number, wpm: number): string {
  const remaining = Math.max(totalTokens - index, 0);
  const totalSeconds = Math.round((remaining / wpm) * 60);
  const mm = Math.floor(totalSeconds / 60);
  const ss = totalSeconds % 60;
  return `${mm.toString().padStart(2, '0')}:${ss.toString().padStart(2, '0')}`;
}

export default function ReaderView({ tokens, textId, startIndex = 0 }: ReaderViewProps) {
  const prefs =
    useLiveQuery(() => db.preferences.get('singleton'), [], DEFAULT_PREFERENCES) ??
    DEFAULT_PREFERENCES;

  const index = useReaderStore((s) => s.index);
  const isPlaying = useReaderStore((s) => s.isPlaying);
  const totalTokens = useReaderStore((s) => s.totalTokens);
  const word = useReaderStore((s) => s.word);
  const progress = useReaderStore((s) => s.progress);
  const initEngine = useReaderStore((s) => s.initEngine);
  const destroyEngine = useReaderStore((s) => s.destroyEngine);
  const updateSettings = useReaderStore((s) => s.updateSettings);
  const seek = useReaderStore((s) => s.seek);
  const play = useReaderStore((s) => s.play);
  const pause = useReaderStore((s) => s.pause);
  const jump = useReaderStore((s) => s.jump);

  const progressWriteTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sessionIdRef = useRef<string | null>(null);
  const sessionStartRef = useRef<number>(0);
  const latestIndexRef = useRef<number>(index);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const navigate = useNavigate();
  const reduceMotion = useReduceMotion();
  const haptics = useMemo(
    () => createHaptics(prefs.haptics, reduceMotion),
    [prefs.haptics, reduceMotion],
  );

  // Keep a ref with the latest token index so cleanup callbacks can read
  // it without going stale through closures.
  useEffect(() => {
    latestIndexRef.current = index;
  }, [index]);

  useEffect(() => {
    initEngine(
      tokens,
      { wpm: prefs.wpm, punctuationPauses: prefs.punctuationPauses },
      async () => {
        haptics.finish();
        if (!textId) return;
        await markCompleted(textId);
        // End the session before navigating so CompletionView sees endedAt.
        if (sessionIdRef.current !== null) {
          const elapsedMs = Date.now() - sessionStartRef.current;
          const elapsedMin = Math.max(elapsedMs / 60000, 0.01);
          const averageWPM = Math.round(latestIndexRef.current / elapsedMin);
          await endSession(sessionIdRef.current, {
            tokensRead: latestIndexRef.current,
            averageWPM,
          });
          sessionIdRef.current = null;
        }
        navigate(`/completion/${textId}`, { replace: true });
      },
    );
    if (startIndex > 0) seek(startIndex);
    return () => destroyEngine();
    // Engine construction is intentionally tied to `tokens` only — live
    // preference changes flow through the updateSettings effect below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tokens, initEngine, destroyEngine, seek, startIndex]);

  // Start a reading session when we have a textId; end it on unmount
  // unless the finish path already ended it.
  useEffect(() => {
    if (!textId) return;
    let cancelled = false;
    void startSession(textId).then((s) => {
      if (cancelled) return;
      sessionIdRef.current = s.id;
      sessionStartRef.current = Date.now();
    });
    return () => {
      cancelled = true;
      if (sessionIdRef.current !== null) {
        const elapsedMs = Date.now() - sessionStartRef.current;
        const elapsedMin = Math.max(elapsedMs / 60000, 0.01);
        const averageWPM = Math.round(latestIndexRef.current / elapsedMin);
        void endSession(sessionIdRef.current, {
          tokensRead: latestIndexRef.current,
          averageWPM,
        });
        sessionIdRef.current = null;
      }
    };
  }, [textId]);

  // Fire a medium haptic whenever playback lands on a paragraph-break token.
  useEffect(() => {
    const token = tokens[index];
    if (token?.isParagraphBreak === true) {
      haptics.medium();
    }
    // We intentionally watch `word` too so the cue fires on each new
    // paragraph-break token render, not just on index changes.
  }, [word, index, tokens, haptics]);

  // Push preference changes into the engine without rebuilding it.
  useEffect(() => {
    updateSettings({
      wpm: prefs.wpm,
      punctuationPauses: prefs.punctuationPauses,
    });
  }, [prefs.wpm, prefs.punctuationPauses, updateSettings]);

  // Persist progress — debounced so we don't thrash IndexedDB during fast playback.
  useEffect(() => {
    if (!textId) return;
    if (progressWriteTimer.current !== null) {
      clearTimeout(progressWriteTimer.current);
    }
    progressWriteTimer.current = setTimeout(() => {
      void updateProgress(textId, index);
    }, PROGRESS_WRITE_DEBOUNCE_MS);
    return () => {
      if (progressWriteTimer.current !== null) {
        clearTimeout(progressWriteTimer.current);
      }
    };
  }, [textId, index]);

  useEffect(() => {
    function handleVisibility() {
      if (document.hidden && isPlaying) pause();
    }
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, [isPlaying, pause]);

  function handleTap() {
    haptics.soft();
    if (isPlaying) pause();
    else play();
  }

  function handleSettingsRequest() {
    setDrawerOpen(true);
  }

  const stageStyle: CSSProperties = {
    position: 'relative',
    width: '100%',
    minHeight: '100dvh',
    background: prefs.backgroundColor,
    overflow: 'hidden',
  };

  const topBarStyle: CSSProperties = {
    position: 'absolute',
    top: 52,
    left: 16,
    right: 16,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    pointerEvents: 'none',
  };

  const hintStyle: CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 8,
    letterSpacing: '0.28em',
    textTransform: 'uppercase',
    color: 'rgba(255, 255, 255, 0.22)',
    fontWeight: 500,
    opacity: index === 0 && !isPlaying ? 1 : 0,
    transition: 'opacity 180ms',
  };

  const remainingStyle: CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 9,
    letterSpacing: '0.12em',
    color: isPlaying ? 'rgba(255, 255, 255, 0.32)' : 'rgba(255, 255, 255, 0.18)',
    fontWeight: 500,
  };

  const pausedPillStyle: CSSProperties = {
    position: 'absolute',
    bottom: 46,
    left: '50%',
    transform: 'translateX(-50%)',
    padding: '8px 14px',
    borderRadius: 999,
    background: 'rgba(255, 255, 255, 0.06)',
    border: '1px solid rgba(255, 255, 255, 0.12)',
    backdropFilter: 'blur(8px)',
    fontFamily: 'var(--font-ui)',
    fontSize: 9.5,
    fontWeight: 500,
    letterSpacing: '0.22em',
    textTransform: 'uppercase',
    color: 'rgba(255, 255, 255, 0.65)',
    pointerEvents: 'none',
  };

  const progressBarStyle: CSSProperties = {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: 2,
    background: 'transparent',
    pointerEvents: 'none',
  };

  const progressFillStyle: CSSProperties = {
    width: `${progress * 100}%`,
    height: '100%',
    background: 'var(--accent)',
  };

  const paragraphGlyphStyle: CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    fontFamily: 'var(--font-reader)',
    fontSize: 48,
    color: 'var(--ink)',
    opacity: 0.25,
    pointerEvents: 'none',
  };

  const cornerButtonStyle = (side: 'left' | 'right'): CSSProperties => ({
    position: 'absolute',
    bottom: 24,
    [side]: 24,
    width: 40,
    height: 40,
    borderRadius: '50%',
    background: 'rgba(255,255,255,0.06)',
    border: '1px solid rgba(255,255,255,0.12)',
    backdropFilter: 'blur(8px)',
    color: 'rgba(255,255,255,0.55)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    padding: 0,
  });

  const currentToken = tokens[index];
  const showIdleHint = index === 0 && !isPlaying;
  const isParagraphBreak = currentToken?.isParagraphBreak === true;

  return (
    <GestureLayer
      onTap={handleTap}
      onSwipeLeft={() => jump(-5)}
      onSwipeRight={() => jump(5)}
      onSwipeUp={handleSettingsRequest}
      style={stageStyle}
    >
      <div style={topBarStyle}>
        <span style={hintStyle}>tap · pause</span>
        <span style={remainingStyle}>
          {formatRemaining(index, totalTokens, prefs.wpm)}
        </span>
      </div>

      {isParagraphBreak ? (
        <div style={paragraphGlyphStyle} aria-hidden>
          ¶
        </div>
      ) : word ? (
        <>
          {prefs.showGuideLines && <GuideLines word={word} size={prefs.fontSize} />}
          <ReaderWord
            word={word}
            size={prefs.fontSize}
            color={prefs.textColor}
            pinColor={prefs.highlightPin ? prefs.pinColor : prefs.textColor}
            fontFamily={prefs.fontFamily}
          />
        </>
      ) : null}

      {showIdleHint && <div style={pausedPillStyle}>Paused — tap to start</div>}

      {!isPlaying && (
        <>
          <button
            type="button"
            aria-label="Library"
            onClick={(e) => { e.stopPropagation(); navigate('/library'); }}
            onPointerDown={(e) => e.stopPropagation()}
            onPointerUp={(e) => e.stopPropagation()}
            style={cornerButtonStyle('left')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
            </svg>
          </button>
          <button
            type="button"
            aria-label="Restart from beginning"
            onClick={(e) => { e.stopPropagation(); pause(); seek(0); }}
            onPointerDown={(e) => e.stopPropagation()}
            onPointerUp={(e) => e.stopPropagation()}
            style={{
              position: 'absolute',
              bottom: 24,
              left: '50%',
              transform: 'translateX(-50%)',
              width: 40,
              height: 40,
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid rgba(255,255,255,0.12)',
              backdropFilter: 'blur(8px)',
              color: 'rgba(255,255,255,0.55)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              padding: 0,
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"
              stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" aria-hidden>
              <polygon points="19 20 9 12 19 4 19 20" />
              <line x1="5" y1="19" x2="5" y2="5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
          <button
            type="button"
            aria-label="Settings"
            onClick={(e) => { e.stopPropagation(); setDrawerOpen(true); }}
            onPointerDown={(e) => e.stopPropagation()}
            onPointerUp={(e) => e.stopPropagation()}
            style={cornerButtonStyle('right')}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
        </>
      )}

      <div style={progressBarStyle}>
        <div style={progressFillStyle} />
      </div>

      <span
        style={{
          position: 'absolute',
          left: -9999,
          top: -9999,
          width: 1,
          height: 1,
          overflow: 'hidden',
        }}
      >
        Pace speed reader is not compatible with screen readers. To read this
        text, use your device&apos;s built-in Read-Aloud feature on the original
        source.
      </span>

      <SettingsDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </GestureLayer>
  );
}
