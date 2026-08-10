/**
 * Pace PWA — Settings screen
 *
 * Full-screen settings view reached from the Library gear icon. Mirrors the
 * design handoff at `pace-design/pace/project/screens/settings.jsx` with the
 * v1 subset per D032: the ACCOUNT section is omitted, and ABOUT surfaces
 * only Version (no Privacy policy / Terms / Acknowledgements).
 *
 * All user-facing values are bound to the `UserPreferences` singleton via
 * `@/core/persistence/preferences`. Reads flow through a Dexie live query so
 * writes in this screen re-render without manual refresh. Slider and Toggle
 * are bespoke local components (kept inline to avoid needless indirection).
 * Font/color pickers use native primitives — a modal list and
 * `<input type="color">` — to stay within S05's v1 scope.
 *
 * See: .gsd/milestones/M001/slices/S05/S05-PLAN.md
 */

import { useRef, useState, type CSSProperties, type PointerEvent, type ReactNode } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useNavigate } from 'react-router-dom';

import { db, DEFAULT_PREFERENCES, type UserPreferences } from '@/core/persistence/schema';
import { setPreference, resetPreferences } from '@/core/persistence/preferences';
import Eyebrow from '@/design-system/components/Eyebrow';
import ReaderWord from '@/design-system/components/ReaderWord';

const STATUS_BAR_HEIGHT = 44;
const WPM_MIN = 150;
const WPM_MAX = 800;
const WPM_STEP = 10;
const FONT_SIZE_MIN = 36;
const FONT_SIZE_MAX = 120;
const FONT_SIZE_STEP = 2;
const APP_VERSION = '1.0.0 · 240';
const FONT_OPTIONS: ReadonlyArray<string> = [
  'EB Garamond', 'Fraunces', 'Georgia', 'Inter', 'JetBrains Mono',
];

// ---------- preferences live query ----------

function usePreferences(): UserPreferences {
  const prefs = useLiveQuery(() => db.preferences.get('singleton'), [], DEFAULT_PREFERENCES);
  return prefs ?? DEFAULT_PREFERENCES;
}

// ---------- Slider ----------

interface SliderProps {
  value: number; min: number; max: number; step: number;
  onChange: (next: number) => void;
}

function clampToStep(raw: number, min: number, max: number, step: number): number {
  const bounded = Math.min(Math.max(raw, min), max);
  const snapped = Math.round((bounded - min) / step) * step + min;
  return Math.min(Math.max(snapped, min), max);
}

function Slider({ value, min, max, step, onChange }: SliderProps) {
  const trackRef = useRef<HTMLDivElement | null>(null);
  const percent = ((value - min) / (max - min)) * 100;

  const rootStyle: CSSProperties = {
    position: 'relative', height: 12, width: '100%', touchAction: 'none', cursor: 'pointer',
  };
  const trackStyle: CSSProperties = {
    position: 'absolute', top: 5, left: 0, right: 0, height: 2, background: 'var(--line-2)',
  };
  const fillStyle: CSSProperties = {
    position: 'absolute', top: 5, left: 0, height: 2,
    width: `${percent}%`, background: 'var(--accent)',
  };
  const thumbStyle: CSSProperties = {
    position: 'absolute', top: 1, left: `calc(${percent}% - 5px)`,
    width: 10, height: 10, borderRadius: '50%',
    background: 'var(--accent)', border: '2px solid var(--reader)',
    boxShadow: '0 0 0 1px var(--accent)',
  };

  function updateFromEvent(event: PointerEvent<HTMLDivElement>): void {
    const node = trackRef.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    if (rect.width <= 0) return;
    const ratio = (event.clientX - rect.left) / rect.width;
    const next = clampToStep(min + ratio * (max - min), min, max, step);
    if (next !== value) onChange(next);
  }

  function handlePointerDown(event: PointerEvent<HTMLDivElement>): void {
    event.currentTarget.setPointerCapture(event.pointerId);
    updateFromEvent(event);
  }
  function handlePointerMove(event: PointerEvent<HTMLDivElement>): void {
    if (event.buttons === 0) return;
    updateFromEvent(event);
  }

  return (
    <div ref={trackRef} style={rootStyle}
      onPointerDown={handlePointerDown} onPointerMove={handlePointerMove}
      role="slider" aria-valuemin={min} aria-valuemax={max} aria-valuenow={value}>
      <div style={trackStyle} />
      <div style={fillStyle} />
      <div style={thumbStyle} />
    </div>
  );
}

// ---------- Toggle ----------

interface ToggleProps {
  on: boolean; label: string; onChange: (next: boolean) => void;
}

