'use client';

import { useState } from 'react';
import { Send, Loader2, AlertCircle, Square, RefreshCw, Repeat, Edit3 } from 'lucide-react';

interface DeviceChatProps {
  profileId: string;
}

interface ChatMessage {
  type: 'user' | 'assistant' | 'error' | 'thinking' | 'step' | 'cancelled';
  message: string;
  timestamp: Date;
  details?: string;
  stepNumber?: number;
  screenshot?: string;  // Base64 screenshot
}

export function DeviceChat({ profileId }: DeviceChatProps) {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<ChatMessage>>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [editingMessage, setEditingMessage] = useState<string | null>(null);
  const [lastUserMessage, setLastUserMessage] = useState<string>('');
  const [chatHeight, setChatHeight] = useState(256); // 16rem = 256px
  const [maxSteps, setMaxSteps] = useState(20);
  const [wasStoppedByUser, setWasStoppedByUser] = useState(false);

  const stopChat = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/profiles/${profileId}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error('Failed to stop chat');
      }
      
      // Stop will be handled by the streaming response
      setWasStoppedByUser(true);
      setIsStreaming(false);
    } catch (error) {
      console.error('Failed to stop chat:', error);
      setWasStoppedByUser(true);
      setIsStreaming(false);
    }
  };

  const refreshChat = () => {
    setChatHistory([]);
    setMessage('');
    setEditingMessage(null);
    setLastUserMessage('');
    setWasStoppedByUser(false);
  };

  const repeatLastMessage = async () => {
    if (lastUserMessage && !isStreaming) {
      setWasStoppedByUser(false);
      await sendMessageWithStream(lastUserMessage);
    }
  };

  const editLastMessage = () => {
    if (lastUserMessage && !isStreaming) {
      setMessage(lastUserMessage);
      setEditingMessage(lastUserMessage);
      setWasStoppedByUser(false);
    }
  };

  const sendMessageWithStream = async (message: string) => {
    setIsStreaming(true);
    
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/profiles/${profileId}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message, max_steps: maxSteps }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');
      
      const decoder = new TextDecoder();
      let buffer = '';
      
      // Add thinking message
      setChatHistory(prev => [...prev, {
        type: 'thinking',
        message: 'Analyzing the screen...',
        timestamp: new Date(),
      }]);
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            
            try {
              const event = JSON.parse(data);
              
              if (event.type === 'step') {
                setChatHistory(prev => {
                  // Remove thinking message if this is the first step
                  const filtered = event.number === 1 
                    ? prev.filter(m => m.type !== 'thinking')
                    : prev;
                  
                  return [...filtered, {
                    type: 'step',
                    message: `Step ${event.number}: ${event.action} - ${event.reasoning}`,
                    details: event.details,
                    stepNumber: event.number,
                    screenshot: event.screenshot,
                    timestamp: new Date(),
                  }];
                });
              } else if (event.type === 'heartbeat') {
                // Ignore heartbeats, just keep connection alive
                continue;
              } else if (event.type === 'cancelled') {
                setChatHistory(prev => {
                  // Remove any thinking messages
                  const filtered = prev.filter(m => m.type !== 'thinking');
                  return [...filtered, {
                    type: 'cancelled',
                    message: event.message || 'Chat session was stopped',
                    timestamp: new Date(),
                  }];
                });
                break; // Exit the loop when cancelled
              } else if (event.type === 'complete') {
                setChatHistory(prev => {
                  // Remove any thinking messages
                  const filtered = prev.filter(m => m.type !== 'thinking');
                  return [...filtered, {
                    type: event.success ? 'assistant' : 'error',
                    message: event.message,
                    timestamp: new Date(),
                  }];
                });
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e);
            }
          }
        }
      }
    } catch (error) {
      setChatHistory(prev => [
        ...prev.filter(m => m.type !== 'thinking'),
        {
          type: 'error',
          message: error instanceof Error ? error.message : 'Failed to send message',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsStreaming(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isStreaming) return;

    // Add user message to history
    const userMessage = message.trim();
    setChatHistory(prev => [
      ...prev,
      {
        type: 'user',
        message: userMessage,
        timestamp: new Date(),
      },
    ]);

    // Track last user message and clear edit state
    setLastUserMessage(userMessage);
    setEditingMessage(null);

    // Clear input and send message with streaming
    setMessage('');
    await sendMessageWithStream(userMessage);
  };

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-900 overflow-hidden">
      <div className="p-4 border-b border-gray-800 flex justify-between items-start">
        <div>
          <h3 className="text-lg font-semibold">AI Device Control</h3>
          <p className="text-sm text-gray-400 mt-1">
            Use natural language to control the device
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={refreshChat}
            disabled={isStreaming}
            className="p-1 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            title="Clear chat history"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
          <button
            onClick={repeatLastMessage}
            disabled={!lastUserMessage || isStreaming}
            className="p-1 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
            title="Repeat last message"
          >
            <Repeat className="h-4 w-4" />
          </button>
          <button
            onClick={editLastMessage}
            disabled={!lastUserMessage || (isStreaming && !wasStoppedByUser)}
            className={`p-1 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed ${
              wasStoppedByUser ? 'text-orange-400 hover:text-orange-300' : ''
            }`}
            title={wasStoppedByUser ? "Edit stopped message" : "Edit last message"}
          >
            <Edit3 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Debug Controls */}
      {process.env.NEXT_PUBLIC_DEBUG === 'true' && (
        <div className="px-4 py-2 border-b border-gray-800 bg-gray-950">
          <div className="flex items-center gap-4 text-sm">
            <label className="flex items-center gap-2 text-gray-400">
              Max Steps:
              <input
                type="number"
                min="1"
                max="100"
                value={maxSteps}
                onChange={(e) => setMaxSteps(parseInt(e.target.value) || 20)}
                className="w-16 px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white"
                disabled={isStreaming}
              />
            </label>
            <label className="flex items-center gap-2 text-gray-400">
              Chat Height:
              <input
                type="range"
                min="200"
                max="600"
                value={chatHeight}
                onChange={(e) => setChatHeight(parseInt(e.target.value))}
                className="w-20"
                disabled={isStreaming}
              />
              <span className="text-xs">{chatHeight}px</span>
            </label>
          </div>
        </div>
      )}

      {/* Chat History */}
      <div 
        className="overflow-y-auto p-4 space-y-3"
        style={{ height: `${chatHeight}px` }}
      >
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
                    : item.type === 'cancelled'
                    ? 'bg-orange-900/20 text-orange-400 border border-orange-800'
                    : 'bg-gray-800 text-gray-200'
                }`}
              >
                {item.type === 'error' && (
                  <AlertCircle className="h-4 w-4 inline-block mr-1" />
                )}
                <p className="text-sm whitespace-pre-wrap">{item.message}</p>
                {item.details && (
                  <p className="text-xs opacity-75 mt-1">{item.details}</p>
                )}
                {item.screenshot && (
                  <div className="mt-2">
                    <img 
                      src={`data:image/png;base64,${item.screenshot}`}
                      alt="Screenshot"
                      className="max-w-full h-auto rounded border border-gray-600"
                      style={{ maxHeight: '200px' }}
                    />
                  </div>
                )}
                <p className="text-xs opacity-60 mt-1">
                  {item.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
        {isStreaming && chatHistory[chatHistory.length - 1]?.type !== 'thinking' && (
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
            placeholder={editingMessage ? "Editing last message..." : "Type a command..."}
            className={`flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              editingMessage ? 'border-orange-500' : ''
            }`}
            disabled={isStreaming}
          />
          {isStreaming && (
            <button
              type="button"
              onClick={stopChat}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
              title="Stop chat"
            >
              <Square className="h-4 w-4" />
            </button>
          )}
          <button
            type="submit"
            disabled={!message.trim() || isStreaming}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isStreaming ? (
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