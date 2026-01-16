'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Loader2, MonitorOff, Server, Wifi, Monitor, Grid } from 'lucide-react';
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
  const [showGrid, setShowGrid] = useState(false);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const [lastClickPos, setLastClickPos] = useState<{ x: number; y: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number; clientX: number; clientY: number } | null>(null);
  const [dragEnd, setDragEnd] = useState<{ x: number; y: number } | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const tapIdRef = useRef(0);
  const typingTimeoutRef = useRef<NodeJS.Timeout>();

  // Minimum distance (in pixels) to consider it a swipe instead of a tap
  const SWIPE_THRESHOLD = 30;

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
      // WebSockets need direct connection to API (can't proxy through Next.js)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.hostname;
      // Map UI port to API port (3100 -> 8100, 3000 -> 8000)
      const uiPort = parseInt(window.location.port || '3100', 10);
      const apiPort = uiPort - 3000 + 8000; // 3100 -> 8100, 3000 -> 8000
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

  const handleMouseDown = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !isReady || !isConnected) return;

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    setDragStart({ x, y, clientX: e.clientX, clientY: e.clientY });
    setIsDragging(true);
    setDragEnd(null);
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !isReady || !isConnected || !dragStart) {
      setIsDragging(false);
      setDragStart(null);
      setDragEnd(null);
      return;
    }

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    // Calculate distance
    const distance = Math.sqrt(
      Math.pow(e.clientX - dragStart.clientX, 2) +
      Math.pow(e.clientY - dragStart.clientY, 2)
    );

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (distance >= SWIPE_THRESHOLD) {
        // Swipe gesture
        wsRef.current.send(JSON.stringify({
          command: 'swipe',
          x1: dragStart.x,
          y1: dragStart.y,
          x2: x,
          y2: y,
          duration: 300
        }));

        // Visual feedback for swipe
        setLastClickPos({ x: dragStart.x, y: dragStart.y });
      } else {
        // Tap gesture
        wsRef.current.send(JSON.stringify({
          command: 'tap',
          x: dragStart.x,
          y: dragStart.y
        }));

        // Visual feedback - show tap indicator
        showTapFeedback(dragStart.clientX, dragStart.clientY);
        setLastClickPos({ x: dragStart.x, y: dragStart.y });
      }
    } else if (onTap && distance < SWIPE_THRESHOLD) {
      // Fallback to HTTP API for tap
      onTap(dragStart.x, dragStart.y);
    }

    setIsDragging(false);
    setDragStart(null);
    setDragEnd(null);
  };

  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    // Click is now handled by mouseUp - this is just for cases where mousedown/up doesn't fire
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !isReady) return;

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    setMousePos({ x, y });

    // Update drag end position while dragging
    if (isDragging && dragStart) {
      setDragEnd({ x, y });
    }
  };

  const handleMouseLeave = (e: React.MouseEvent<HTMLImageElement>) => {
    setMousePos(null);

    // If we're dragging and mouse leaves, complete the swipe at the edge
    if (isDragging && dragStart && imgRef.current) {
      const rect = imgRef.current.getBoundingClientRect();
      const scaleX = imgRef.current.naturalWidth / rect.width;
      const scaleY = imgRef.current.naturalHeight / rect.height;

      // Clamp to image bounds
      const x = Math.max(0, Math.min(imgRef.current.naturalWidth - 1,
        Math.round((e.clientX - rect.left) * scaleX)));
      const y = Math.max(0, Math.min(imgRef.current.naturalHeight - 1,
        Math.round((e.clientY - rect.top) * scaleY)));

      const distance = Math.sqrt(
        Math.pow(e.clientX - dragStart.clientX, 2) +
        Math.pow(e.clientY - dragStart.clientY, 2)
      );

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && distance >= SWIPE_THRESHOLD) {
        wsRef.current.send(JSON.stringify({
          command: 'swipe',
          x1: dragStart.x,
          y1: dragStart.y,
          x2: x,
          y2: y,
          duration: 300
        }));
      }

      setIsDragging(false);
      setDragStart(null);
      setDragEnd(null);
    }
  };

  // Handle paste event (Ctrl-V / Cmd-V)
  const handlePaste = async (e: React.ClipboardEvent) => {
    if (!isReady || !isConnected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    e.preventDefault();
    const text = e.clipboardData.getData('text');

    if (text) {
      // Show typing indicator
      setIsTyping(true);
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      typingTimeoutRef.current = setTimeout(() => setIsTyping(false), 1000);

      // Send text via WebSocket
      wsRef.current.send(JSON.stringify({
        command: 'text',
        text: text
      }));

      console.log('Pasted text:', text.substring(0, 50) + (text.length > 50 ? '...' : ''));
    }
  };

  // Handle keyboard input
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isReady || !isConnected || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    // Let paste event handler deal with Ctrl-V / Cmd-V
    if ((e.ctrlKey || e.metaKey) && e.key === 'v') {
      return; // Will be handled by onPaste event
    }

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
      onPaste={handlePaste}
      onFocus={handleFocus}
      onBlur={handleBlur}
    >
      {/* Connection status indicators - always visible */}
      <ConnectionStatus />

      {/* Grid toggle button - always visible when ready */}
      {isReady && (
        <button
          onClick={() => setShowGrid(!showGrid)}
          className={`absolute top-12 right-2 z-20 rounded-full bg-gray-800/80 p-2 transition-colors ${
            showGrid ? 'text-primary-500 bg-gray-700/80' : 'text-gray-400 hover:text-white'
          }`}
          title="Toggle coordinate grid"
        >
          <Grid className="h-4 w-4" />
        </button>
      )}

      {/* Typing indicator */}
      {isTyping && (
        <div className="absolute top-2 right-2 z-20 bg-primary-500/20 rounded px-2 py-1 text-xs text-primary-400">
          Typing...
        </div>
      )}

      {/* Focus hint */}
      {!isFocused && isReady && isConnected && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-20 bg-gray-800/90 rounded px-2 py-1 text-xs text-gray-400">
          Click to focus, then type or paste (Ctrl/Cmd-V)
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
          <>
            <img
              ref={imgRef}
              src={currentFrame}
              alt="Device screen"
              className={`w-full h-full object-contain ${isDragging ? 'cursor-grabbing' : 'cursor-pointer'}`}
              onMouseDown={handleMouseDown}
              onMouseUp={handleMouseUp}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
              draggable={false}
            />

            {/* Coordinate overlay */}
            {showGrid && imgRef.current && (
              <CoordinateOverlay
                imgRef={imgRef}
                mousePos={mousePos}
                lastClickPos={lastClickPos}
              />
            )}

            {/* Mouse position tooltip */}
            {mousePos && imgRef.current && (
              <div
                className="absolute z-20 bg-black/80 text-white px-2 py-1 rounded text-xs pointer-events-none"
                style={{
                  left: `${(mousePos.x / imgRef.current.naturalWidth) * 100}%`,
                  top: `${(mousePos.y / imgRef.current.naturalHeight) * 100}%`,
                  transform: 'translate(-50%, -150%)',
                }}
              >
                {mousePos.x}, {mousePos.y}
              </div>
            )}
          </>
        )}
        
        {/* Swipe indicator while dragging */}
        {isDragging && dragStart && dragEnd && imgRef.current && (
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none z-30"
            viewBox={`0 0 ${imgRef.current.naturalWidth} ${imgRef.current.naturalHeight}`}
            preserveAspectRatio="xMidYMid meet"
          >
            {/* Swipe line */}
            <line
              x1={dragStart.x}
              y1={dragStart.y}
              x2={dragEnd.x}
              y2={dragEnd.y}
              stroke="#3b82f6"
              strokeWidth="6"
              strokeLinecap="round"
              opacity={0.8}
            />
            {/* Start point */}
            <circle
              cx={dragStart.x}
              cy={dragStart.y}
              r="15"
              fill="#3b82f6"
              opacity={0.6}
            />
            {/* End point / arrow */}
            <circle
              cx={dragEnd.x}
              cy={dragEnd.y}
              r="20"
              fill="none"
              stroke="#3b82f6"
              strokeWidth="4"
              opacity={0.8}
            />
          </svg>
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

// Coordinate overlay component
interface CoordinateOverlayProps {
  imgRef: React.RefObject<HTMLImageElement>;
  mousePos: { x: number; y: number } | null;
  lastClickPos: { x: number; y: number } | null;
}

function CoordinateOverlay({ imgRef, mousePos, lastClickPos }: CoordinateOverlayProps) {
  if (!imgRef.current) return null;

  const width = imgRef.current.naturalWidth;
  const height = imgRef.current.naturalHeight;
  const gridSize = 100; // Grid line every 100 pixels

  // Generate grid lines
  const verticalLines = [];
  const horizontalLines = [];

  for (let x = 0; x <= width; x += gridSize) {
    verticalLines.push(x);
  }

  for (let y = 0; y <= height; y += gridSize) {
    horizontalLines.push(y);
  }

  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
    >
      {/* Grid lines */}
      <g opacity={0.3}>
        {verticalLines.map((x) => (
          <line
            key={`v-${x}`}
            x1={x}
            y1={0}
            x2={x}
            y2={height}
            stroke="white"
            strokeWidth="2"
          />
        ))}
        {horizontalLines.map((y) => (
          <line
            key={`h-${y}`}
            x1={0}
            y1={y}
            x2={width}
            y2={y}
            stroke="white"
            strokeWidth="2"
          />
        ))}
      </g>

      {/* Axis labels */}
      <g opacity={0.7}>
        {verticalLines.map((x) => (
          <text
            key={`vl-${x}`}
            x={x + 5}
            y={25}
            fill="white"
            fontSize="24"
            fontWeight="bold"
            className="select-none"
          >
            {x}
          </text>
        ))}
        {horizontalLines.map((y) => (
          <text
            key={`hl-${y}`}
            x={10}
            y={y + 25}
            fill="white"
            fontSize="24"
            fontWeight="bold"
            className="select-none"
          >
            {y}
          </text>
        ))}
      </g>

      {/* Last click position */}
      {lastClickPos && (
        <g>
          <circle
            cx={lastClickPos.x}
            cy={lastClickPos.y}
            r="15"
            fill="none"
            stroke="#ef4444"
            strokeWidth="4"
          />
          <circle
            cx={lastClickPos.x}
            cy={lastClickPos.y}
            r="30"
            fill="none"
            stroke="#ef4444"
            strokeWidth="2"
            opacity={0.5}
          />
          <text
            x={lastClickPos.x + 40}
            y={lastClickPos.y - 20}
            fill="#ef4444"
            fontSize="28"
            fontWeight="bold"
            className="select-none"
          >
            {lastClickPos.x}, {lastClickPos.y}
          </text>
        </g>
      )}

      {/* Mouse hover crosshair */}
      {mousePos && (
        <g opacity={0.6}>
          <line
            x1={mousePos.x}
            y1={0}
            x2={mousePos.x}
            y2={height}
            stroke="#3b82f6"
            strokeWidth="2"
            strokeDasharray="10,10"
          />
          <line
            x1={0}
            y1={mousePos.y}
            x2={width}
            y2={mousePos.y}
            stroke="#3b82f6"
            strokeWidth="2"
            strokeDasharray="10,10"
          />
        </g>
      )}
    </svg>
  );
}