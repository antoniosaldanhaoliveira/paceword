/**
 * Pace PWA — Library screen
 *
 * Root of the `/library` route. Composes `ContinueCard`, `TextRow`, and `Fab`
 * over a Dexie live-query of `listTexts()`. The newest in-progress text is
 * surfaced in the Continue card; every other text (including completed ones)
 * lands in the list below. Empty state invites the user to add their first
 * text. All navigation is handled via react-router.
 *
 * See: .gsd/milestones/M001/slices/S03/S03-PLAN.md §6.2
 *      (Library screen — layout, filtering, and navigation rules).
 */
import type { CSSProperties } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useNavigate } from 'react-router-dom';

import { listTexts, deleteText } from '@/core/persistence/texts';
import { db, DEFAULT_PREFERENCES, type ReadingText } from '@/core/persistence/schema';
import Wordmark from '@/design-system/components/Wordmark';
import Eyebrow from '@/design-system/components/Eyebrow';

import ContinueCard from './ContinueCard';
import TextRow from './TextRow';
import Fab from './Fab';

const STATUS_BAR_HEIGHT = 44;
const HEADER_PADDING = '12px 20px 20px';
const SCROLL_PADDING = '0 20px 100px';

const stageStyle: CSSProperties = {
  width: '100%', height: '100%', background: 'var(--stage)',
  display: 'flex', flexDirection: 'column', position: 'relative',
  overflow: 'hidden',
};

const headerStyle: CSSProperties = {
  display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
  padding: HEADER_PADDING, flexShrink: 0,
};

const headerRightStyle: CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 14,
};

const countStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 9.5, letterSpacing: '0.2em',
  color: 'var(--ink-3)', fontWeight: 500,
};

const gearButtonStyle: CSSProperties = {
  background: 'transparent', border: 'none', padding: 0,
  cursor: 'pointer', display: 'inline-flex', alignItems: 'center',
};

const scrollStyle: CSSProperties = {
  flex: 1, overflow: 'auto', padding: SCROLL_PADDING,
};

const emptyWrapStyle: CSSProperties = {
  display: 'flex', flexDirection: 'column', alignItems: 'center',
  justifyContent: 'center', gap: 20, padding: '80px 0',
};

const emptyCopyStyle: CSSProperties = {
  fontFamily: 'var(--font-display)', fontStyle: 'italic',
  fontSize: 18, color: 'var(--ink-2)', textAlign: 'center',
};

const emptyButtonStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 500,
  letterSpacing: '0.18em', textTransform: 'uppercase',
  padding: '10px 18px', borderRadius: 'var(--r-sm)',
  background: 'var(--accent)', color: '#fff', border: 'none',
  cursor: 'pointer',
};

function findInProgress(texts: ReadingText[]): ReadingText | undefined {
  return texts.find((t) => !t.isCompleted && t.currentTokenIndex > 0 && t.wordCount > 0);
}

function GearIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
      stroke="var(--ink-2)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
      aria-hidden>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33h0a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51h0a1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82v0a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  );
}

function LibraryView() {
  const navigate = useNavigate();
  // `useLiveQuery` returns `undefined` on the first synchronous render before
  // Dexie has resolved the query. We render a lean skeleton (stage + wordmark)
  // during that window so the user never sees a flash of "0 TEXTS" / empty.
  const texts = useLiveQuery(() => listTexts(), []);
  const prefs = useLiveQuery(() => db.preferences.get('singleton'), [], DEFAULT_PREFERENCES) ?? DEFAULT_PREFERENCES;

  if (texts === undefined) {
    return (
      <div style={stageStyle}>
        <div style={{ height: STATUS_BAR_HEIGHT, flexShrink: 0 }} />
        <div style={headerStyle}>
          <Wordmark size="header" as="h1" />
        </div>
      </div>
    );
  }

  const inProgress = findInProgress(texts);
  const otherTexts = inProgress ? texts.filter((t) => t !== inProgress) : texts;

  const handleOpen = (id: string) => navigate(`/reader/${id}`);
  const handleDelete = async (id: string): Promise<void> => {
    await deleteText(id);
  };

  return (
    <div style={stageStyle}>
      <div style={{ height: STATUS_BAR_HEIGHT, flexShrink: 0 }} />

      <div style={headerStyle}>
        <Wordmark size="header" as="h1" />
        <div style={headerRightStyle}>
          <div style={countStyle}>{`${texts.length} TEXTS`}</div>
          <button type="button" aria-label="Open settings"
            style={gearButtonStyle} onClick={() => navigate('/settings')}>
            <GearIcon />
          </button>
        </div>
      </div>

      <div style={scrollStyle}>
        {inProgress && (
          <ContinueCard text={inProgress} wpm={prefs.wpm} onOpen={() => handleOpen(inProgress.id)} />
        )}

        <Eyebrow style={{ marginTop: 32, marginBottom: 4, paddingLeft: 2, fontSize: 9.5 }}>
          LIBRARY
        </Eyebrow>

        {texts.length === 0 ? (
          <div style={emptyWrapStyle}>
            <div style={emptyCopyStyle}>Nothing to read yet.</div>
            <button type="button" style={emptyButtonStyle} onClick={() => navigate('/new')}>
              Add your first text
            </button>
          </div>
        ) : (
          otherTexts.map((t) => (
            <TextRow
              key={t.id}
              text={t}
              onOpen={() => handleOpen(t.id)}
              onDelete={() => { void handleDelete(t.id); }}
            />
          ))
        )}
      </div>

      <Fab onClick={() => navigate('/new')} label="Add a new text" />
    </div>
  );
}

export default LibraryView;
