import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useResizablePanel } from '../hooks/useResizablePanel';

describe('useResizablePanel', () => {
  beforeEach(() => localStorage.clear());

  it('uses default when no stored value', () => {
    const { result } = renderHook(() => useResizablePanel('sidebar', 320, 220, 560, 1));
    expect(result.current.width).toBe(320);
  });

  it('reads stored value and clamps on init', () => {
    localStorage.setItem('panel-width:sidebar', '9999');
    const { result } = renderHook(() => useResizablePanel('sidebar', 320, 220, 560, 1));
    expect(result.current.width).toBe(560);
  });

  it('applies sign and clamps during drag, persists on pointerup', () => {
    const { result } = renderHook(() => useResizablePanel('sidebar', 320, 220, 560, 1));
    const handlers = result.current.dividerProps;
    (handlers as any).onPointerDown({ clientX: 0, currentTarget: { setPointerCapture: () => {} } });
    (handlers as any).onPointerMove({ clientX: 50 });
    expect(result.current.width).toBe(370);
    (handlers as any).onPointerMove({ clientX: 10000 });
    expect(result.current.width).toBe(560);
    (handlers as any).onPointerUp({});
    expect(localStorage.getItem('panel-width:sidebar')).toBe('560');
  });

  it('sign -1 shrinks on positive delta and clamps at min', () => {
    const { result } = renderHook(() => useResizablePanel('command', 384, 300, 640, -1));
    const handlers = result.current.dividerProps;
    (handlers as any).onPointerDown({ clientX: 0, currentTarget: { setPointerCapture: () => {} } });
    (handlers as any).onPointerMove({ clientX: 20 });
    // 384 - 20 = 364
    expect(result.current.width).toBe(364);
    (handlers as any).onPointerMove({ clientX: 10000 });
    // 384 - 10000 clamped to min 300
    expect(result.current.width).toBe(300);
  });
});
