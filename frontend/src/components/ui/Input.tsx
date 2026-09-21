import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input: React.FC<InputProps> = ({ className = '', error, ...props }) => {
  return (
    <input
      className={`bg-black/40 text-xs px-2 py-1 rounded border mono text-white focus:outline-none focus:border-[var(--color-accent)] transition-all ${
        error ? 'border-red-500' : 'border-[var(--color-border)]'
      } ${className}`}
      {...props}
    />
  );
};