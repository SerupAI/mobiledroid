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
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);

  // Poll device readiness
  const { data: readiness } = useQuery({
    queryKey: ['device-ready', profileId],
    queryFn: () => api.checkDeviceReady(profileId),
    refetchInterval: 5000,
  });

  const isReady = readiness?.ready ?? false;

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
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isReady, profileId]);

  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !onTap || !isReady) return;

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    onTap(x, y);
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
    <div className="relative" ref={containerRef}>
      {/* Connection status indicators - always visible */}
      <ConnectionStatus />

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
      </div>
    </div>
  );
}