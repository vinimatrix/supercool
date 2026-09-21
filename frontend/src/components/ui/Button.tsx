import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  loading,
  icon,
  className = '',
  ...props
}) => {
  const variants = {
    primary: 'bg-[var(--color-accent)] text-black hover:opacity-90',
    secondary: 'bg-black/40 border border-[var(--color-border)] text-gray-400 hover:text-white hover:border-[var(--color-accent)]',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  };

  return (
    <button
      className={`px-2 py-1 rounded text-xs font-bold transition-all flex items-center justify-center gap-1 disabled:opacity-30 ${variants[variant]} ${className}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <span className="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin" />
      ) : (
        <>
          {icon}
          {children}
        </>
      )}
    </button>
  );
};