function Toggle({ on, label, onChange }: ToggleProps) {
  const rootStyle: CSSProperties = {
    width: 28, height: 16, borderRadius: 'var(--r-sm)',
    background: on ? 'var(--accent)' : 'var(--line-2)',
    position: 'relative', transition: 'background 150ms ease',
    flexShrink: 0, border: 'none', padding: 0, cursor: 'pointer',
  };
  const knobStyle: CSSProperties = {
    position: 'absolute', top: 2, left: on ? 14 : 2,
    width: 12, height: 12, borderRadius: 'var(--r-sm)',
    background: '#fff', transition: 'left 150ms ease',
  };
  return (
    <button type="button" role="switch" aria-checked={on} aria-label={label}
      style={rootStyle} onClick={() => onChange(!on)}>
      <span style={knobStyle} />
    </button>
  );
}

// ---------- Row + Chevron ----------

interface SettingRowProps {
  label: ReactNode; right?: ReactNode; last?: boolean; onClick?: () => void;
}

const ROW_LABEL_STYLE: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 400, color: 'var(--ink)',
};

function rowStyle(last: boolean, clickable: boolean): CSSProperties {
  return {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    height: 44, borderBottom: last ? 'none' : '1px solid var(--line)',
    cursor: clickable ? 'pointer' : 'default',
    background: 'transparent', border: 'none', borderRadius: 0,
    padding: 0, width: '100%', textAlign: 'left', color: 'inherit', font: 'inherit',
  };
}

function SettingRow({ label, right, last = false, onClick }: SettingRowProps) {
  const content = (
    <>
      <div style={ROW_LABEL_STYLE}>{label}</div>
      <div>{right}</div>
    </>
  );
  if (onClick) {
    return (
      <button type="button" style={{ ...rowStyle(last, true), borderBottom: last ? 'none' : '1px solid var(--line)' }} onClick={onClick}>
        {content}
      </button>
    );
  }
  return <div style={rowStyle(last, false)}>{content}</div>;
}

function Chevron() {
  return (
    <svg width="10" height="14" viewBox="0 0 10 14" fill="none"
      stroke="var(--ink-3)" strokeWidth="1.6" strokeLinecap="round" aria-hidden>
      <path d="M2 1l6 6-6 6" />
    </svg>
  );
}

// ---------- Font picker ----------

interface FontPickerProps {
  current: string; onPick: (font: string) => void; onClose: () => void;
}

