'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { RefreshCw, Loader2, MonitorOff, Server, Wifi, Monitor, Grid } from 'lucide-react';
import { api } from '@/lib/api';

interface DeviceViewerProps {
  profileId: string;
  onTap?: (x: number, y: number) => void;
}

export function DeviceViewer({ profileId, onTap }: DeviceViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [isImageLoading, setIsImageLoading] = useState(true);
  const [imageError, setImageError] = useState(false);
  const [imageKey, setImageKey] = useState(0);
  const [showGrid, setShowGrid] = useState(false);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const [lastClickPos, setLastClickPos] = useState<{ x: number; y: number } | null>(null);

  // Poll device readiness
  const { data: readiness } = useQuery({
    queryKey: ['device-ready', profileId],
    queryFn: () => api.checkDeviceReady(profileId),
    refetchInterval: (query) => {
      // Poll faster while not ready, slower once ready
      return query.state.data?.ready ? 5000 : 2000;
    },
  });

  const isReady = readiness?.ready ?? false;

  // Only refresh screenshot when device is ready
  useEffect(() => {
    if (!isReady) return;

    const interval = setInterval(() => {
      setImageKey((k) => k + 1);
    }, 200); // 200ms = 5 fps for smoother interaction

    return () => clearInterval(interval);
  }, [isReady]);

  const refreshScreenshot = () => {
    setImageKey((k) => k + 1);
    setIsImageLoading(true);
    setImageError(false);
  };

  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !onTap || !isReady) return;

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    setLastClickPos({ x, y });
    onTap(x, y);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLImageElement>) => {
    if (!imgRef.current || !isReady) return;

    const rect = imgRef.current.getBoundingClientRect();
    const scaleX = imgRef.current.naturalWidth / rect.width;
    const scaleY = imgRef.current.naturalHeight / rect.height;

    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);

    setMousePos({ x, y });
  };

  const handleMouseLeave = () => {
    setMousePos(null);
  };

  const handleImageLoad = () => {
    setIsImageLoading(false);
    setImageError(false);
  };

  const handleImageError = () => {
    setIsImageLoading(false);
    setImageError(true);
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

  // Connection status indicators component
  const ConnectionStatus = () => {
    if (!readiness) return null;
    
    const steps = [
      { key: 'container', label: 'Container', done: readiness.container_running, icon: Server },
      { key: 'adb', label: 'ADB', done: readiness.adb_connected, icon: Wifi },
      { key: 'screen', label: 'Screen', done: readiness.screen_available, icon: Monitor },
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
              <step.icon className="h-3 w-3" />
            </div>
            <span className={`text-xs ${step.done ? 'text-green-400' : 'text-gray-500'}`}>
              {step.label}
            </span>
          </div>
        ))}
        <span className="text-xs text-gray-400 ml-auto">{readiness.status}</span>
      </div>
    );
  };

  return (
    <div className="relative" ref={containerRef}>
      {/* Connection status indicators - always visible */}
      <ConnectionStatus />
      
      {/* Refresh button - only show when ready */}
      {isReady && (
        <button
          onClick={refreshScreenshot}
          className="absolute top-12 right-2 z-10 rounded-full bg-gray-800/80 p-2 text-gray-400 hover:text-white transition-colors"
          title="Refresh screenshot"
        >
          <RefreshCw className={`h-4 w-4 ${isImageLoading ? 'animate-spin' : ''}`} />
        </button>
      )}

      {/* Grid toggle button - only in debug mode and when ready */}
      {process.env.NEXT_PUBLIC_DEBUG === 'true' && isReady && (
        <button
          onClick={() => setShowGrid(!showGrid)}
          className={`absolute top-12 right-12 z-10 rounded-full bg-gray-800/80 p-2 transition-colors ${
            showGrid ? 'text-primary-500 bg-gray-700/80' : 'text-gray-400 hover:text-white'
          }`}
          title="Toggle coordinate grid"
        >
          <Grid className="h-4 w-4" />
        </button>
      )}

      {/* Device screen container */}
      <div className="aspect-phone bg-black rounded-lg overflow-hidden relative">
        {/* Not ready - show boot progress */}
        {!isReady && renderBootProgress()}

        {/* Ready but image error */}
        {isReady && imageError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/95 z-10">
            <MonitorOff className="h-12 w-12 text-gray-600 mb-3" />
            <p className="text-sm text-gray-400 mb-4">Screenshot failed</p>
            <button
              onClick={refreshScreenshot}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-md text-sm font-medium transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Actual screenshot image - always try to render when ready */}
        {isReady && (
          <>
            {/* Show loading only on first load */}
            {isImageLoading && imageKey === 0 && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-900/80 z-10">
                <Loader2 className="h-8 w-8 animate-spin text-primary-500 mb-2" />
                <p className="text-sm text-gray-400">Loading screen...</p>
              </div>
            )}
            {/* Current image */}
            <img
              ref={imgRef}
              src={`${api.getScreenshotUrl(profileId)}?t=${imageKey}`}
              alt="Device screen"
              className={`w-full h-full object-contain cursor-pointer ${imageError || isImageLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-100`}
              onLoad={handleImageLoad}
              onError={handleImageError}
              onClick={handleClick}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
              draggable={false}
            />
            {/* Preload next image */}
            <img
              src={`${api.getScreenshotUrl(profileId)}?t=${imageKey + 1}`}
              alt="Preload"
              className="hidden"
              aria-hidden="true"
            />

            {/* Coordinate overlay - only in debug mode */}
            {process.env.NEXT_PUBLIC_DEBUG === 'true' && imgRef.current && showGrid && (
              <CoordinateOverlay
                imgRef={imgRef}
                mousePos={mousePos}
                lastClickPos={lastClickPos}
              />
            )}

            {/* Mouse position tooltip - only in debug mode */}
            {process.env.NEXT_PUBLIC_DEBUG === 'true' && mousePos && imgRef.current && (
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
      preserveAspectRatio="none"
      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
    >
      {/* Grid lines */}
      <g opacity={0.2}>
        {verticalLines.map((x) => (
          <line
            key={`v-${x}`}
            x1={x}
            y1={0}
            x2={x}
            y2={height}
            stroke="white"
            strokeWidth="1"
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
            strokeWidth="1"
          />
        ))}
      </g>

      {/* Axis labels */}
      <g opacity={0.5}>
        {verticalLines.map((x) => (
          <text
            key={`vl-${x}`}
            x={x}
            y={20}
            fill="white"
            fontSize="12"
            textAnchor="middle"
            className="select-none"
          >
            {x}
          </text>
        ))}
        {horizontalLines.map((y) => (
          <text
            key={`hl-${y}`}
            x={10}
            y={y}
            fill="white"
            fontSize="12"
            textAnchor="start"
            dominantBaseline="middle"
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
            r="5"
            fill="none"
            stroke="#ef4444"
            strokeWidth="2"
          />
          <circle
            cx={lastClickPos.x}
            cy={lastClickPos.y}
            r="10"
            fill="none"
            stroke="#ef4444"
            strokeWidth="1"
            opacity={0.5}
          />
          <text
            x={lastClickPos.x + 15}
            y={lastClickPos.y - 15}
            fill="#ef4444"
            fontSize="14"
            fontWeight="bold"
            className="select-none"
          >
            {lastClickPos.x}, {lastClickPos.y}
          </text>
        </g>
      )}

      {/* Mouse hover crosshair */}
      {mousePos && (
        <g opacity={0.5}>
          <line
            x1={mousePos.x}
            y1={0}
            x2={mousePos.x}
            y2={height}
            stroke="#3b82f6"
            strokeWidth="1"
            strokeDasharray="5,5"
          />
          <line
            x1={0}
            y1={mousePos.y}
            x2={width}
            y2={mousePos.y}
            stroke="#3b82f6"
            strokeWidth="1"
            strokeDasharray="5,5"
          />
        </g>
      )}
    </svg>
  );
}
