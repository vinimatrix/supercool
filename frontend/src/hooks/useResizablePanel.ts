import { useCallback, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent } from 'react';
import { flushSync } from 'react-dom';

export interface ResizablePanelDividerProps {
  onPointerDown: (e: ReactPointerEvent) => void;
  onPointerMove: (e: ReactPointerEvent) => void;
  onPointerUp: () => void;
  onPointerCancel: () => void;
}

export function useResizablePanel(
  key: string,
  defaultWidth: number,
  min: number,
  max: number,
  sign: 1 | -1
): { width: number; dividerProps: ResizablePanelDividerProps } {
  const storageKey = `panel-width:${key}`;
  const [width, setWidth] = useState<number>(() => {
    if (typeof window === 'undefined') return defaultWidth;
    const raw = window.localStorage.getItem(storageKey);
    const n = raw ? Number(raw) : NaN;
    if (Number.isFinite(n)) return Math.min(max, Math.max(min, n));
    return defaultWidth;
  });

  const widthRef = useRef(width);
  const startRef = useRef({ x: 0, w: defaultWidth });
  const draggingRef = useRef(false);

  const onPointerDown = useCallback(
    (e: ReactPointerEvent) => {
      draggingRef.current = true;
      startRef.current = { x: e.clientX, w: widthRef.current };
      e.currentTarget?.setPointerCapture?.(e.pointerId ?? 1);
    },
    []
  );

  const onPointerMove = useCallback(
    (e: ReactPointerEvent) => {
      if (!draggingRef.current) return;
      const delta = e.clientX - startRef.current.x;
      const next = Math.min(max, Math.max(min, startRef.current.w + sign * delta));
      widthRef.current = next;
      flushSync(() => setWidth(next));
    },
    [min, max, sign]
  );

  const endDrag = useCallback(() => {
    draggingRef.current = false;
    window.localStorage.setItem(storageKey, String(widthRef.current));
  }, [storageKey]);

  const dividerProps: ResizablePanelDividerProps = {
    onPointerDown,
    onPointerMove,
    onPointerUp: endDrag,
    onPointerCancel: endDrag,
  };

  return { width, dividerProps };
}
