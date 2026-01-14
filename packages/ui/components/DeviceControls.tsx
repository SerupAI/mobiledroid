'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Home, ArrowLeft, RotateCcw, Clipboard, Send, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface DeviceControlsProps {
  profileId: string;
}

export function DeviceControls({ profileId }: DeviceControlsProps) {
  const [pasteText, setPasteText] = useState('');
  const [showPasteInput, setShowPasteInput] = useState(false);

  const backMutation = useMutation({
    mutationFn: () => api.pressBack(profileId),
  });

  const homeMutation = useMutation({
    mutationFn: () => api.pressHome(profileId),
  });

  const pasteMutation = useMutation({
    mutationFn: (text: string) => api.pasteText(profileId, text),
    onSuccess: () => {
      setPasteText('');
      setShowPasteInput(false);
    },
  });

  const handlePaste = () => {
    if (pasteText.trim()) {
      pasteMutation.mutate(pasteText);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handlePaste();
    }
    if (e.key === 'Escape') {
      setShowPasteInput(false);
      setPasteText('');
    }
  };

  const buttonClass = cn(
    'flex items-center justify-center rounded-lg bg-gray-800 p-3',
    'hover:bg-gray-700 transition-colors disabled:opacity-50'
  );

  return (
    <div className="space-y-3">
      {/* Navigation buttons */}
      <div className="flex items-center justify-center gap-4">
        <button
          onClick={() => backMutation.mutate()}
          disabled={backMutation.isPending}
          className={buttonClass}
          title="Back"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>

        <button
          onClick={() => homeMutation.mutate()}
          disabled={homeMutation.isPending}
          className={buttonClass}
          title="Home"
        >
          <Home className="h-5 w-5" />
        </button>

        <button className={buttonClass} title="Recent Apps">
          <RotateCcw className="h-5 w-5" />
        </button>

        <button
          onClick={() => setShowPasteInput(!showPasteInput)}
          className={cn(buttonClass, showPasteInput && 'bg-primary-600 hover:bg-primary-700')}
          title="Paste Text"
        >
          <Clipboard className="h-5 w-5" />
        </button>
      </div>

      {/* Paste text input */}
      {showPasteInput && (
        <div className="flex gap-2">
          <input
            type="text"
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type or paste text to send to device..."
            className="flex-1 rounded-lg border border-gray-600 bg-gray-800 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
            autoFocus
          />
          <button
            onClick={handlePaste}
            disabled={!pasteText.trim() || pasteMutation.isPending}
            className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm text-white hover:bg-primary-700 disabled:opacity-50"
          >
            {pasteMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            Send
          </button>
        </div>
      )}
    </div>
  );
}
