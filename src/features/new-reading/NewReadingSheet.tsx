/**
 * Pace PWA — New reading sheet
 *
 * Modal bottom-sheet rendered at `/new`, offering three input sources:
 * Paste text (wired to `/new/paste`), Upload PDF (placeholder log until
 * S04), and From a URL (disabled, SOON chip). Tapping the dim backdrop
 * dismisses the sheet via `navigate(-1)`; taps inside the sheet are
 * contained with `stopPropagation`.
 *
 * See: .gsd/milestones/M001/slices/S03/S03-PLAN.md §6.3
 */
import type { CSSProperties, MouseEvent, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

interface OptionRow {
  key: string;
  icon: ReactNode;
  title: string;
  desc: string;
  iconColor: string;
  disabled: boolean;
  badge?: string;
  onClick?: () => void;
}

const svgProps = {
  width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none',
  stroke: 'currentColor', strokeWidth: 1.8,
  strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
};

const pencilIcon = (
  <svg {...svgProps}>
    <path d="M12 20h9" />
    <path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
  </svg>
);

const docIcon = (
  <svg {...svgProps}>
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
);

const globeIcon = (
  <svg {...svgProps}>
    <circle cx="12" cy="12" r="10" />
    <path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10A15.3 15.3 0 018 12a15.3 15.3 0 014-10z" />
  </svg>
);

const chevron = (
  <svg width="10" height="14" viewBox="0 0 10 14" fill="none" stroke="var(--ink-3)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 1l6 6-6 6" />
  </svg>
);

const backdropStyle: CSSProperties = {
  position: 'fixed', inset: 0, background: 'rgba(3,3,3,0.55)',
  backdropFilter: 'blur(8px)', WebkitBackdropFilter: 'blur(8px)',
  display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', zIndex: 50,
};

const sheetStyle: CSSProperties = {
  background: 'var(--surface-2)',
  borderTopLeftRadius: 'var(--r-xl)', borderTopRightRadius: 'var(--r-xl)',
  borderTop: '1px solid var(--line-2)', borderLeft: '1px solid var(--line-2)',
  borderRight: '1px solid var(--line-2)', paddingBottom: 30, margin: '0 6px',
};

const handleStyle: CSSProperties = {
  width: 36, height: 3, background: 'var(--ink-3)', opacity: 0.5,
  borderRadius: 2, margin: '10px auto 18px',
};

const iconTileStyle = (color: string): CSSProperties => ({
  width: 36, height: 36, borderRadius: 'var(--r-sm)',
  background: 'var(--surface)', border: '1px solid var(--line-2)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  color, flexShrink: 0,
});

const badgeStyle: CSSProperties = {
  fontFamily: 'var(--font-ui)', fontSize: 8.5, fontWeight: 500,
  letterSpacing: '0.2em', color: 'var(--ink-3)',
  border: '1px solid var(--line-2)', padding: '3px 6px', borderRadius: 4,
};

function NewReadingSheet() {
  const navigate = useNavigate();

  const rows: OptionRow[] = [
    {
      key: 'paste', icon: pencilIcon, title: 'Paste text',
      desc: 'Drop in anything from the clipboard',
      iconColor: 'var(--accent)', disabled: false,
      onClick: () => navigate('/new/paste'),
    },
    {
      key: 'pdf', icon: docIcon, title: 'Upload PDF',
      desc: 'Text-based PDFs only for now',
      iconColor: 'var(--ink-2)', disabled: false,
      onClick: () => navigate('/new/pdf'),
    },
    {
      key: 'url', icon: globeIcon, title: 'From a URL',
      desc: 'Extracts article text from any link',
      iconColor: 'var(--ink-2)', disabled: false,
      onClick: () => navigate('/new/url'),
    },
  ];

  const stopBubble = (event: MouseEvent<HTMLDivElement>) => event.stopPropagation();
  const dismiss = () => navigate(-1);

  return (
    <div style={backdropStyle} onClick={dismiss} role="presentation">
      <div style={sheetStyle} onClick={stopBubble} role="dialog" aria-modal="true" aria-label="New reading">
        <div style={handleStyle} aria-hidden="true" />
        <div style={{ padding: '0 22px 6px' }}>
          <div style={{ fontFamily: 'var(--font-display)', fontSize: 19, fontWeight: 400, color: 'var(--ink)', letterSpacing: '-0.02em' }}>
            New reading
          </div>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 400, color: 'var(--ink-2)', marginTop: 3 }}>
            Choose a source.
          </div>
        </div>
        <div style={{ marginTop: 20, padding: '0 22px' }}>
          {rows.map((row, index) => {
            const isLast = index === rows.length - 1;
            const handleRowClick = () => {
              if (row.disabled) return;
              row.onClick?.();
            };
            return (
              <div
                key={row.key}
                onClick={handleRowClick}
                role={row.disabled ? undefined : 'button'}
                tabIndex={row.disabled ? -1 : 0}
                aria-disabled={row.disabled}
                style={{
                  display: 'flex', alignItems: 'center', gap: 14, padding: '14px 0',
                  borderBottom: isLast ? 'none' : '1px solid var(--line)',
                  opacity: row.disabled ? 0.55 : 1,
                  cursor: row.disabled ? 'default' : 'pointer',
                }}
              >
                <div style={iconTileStyle(row.iconColor)}>{row.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: 'var(--font-ui)', fontSize: 13, fontWeight: 500, color: 'var(--ink)' }}>
                    {row.title}
                  </div>
                  <div style={{ fontFamily: 'var(--font-ui)', fontSize: 10.5, fontWeight: 400, color: 'var(--ink-2)', marginTop: 2 }}>
                    {row.desc}
                  </div>
                </div>
                {row.badge ? <div style={badgeStyle}>{row.badge}</div> : chevron}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default NewReadingSheet;