function FontPicker({ current, onPick, onClose }: FontPickerProps) {
  const backdropStyle: CSSProperties = {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
    display: 'flex', alignItems: 'flex-end', justifyContent: 'center', zIndex: 40,
  };
  const sheetStyle: CSSProperties = {
    width: '100%', maxWidth: 480, background: 'var(--surface-2)',
    borderTopLeftRadius: 'var(--r-lg)', borderTopRightRadius: 'var(--r-lg)',
    padding: '18px 20px 28px', borderTop: '1px solid var(--line-2)',
  };
  const headerStyle: CSSProperties = {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12,
  };
  const titleStyle: CSSProperties = {
    fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 500, color: 'var(--ink)',
  };
  const closeStyle: CSSProperties = {
    fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.2em',
    color: 'var(--ink-2)', background: 'transparent', border: 'none',
    cursor: 'pointer', padding: 0,
  };
  const baseItemStyle: CSSProperties = {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    width: '100%', padding: '12px 0',
    background: 'transparent', border: 'none', cursor: 'pointer',
    fontSize: 15, textAlign: 'left',
  };
  return (
    <div style={backdropStyle} onClick={onClose} role="dialog" aria-label="Choose font">
      <div style={sheetStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <div style={titleStyle}>Default font</div>
          <button type="button" style={closeStyle} onClick={onClose}>CLOSE</button>
        </div>
        {FONT_OPTIONS.map((font, i) => {
          const selected = font === current;
          return (
            <button key={font} type="button"
              style={{
                ...baseItemStyle,
                color: selected ? 'var(--accent)' : 'var(--ink)',
                fontFamily: font,
                borderBottom: i === FONT_OPTIONS.length - 1 ? 'none' : '1px solid var(--line)',
              }}
              onClick={() => onPick(font)}>
              <span>{font}</span>
              {selected && (
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, letterSpacing: '0.2em' }}>
                  ACTIVE
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------- Data side effects ----------

async function handleExport(): Promise<void> {
  const [texts, sessions, preferencesRows] = await Promise.all([
    db.texts.toArray(), db.sessions.toArray(), db.preferences.toArray(),
  ]);
  const payload = { exportedAt: Date.now(), texts, sessions, preferences: preferencesRows };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `pace-library-${new Date().toISOString().slice(0, 10)}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

// ---------- shared styles for main view ----------

const STAGE_STYLE: CSSProperties = { width: '100%', height: '100%', minHeight: '100dvh', background: 'var(--stage)', display: 'flex', flexDirection: 'column', overflow: 'hidden' };
const HEADER_STYLE: CSSProperties = { padding: '10px 20px 16px', display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 };
const BACK_BTN_STYLE: CSSProperties = { background: 'transparent', border: 'none', padding: 0, cursor: 'pointer', display: 'inline-flex', alignItems: 'center' };
const TITLE_STYLE: CSSProperties = { fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 400, color: 'var(--ink)', letterSpacing: '-0.02em' };
const SCROLL_STYLE: CSSProperties = { flex: 1, overflow: 'auto', padding: '4px 20px 80px' };
const SECTION_STYLE: CSSProperties = { marginTop: 28 };
const SLIDER_ROW_STYLE: CSSProperties = { padding: '10px 0', borderBottom: '1px solid var(--line)' };
const SLIDER_HEADER_STYLE: CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' };
const SLIDER_LABEL_STYLE: CSSProperties = { fontFamily: 'var(--font-ui)', fontSize: 13, color: 'var(--ink)' };
const SLIDER_VALUE_STYLE: CSSProperties = { fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-2)', letterSpacing: '0.04em' };
const PREVIEW_TILE_BASE_STYLE: CSSProperties = { height: 100, borderRadius: 'var(--r-lg)', border: '1px solid var(--line-2)', position: 'relative', overflow: 'hidden', marginBottom: 14 };
const PREVIEW_EYEBROW_STYLE: CSSProperties = { position: 'absolute', left: 10, top: 10, fontFamily: 'var(--font-mono)', fontSize: 8, letterSpacing: '0.22em', color: 'rgba(255,255,255,0.3)' };
const SWATCH_RIGHT_STYLE: CSSProperties = { display: 'flex', alignItems: 'center', gap: 10 };
const SWATCH_HEX_STYLE: CSSProperties = { fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--ink-2)', letterSpacing: '0.06em' };
const HIDDEN_COLOR_INPUT_STYLE: CSSProperties = { position: 'absolute', opacity: 0, pointerEvents: 'none', width: 0, height: 0 };
const VERSION_STYLE: CSSProperties = { fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--ink-2)', letterSpacing: '0.04em' };
const FONT_RIGHT_STYLE: CSSProperties = { display: 'flex', alignItems: 'center', gap: 6 };

function renderSwatch(color: string): ReactNode {
  return (
    <div style={SWATCH_RIGHT_STYLE}>
      <div style={SWATCH_HEX_STYLE}>{color.toUpperCase()}</div>
      <div style={{
        width: 24, height: 24, borderRadius: 'var(--r-sm)',
        background: color, border: '1px solid var(--line-2)',
      }} />
    </div>
  );
}

// ---------- Main view ----------

export default function SettingsView() {
  const navigate = useNavigate();
  const prefs = usePreferences();
  const [isFontPickerOpen, setFontPickerOpen] = useState<boolean>(false);
  const bgColorRef = useRef<HTMLInputElement | null>(null);
  const textColorRef = useRef<HTMLInputElement | null>(null);
  const pinColorRef = useRef<HTMLInputElement | null>(null);

  async function handleClearAll(): Promise<void> {
    const confirmed = window.confirm(
      'Delete all texts, sessions, and preferences? This cannot be undone.',
    );
    if (!confirmed) return;
    await db.delete();
    await db.open();
    await resetPreferences();
    navigate('/', { replace: true });
  }

  function pickColor(ref: { current: HTMLInputElement | null }): void {
    ref.current?.click();
  }

  return (
    <div style={STAGE_STYLE}>
      <div style={{ height: STATUS_BAR_HEIGHT, flexShrink: 0 }} />

      <div style={HEADER_STYLE}>
        <button type="button" aria-label="Back" style={BACK_BTN_STYLE} onClick={() => navigate(-1)}>
          <svg width="9" height="15" viewBox="0 0 9 15" fill="none"
            stroke="var(--ink-2)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
            aria-hidden>
            <path d="M7.5 1.5L1.5 7.5l6 6" />
          </svg>
        </button>
        <div style={TITLE_STYLE}>Settings</div>
      </div>

      <div style={SCROLL_STYLE}>
        {/* READING */}
        <div>
          <Eyebrow>READING</Eyebrow>

          <div style={SLIDER_ROW_STYLE}>
            <div style={SLIDER_HEADER_STYLE}>
              <div style={SLIDER_LABEL_STYLE}>Default speed</div>
              <div style={SLIDER_VALUE_STYLE}>{`${prefs.wpm} WPM`}</div>
            </div>
            <div style={{ marginTop: 10 }}>
              <Slider value={prefs.wpm} min={WPM_MIN} max={WPM_MAX} step={WPM_STEP}
                onChange={(v) => { void setPreference('wpm', v); }} />
            </div>
          </div>

          <div style={SLIDER_ROW_STYLE}>
            <div style={SLIDER_HEADER_STYLE}>
              <div style={SLIDER_LABEL_STYLE}>Default font size</div>
              <div style={SLIDER_VALUE_STYLE}>{`${prefs.fontSize} PX`}</div>
            </div>
            <div style={{ marginTop: 10 }}>
              <Slider value={prefs.fontSize} min={FONT_SIZE_MIN} max={FONT_SIZE_MAX} step={FONT_SIZE_STEP}
                onChange={(v) => { void setPreference('fontSize', v); }} />
            </div>
          </div>

          <SettingRow label="Default font" last onClick={() => setFontPickerOpen(true)}
            right={
              <div style={FONT_RIGHT_STYLE}>
                <span style={{ fontFamily: prefs.fontFamily, fontSize: 14, color: 'var(--ink)' }}>
                  {prefs.fontFamily}
                </span>
                <Chevron />
              </div>
            } />
        </div>

        {/* APPEARANCE */}
        <div style={SECTION_STYLE}>
          <Eyebrow>APPEARANCE</Eyebrow>

          <div style={{ ...PREVIEW_TILE_BASE_STYLE, background: prefs.backgroundColor }}>
            <div style={PREVIEW_EYEBROW_STYLE}>PREVIEW</div>
            <ReaderWord
              word="preview"
              size={28}
              color={prefs.textColor}
              pinColor={prefs.highlightPin ? prefs.pinColor : prefs.textColor}
              fontFamily={prefs.fontFamily}
            />
          </div>

          <SettingRow label="Background" onClick={() => pickColor(bgColorRef)}
            right={renderSwatch(prefs.backgroundColor)} />
          <SettingRow label="Text" onClick={() => pickColor(textColorRef)}
            right={renderSwatch(prefs.textColor)} />
          <SettingRow label="Pin" last onClick={() => pickColor(pinColorRef)}
            right={renderSwatch(prefs.pinColor)} />

          <input ref={bgColorRef} type="color" value={prefs.backgroundColor}
            onChange={(e) => { void setPreference('backgroundColor', e.target.value); }}
            style={HIDDEN_COLOR_INPUT_STYLE} aria-label="Background color" />
          <input ref={textColorRef} type="color" value={prefs.textColor}
            onChange={(e) => { void setPreference('textColor', e.target.value); }}
            style={HIDDEN_COLOR_INPUT_STYLE} aria-label="Text color" />
          <input ref={pinColorRef} type="color" value={prefs.pinColor}
            onChange={(e) => { void setPreference('pinColor', e.target.value); }}
            style={HIDDEN_COLOR_INPUT_STYLE} aria-label="Pin color" />
        </div>

        {/* BEHAVIOR */}
        <div style={SECTION_STYLE}>
          <Eyebrow>BEHAVIOR</Eyebrow>
          <SettingRow label="Highlight pin"
            right={<Toggle on={prefs.highlightPin} label="Highlight pin"
              onChange={(v) => { void setPreference('highlightPin', v); }} />} />
          <SettingRow label="Show center guide lines"
            right={<Toggle on={prefs.showGuideLines} label="Show center guide lines"
              onChange={(v) => { void setPreference('showGuideLines', v); }} />} />
          <SettingRow label="Punctuation pauses"
            right={<Toggle on={prefs.punctuationPauses} label="Punctuation pauses"
              onChange={(v) => { void setPreference('punctuationPauses', v); }} />} />
          <SettingRow label="Haptics" last
            right={<Toggle on={prefs.haptics} label="Haptics"
              onChange={(v) => { void setPreference('haptics', v); }} />} />
        </div>

        {/* DATA */}
        <div style={SECTION_STYLE}>
          <Eyebrow>DATA</Eyebrow>
          <SettingRow label="Export library" onClick={() => { void handleExport(); }}
            right={<Chevron />} />
          <SettingRow label={<span style={{ color: 'var(--accent)' }}>Clear all data</span>}
            last onClick={() => { void handleClearAll(); }} />
        </div>

        {/* ABOUT */}
        <div style={SECTION_STYLE}>
          <Eyebrow>ABOUT</Eyebrow>
          <SettingRow label="Version" last
            right={<div style={VERSION_STYLE}>{APP_VERSION}</div>} />
        </div>
      </div>

      {isFontPickerOpen && (
        <FontPicker current={prefs.fontFamily}
          onPick={(font) => {
            void setPreference('fontFamily', font);
            setFontPickerOpen(false);
          }}
          onClose={() => setFontPickerOpen(false)} />
      )}
    </div>
  );
}
