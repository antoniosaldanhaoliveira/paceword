import {
  useRef,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from 'react';

/**
 * Hand-rolled pointer-events wrapper that classifies user input into
 * tap / swipe-left / swipe-right / swipe-up / swipe-down. Sized and
 * styled by the parent; `touch-action: none` so mobile browsers don't
 * eat the gestures for pull-to-refresh or back-navigation.
 *
 * Swipe-up is zone-gated to the bottom 30% of the stage (settings drawer).
 * Swipe-down is zone-gated to the top 30% of the stage (dismiss reader).
 *
 * See `.gsd/milestones/M001/slices/S02/tasks/T04-PLAN.md`.
 */

const TAP_MAX_MS = 250;
const TAP_MAX_MOVEMENT_PX = 10;
const SWIPE_MIN_DISTANCE_PX = 40;
const SWIPE_MAX_ORTHOGONAL_PX = 40;
const SWIPE_MAX_MS = 500;
const BOTTOM_SWIPE_ZONE_RATIO = 0.7;
const TOP_SWIPE_ZONE_RATIO = 0.3;

export interface GestureLayerProps {
  children: ReactNode;
  onTap?: () => void;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  className?: string;
  style?: CSSProperties;
}

interface PointerStart {
  x: number;
  y: number;
  t: number;
  heightAtStart: number;
}

export default function GestureLayer({
  children,
  onTap,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  className,
  style,
}: GestureLayerProps) {
  const startRef = useRef<PointerStart | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  function handlePointerDown(e: ReactPointerEvent<HTMLDivElement>) {
    const rect = wrapperRef.current?.getBoundingClientRect();
    startRef.current = {
      x: e.clientX,
      y: e.clientY,
      t: performance.now(),
      heightAtStart: rect?.height ?? window.innerHeight,
    };
  }

  function handlePointerUp(e: ReactPointerEvent<HTMLDivElement>) {
    const start = startRef.current;
    startRef.current = null;
    if (!start) return;

    const dx = e.clientX - start.x;
    const dy = e.clientY - start.y;
    const dt = performance.now() - start.t;
    const absX = Math.abs(dx);
    const absY = Math.abs(dy);

    if (dt < TAP_MAX_MS && absX < TAP_MAX_MOVEMENT_PX && absY < TAP_MAX_MOVEMENT_PX) {
      onTap?.();
      return;
    }

    if (dt > SWIPE_MAX_MS) return;

    if (absX >= SWIPE_MIN_DISTANCE_PX && absY < SWIPE_MAX_ORTHOGONAL_PX) {
      if (dx < 0) onSwipeLeft?.();
      else onSwipeRight?.();
      return;
    }

    if (absY >= SWIPE_MIN_DISTANCE_PX && absX < SWIPE_MAX_ORTHOGONAL_PX) {
      if (dy < 0) {
        const startedInBottom = start.y > start.heightAtStart * BOTTOM_SWIPE_ZONE_RATIO;
        if (startedInBottom) onSwipeUp?.();
      } else {
        const startedInTop = start.y < start.heightAtStart * TOP_SWIPE_ZONE_RATIO;
        if (startedInTop) onSwipeDown?.();
      }
    }
  }

  function handlePointerCancel() {
    startRef.current = null;
  }

  const mergedStyle: CSSProperties = { touchAction: 'none', ...style };

  return (
    <div
      ref={wrapperRef}
      className={className}
      style={mergedStyle}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerCancel}
    >
      {children}
    </div>
  );
}
