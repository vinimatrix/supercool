import React from 'react';

export const PanelDivider: React.FC<React.HTMLAttributes<HTMLDivElement>> = (props) => (
  <div
    role="separator"
    aria-orientation="vertical"
    data-testid="panel-divider"
    className="w-1 shrink-0 cursor-col-resize hover:bg-[var(--color-accent)] transition-colors"
    style={{ backgroundColor: 'var(--color-border)' }}
    {...props}
  />
);
