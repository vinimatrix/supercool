import React from 'react';

interface ToastProps {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

export const Toast: React.FC<ToastProps> = ({ message, type }) => {
  const styles = {
    success: 'bg-emerald-900/80 border-emerald-500 text-emerald-200',
    error: 'bg-red-900/80 border-red-500 text-red-200',
    info: 'bg-blue-900/80 border-blue-500 text-blue-200',
  };

  return (
    <div className={`px-4 py-2 rounded-sm text-xs font-bold mono shadow-xl border animate-in slide-in-from-right-full ${styles[type]}`}>
      {message}
    </div>
  );
};