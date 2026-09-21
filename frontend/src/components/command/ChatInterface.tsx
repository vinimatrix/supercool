import React, { useState } from 'react';
import { Send, Sparkles, Zap } from 'lucide-react';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { useStudioContext } from '../../context/StudioContext';

interface ChatInterfaceProps {
  messages: { role: string; text: string }[];
  onSend: (text: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, onSend }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-30">
            <div className="p-4 rounded-full bg-[var(--color-border)]">
              <Sparkles className="w-8 h-8 text-gray-500" />
            </div>
            <div>
              <p className="text-xs mono text-gray-500">WAITING FOR INPUT</p>
              <p className="text-[10px] mono text-gray-600 mt-1">Enter director prompts to shape the scene</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`text-xs p-3 rounded-sm border ${
            msg.role === 'user'
              ? 'bg-black/20 border-l-2 border-l-[var(--color-accent)] ml-4'
              : 'bg-black/40 border-[var(--color-border)] mr-4 text-gray-400 mono'
          }`}>
            <div className="flex items-center gap-2 mb-1 opacity-50">
              <span className="text-[9px] mono font-bold uppercase">
                {msg.role === 'user' ? 'Director' : 'System'}
              </span>
            </div>
            {msg.text}
          </div>
        ))}
      </div>

      <div className="p-4 border-t" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center gap-2 bg-black/40 p-2 rounded border border-[var(--color-border)] focus-within:border-[var(--color-accent)] transition-all">
          <span className="text-[10px] mono text-[var(--color-accent)] font-bold">{'>'}</span>
          <Input
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Execute command..."
            className="flex-1 bg-transparent border-none focus:ring-0"
            onKeyDown={e => e.key === 'Enter' && handleSend()}
          />
          <Button onClick={handleSend} className="p-1" icon={<Send className="w-3 h-3" />}>
            {/* Icon only */}
          </Button>
        </div>
      </div>
    </div>
  );
};