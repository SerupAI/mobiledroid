'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, AlertCircle, Square, RefreshCw, Repeat, Edit3, History, X, ChevronRight, DollarSign } from 'lucide-react';
import { api, ChatSession, ChatMessage as ApiChatMessage } from '@/lib/api';

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
  tokens?: number;  // Token count (cumulative for steps, total for complete)
}

interface ChatSessionSummary {
  id: string;
  profile_id: string;
  initial_prompt: string;
  status: string;
  total_tokens: number;
  total_steps: number;
  created_at: string;
  completed_at: string | null;
  message_count: number;
}

interface ChatHistoryResponse {
  sessions: ChatSessionSummary[];
  total_tokens: number;
  total_sessions: number;
}

// Claude Sonnet pricing (per 1K tokens)
const COST_PER_1K_INPUT = 0.003;
const COST_PER_1K_OUTPUT = 0.015;

function calculateCost(tokens: number): number {
  // Approximate 50/50 split between input and output
  const inputTokens = tokens / 2;
  const outputTokens = tokens / 2;
  return (inputTokens / 1000 * COST_PER_1K_INPUT) + (outputTokens / 1000 * COST_PER_1K_OUTPUT);
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
  const [showHistory, setShowHistory] = useState(false);
  const [historyData, setHistoryData] = useState<ChatHistoryResponse | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const hasLoadedInitialSession = useRef(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatEndRef.current && chatHistory.length > 0) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory]);

  // Load most recent session on mount
  useEffect(() => {
    if (hasLoadedInitialSession.current) return;
    hasLoadedInitialSession.current = true;

    const loadRecentSession = async () => {
      try {
        const history = await api.getChatHistory(profileId);
        setHistoryData(history);

        if (history.sessions.length > 0) {
          const mostRecentSession = history.sessions[0];
          const sessionAge = Date.now() - new Date(mostRecentSession.created_at).getTime();
          const oneHour = 60 * 60 * 1000;

          // Load if session is recent (within 1 hour) or still running
          if (sessionAge < oneHour || mostRecentSession.status === 'running') {
            const fullSession = await api.getChatSession(mostRecentSession.id);
            setCurrentSessionId(fullSession.id);

            // Convert API messages to chat history format
            const loadedMessages: ChatMessage[] = fullSession.messages.map((msg) => {
              if (msg.role === 'user') {
                return {
                  type: 'user' as const,
                  message: msg.content,
                  timestamp: new Date(msg.created_at),
                };
              } else if (msg.role === 'step') {
                return {
                  type: 'step' as const,
                  message: `Step ${msg.step_number}: ${msg.action_type || 'action'} - ${msg.action_reasoning || msg.content}`,
                  timestamp: new Date(msg.created_at),
                  tokens: msg.cumulative_tokens || undefined,
                };
              } else {
                // assistant or completion message
                return {
                  type: fullSession.status === 'error' ? 'error' as const : 'assistant' as const,
                  message: msg.content,
                  timestamp: new Date(msg.created_at),
                  tokens: msg.cumulative_tokens || undefined,
                };
              }
            });

            setChatHistory(loadedMessages);

            // Set last user message for repeat/edit functionality
            const lastUserMsg = fullSession.messages.filter(m => m.role === 'user').pop();
            if (lastUserMsg) {
              setLastUserMessage(lastUserMsg.content);
            }
          }
        }
      } catch (error) {
        console.error('Failed to load recent session:', error);
      } finally {
        setIsLoadingSession(false);
      }
    };

    loadRecentSession();
  }, [profileId]);

  // Load a specific session by ID
  const loadSession = async (sessionId: string) => {
    try {
      setIsLoadingSession(true);
      const fullSession = await api.getChatSession(sessionId);
      setCurrentSessionId(fullSession.id);

      // Convert API messages to chat history format
      const loadedMessages: ChatMessage[] = fullSession.messages.map((msg) => {
        if (msg.role === 'user') {
          return {
            type: 'user' as const,
            message: msg.content,
            timestamp: new Date(msg.created_at),
          };
        } else if (msg.role === 'step') {
          return {
            type: 'step' as const,
            message: `Step ${msg.step_number}: ${msg.action_type || 'action'} - ${msg.action_reasoning || msg.content}`,
            timestamp: new Date(msg.created_at),
            tokens: msg.cumulative_tokens || undefined,
          };
        } else {
          // assistant or completion message
          return {
            type: fullSession.status === 'error' ? 'error' as const : 'assistant' as const,
            message: msg.content,
            timestamp: new Date(msg.created_at),
            tokens: msg.cumulative_tokens || undefined,
          };
        }
      });

      setChatHistory(loadedMessages);

      // Set last user message for repeat/edit functionality
      const lastUserMsg = fullSession.messages.filter(m => m.role === 'user').pop();
      if (lastUserMsg) {
        setLastUserMessage(lastUserMsg.content);
      }

      // Close history panel
      setShowHistory(false);
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setIsLoadingSession(false);
    }
  };

  const fetchHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/chat/profiles/${profileId}/history`
      );
      if (response.ok) {
        const data = await response.json();
        setHistoryData(data);
      }
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    if (showHistory && !historyData) {
      fetchHistory();
    }
  }, [showHistory]);

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
    setCurrentSessionId(null); // Start fresh session
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
                    tokens: event.tokens_so_far,
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
                    tokens: event.total_tokens,
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
            onClick={() => {
              setShowHistory(!showHistory);
              if (!showHistory) fetchHistory();
            }}
            className={`p-1 hover:text-white ${showHistory ? 'text-primary-400' : 'text-gray-400'}`}
            title="View chat history"
          >
            <History className="h-4 w-4" />
          </button>
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

      {/* History Panel */}
      {showHistory && (
        <div className="border-b border-gray-800 bg-gray-950 p-4">
          <div className="flex justify-between items-center mb-3">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium text-gray-200">Recent Chats</h4>
              {historyData && (
                <span className="text-xs text-gray-500">
                  {historyData.total_tokens.toLocaleString()} tokens
                  <span className="ml-1 text-green-400">
                    (${calculateCost(historyData.total_tokens).toFixed(4)})
                  </span>
                </span>
              )}
            </div>
            <button
              onClick={() => setShowHistory(false)}
              className="p-1 text-gray-400 hover:text-white"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {isLoadingHistory ? (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            </div>
          ) : historyData?.sessions.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No chat history yet</p>
          ) : (
            <>
              <div className="space-y-2">
                {historyData?.sessions.slice(0, 5).map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-2 bg-gray-800 rounded hover:bg-gray-700 cursor-pointer"
                    onClick={() => loadSession(session.id)}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-200 truncate">
                        {session.initial_prompt}
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(session.created_at).toLocaleString()} · {session.total_steps} steps
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <span className={`text-xs px-1.5 py-0.5 rounded ${
                        session.status === 'completed' ? 'bg-green-900/50 text-green-400' :
                        session.status === 'error' ? 'bg-red-900/50 text-red-400' :
                        session.status === 'cancelled' ? 'bg-orange-900/50 text-orange-400' :
                        'bg-gray-700 text-gray-400'
                      }`}>
                        {session.status}
                      </span>
                      <div className="text-right">
                        <p className="text-xs text-gray-400">
                          {session.total_tokens.toLocaleString()} tokens
                        </p>
                        <p className="text-xs text-green-400">
                          ${calculateCost(session.total_tokens).toFixed(4)}
                        </p>
                      </div>
                      <ChevronRight className="h-4 w-4 text-gray-500" />
                    </div>
                  </div>
                ))}
              </div>
              {(historyData?.total_sessions || 0) > 5 && (
                <a
                  href="/history"
                  className="mt-3 block text-center text-sm text-primary-400 hover:text-primary-300"
                >
                  View all {historyData?.total_sessions} sessions
                </a>
              )}
            </>
          )}
        </div>
      )}

      {/* Chat History */}
      <div
        className="overflow-y-auto p-4 space-y-3"
        style={{ height: `${chatHeight}px` }}
      >
        {isLoadingSession ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
            <span className="ml-2 text-gray-400 text-sm">Loading chat...</span>
          </div>
        ) : chatHistory.length === 0 ? (
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
                <div className="flex justify-between items-center text-xs opacity-60 mt-1">
                  <span>{item.timestamp.toLocaleTimeString()}</span>
                  {item.tokens !== undefined && item.tokens > 0 && (
                    <span className="ml-2 px-1.5 py-0.5 bg-gray-700 rounded text-gray-300">
                      {item.tokens.toLocaleString()} tokens
                    </span>
                  )}
                </div>
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
        {/* Auto-scroll anchor */}
        <div ref={chatEndRef} />
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