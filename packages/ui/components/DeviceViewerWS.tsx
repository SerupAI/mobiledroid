'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Loader2, MonitorOff, Server, Wifi, Monitor } from 'lucide-react';
import { api } from '@/lib/api';

interface DeviceViewerProps {
  profileId: string;
  onTap?: (x: number, y: number) => void;
}

export function DeviceViewerWS({ profileId, onTap }: DeviceViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [currentFrame, setCurrentFrame] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tapIndicators, setTapIndicators] = useState<Array<{id: number, x: number, y: number}>>([]);
  const [isFocused, setIsFocused] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const tapIdRef = useRef(0);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();

  // Poll device readiness
  const { data: readiness } = useQuery({
    queryKey: ['device-ready', profileId],
    queryFn: () => api.checkDeviceReady(profileId),
    refetchInterval: 5000,
  });

  const isReady = readiness?.ready ?? false;

  // Show tap feedback
  const showTapFeedback = (clientX: number, clientY: number) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = clientX - rect.left;
    const y = clientY - rect.top;
    const id = tapIdRef.current++;

    setTapIndicators(prev => [...prev, { id, x, y }]);

    // Remove after animation
    setTimeout(() => {
      setTapIndicators(prev => prev.filter(tap => tap.id !== id));
    }, 600);
  };

  // WebSocket connection
  useEffect(() => {
    if (!isReady) return;

    const connectWebSocket = () => {
      // Build WebSocket URL based on current location
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      const apiPort = process.env.NEXT_PUBLIC_API_URL?.match(/:(\d+)/)?.[1] || '8100';
      const wsUrl = `${protocol}//${host}:${apiPort}/ws/profiles/${profileId}/stream`;

      console.log('Connecting to WebSocket:', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'frame' && data.data) {
            // Convert base64 to data URL
            setCurrentFrame(`data:image/png;base64,${data.data}`);
          } else if (data.type === 'command_result') {
            // Handle command results
            if (!data.success) {
              console.error('Command failed:', data.command);
            }
          } else if (data.error) {
            setError(data.error);
          }
        } catch (e) {
          console.error('WebSocket message error:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect with exponential backoff
        if (reconnectAttemptsRef.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
          reconnectAttemptsRef.current++;
          
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay);
        }
      };
    };

    connectWebSocket();

    // Cleanup
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isReady, profileId]);

  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !isReady || !isConnected) return;

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    // Send tap command through WebSocket for lower latency
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        command: 'tap',
        x,
        y
      }));
      
      // Visual feedback - show tap indicator
      showTapFeedback(e.clientX, e.clientY);
    } else if (onTap) {
      // Fallback to HTTP API
      onTap(x, y);
    }
  };

  // Handle keyboard input
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isReady || !isConnected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    // Show typing indicator
    setIsTyping(true);
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 500);

    // Handle special keys
    const specialKeys: { [key: string]: string } = {
      'Enter': 'KEYCODE_ENTER',
      'Backspace': 'KEYCODE_DEL',
      'Delete': 'KEYCODE_FORWARD_DEL',
      'Tab': 'KEYCODE_TAB',
      'Escape': 'KEYCODE_ESCAPE',
      'ArrowUp': 'KEYCODE_DPAD_UP',
      'ArrowDown': 'KEYCODE_DPAD_DOWN',
      'ArrowLeft': 'KEYCODE_DPAD_LEFT',
      'ArrowRight': 'KEYCODE_DPAD_RIGHT',
      'Home': 'KEYCODE_MOVE_HOME',
      'End': 'KEYCODE_MOVE_END',
      'PageUp': 'KEYCODE_PAGE_UP',
      'PageDown': 'KEYCODE_PAGE_DOWN',
      ' ': 'KEYCODE_SPACE',
    };

    if (e.key in specialKeys) {
      e.preventDefault();
      wsRef.current.send(JSON.stringify({
        command: 'key',
        keycode: specialKeys[e.key]
      }));
    } else if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
      // Regular character input
      e.preventDefault();
      wsRef.current.send(JSON.stringify({
        command: 'text',
        text: e.key
      }));
    }
  };

  // Focus handlers
  const handleFocus = () => setIsFocused(true);
  const handleBlur = () => {
    setIsFocused(false);
    setIsTyping(false);
  };

  // Connection status indicators component
  const ConnectionStatus = () => {
    if (!readiness) return null;
    
    const steps = [
      { key: 'container', label: 'Container', done: readiness.container_running, icon: Server },
      { key: 'adb', label: 'ADB', done: readiness.adb_connected, icon: Wifi },
      { key: 'screen', label: 'Screen', done: readiness.screen_available, icon: Monitor },
      { key: 'stream', label: 'Stream', done: isConnected, icon: RefreshCw },
    ];

    return (
      <div className="flex items-center gap-2 mb-3">
        {steps.map((step) => (
          <div key={step.key} className="flex items-center gap-1">
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center ${
                step.done
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-gray-800 text-gray-500'
              }`}
            >
              <step.icon className={`h-3 w-3 ${step.key === 'stream' && isConnected ? 'animate-pulse' : ''}`} />
            </div>
            <span className={`text-xs ${step.done ? 'text-green-400' : 'text-gray-500'}`}>
              {step.label}
            </span>
          </div>
        ))}
        <span className="text-xs text-gray-400 ml-auto">{readiness?.status}</span>
      </div>
    );
  };

  // Render boot progress
  const renderBootProgress = () => {
    if (!readiness) {
      return (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95 z-10">
          <Loader2 className="h-10 w-10 animate-spin text-primary-500 mb-4" />
          <p className="text-sm text-gray-300">Checking device status...</p>
        </div>
      );
    }

    const steps = [
      { key: 'container', label: 'Container', done: readiness.container_running, icon: Server },
      { key: 'adb', label: 'ADB', done: readiness.adb_connected, icon: Wifi },
      { key: 'screen', label: 'Screen', done: readiness.screen_available, icon: Monitor },
    ];

    return (
      <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95 z-10">
        <Loader2 className="h-10 w-10 animate-spin text-primary-500 mb-4" />
        <p className="text-sm text-gray-300 mb-2">{readiness.message}</p>

        <div className="flex items-center gap-4 mt-4">
          {steps.map((step) => (
            <div key={step.key} className="flex flex-col items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step.done
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-gray-800 text-gray-500'
                }`}
              >
                <step.icon className="h-5 w-5" />
              </div>
              <span className={`text-xs mt-1 ${step.done ? 'text-green-400' : 'text-gray-500'}`}>
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div 
      className={`relative outline-none ${isFocused ? 'ring-2 ring-primary-500 ring-offset-2 ring-offset-gray-900 rounded-lg' : ''}`} 
      ref={containerRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onFocus={handleFocus}
      onBlur={handleBlur}
    >
      {/* Connection status indicators - always visible */}
      <ConnectionStatus />

      {/* Typing indicator */}
      {isTyping && (
        <div className="absolute top-2 right-2 z-20 bg-primary-500/20 rounded px-2 py-1 text-xs text-primary-400">
          Typing...
        </div>
      )}

      {/* Focus hint */}
      {!isFocused && isReady && isConnected && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-20 bg-gray-800/90 rounded px-2 py-1 text-xs text-gray-400">
          Click to focus and type
        </div>
      )}

      {/* Device screen container */}
      <div className="aspect-phone bg-black rounded-lg overflow-hidden relative">
        {/* Not ready - show boot progress */}
        {!isReady && renderBootProgress()}

        {/* Ready but no stream */}
        {isReady && !currentFrame && !error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 z-10">
            <Loader2 className="h-8 w-8 animate-spin text-primary-500 mb-2" />
            <p className="text-sm text-gray-400">Connecting stream...</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95 z-10">
            <MonitorOff className="h-12 w-12 text-gray-600 mb-3" />
            <p className="text-sm text-gray-400 mb-4">{error}</p>
          </div>
        )}

        {/* WebSocket stream */}
        {currentFrame && (
          <img
            ref={imgRef}
            src={currentFrame}
            alt="Device screen"
            className="w-full h-full object-contain cursor-pointer"
            onClick={handleClick}
            draggable={false}
          />
        )}
        
        {/* Tap indicators */}
        {tapIndicators.map(tap => (
          <div
            key={tap.id}
            className="absolute pointer-events-none"
            style={{
              left: tap.x,
              top: tap.y,
              transform: 'translate(-50%, -50%)',
            }}
          >
            <div className="tap-indicator" />
          </div>
        ))}
      </div>
    </div>
  );
}