'use client';

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Loader2, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface DeviceChatProps {
  profileId: string;
}

interface ChatResponse {
  success: boolean;
  response: string;
  steps_taken: number;
  error?: string;
}

export function DeviceChat({ profileId }: DeviceChatProps) {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{
    type: 'user' | 'assistant' | 'error';
    message: string;
    timestamp: Date;
  }>>([]);

  const sendMessage = useMutation({
    mutationFn: async (message: string) => {
      const response = await api.request(`/chat/profiles/${profileId}`, {
        method: 'POST',
        body: JSON.stringify({ message }),
      });
      return response as ChatResponse;
    },
    onSuccess: (data) => {
      setChatHistory(prev => [
        ...prev,
        {
          type: data.success ? 'assistant' : 'error',
          message: data.response,
          timestamp: new Date(),
        },
      ]);
    },
    onError: (error) => {
      setChatHistory(prev => [
        ...prev,
        {
          type: 'error',
          message: error instanceof Error ? error.message : 'Failed to send message',
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || sendMessage.isPending) return;

    // Add user message to history
    setChatHistory(prev => [
      ...prev,
      {
        type: 'user',
        message: message.trim(),
        timestamp: new Date(),
      },
    ]);

    // Send message
    sendMessage.mutate(message.trim());
    setMessage('');
  };

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
      <div className="p-4 border-b border-gray-800">
        <h3 className="text-lg font-semibold">AI Device Control</h3>
        <p className="text-sm text-gray-400 mt-1">
          Use natural language to control the device
        </p>
      </div>

      {/* Chat History */}
      <div className="h-64 overflow-y-auto p-4 space-y-3">
        {chatHistory.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <p className="text-sm">Try commands like:</p>
            <ul className="text-xs mt-2 space-y-1">
              <li>"Open the settings app"</li>
              <li>"What\'s on the screen?"</li>
              <li>"Click on the Search button"</li>
            </ul>
          </div>
        ) : (
          chatHistory.map((item, idx) => (
            <div
              key={idx}
              className={`flex ${
                item.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 ${
                  item.type === 'user'
                    ? 'bg-primary-600 text-white'
                    : item.type === 'error'
                    ? 'bg-red-900/20 text-red-400 border border-red-800'
                    : 'bg-gray-800 text-gray-200'
                }`}
              >
                {item.type === 'error' && (
                  <AlertCircle className="h-4 w-4 inline-block mr-1" />
                )}
                <p className="text-sm whitespace-pre-wrap">{item.message}</p>
                <p className="text-xs opacity-60 mt-1">
                  {item.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
        {sendMessage.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-lg p-3">
              <Loader2 className="h-4 w-4 animate-spin" />
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a command..."
            className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={sendMessage.isPending}
          />
          <button
            type="submit"
            disabled={!message.trim() || sendMessage.isPending}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {sendMessage.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}