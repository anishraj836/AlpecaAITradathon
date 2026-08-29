'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { VolatilitySurface } from '@/types/voltron';

interface VolSurface3DCanvasProps {
  surfaceData: VolatilitySurface;
}

interface Point3D {
  x: number; // Strike dimension
  y: number; // DTE dimension
  z: number; // IV height dimension
  strike: number;
  dte: number;
  iv: number;
}

interface Quad3D {
  p1: Point3D;
  p2: Point3D;
  p3: Point3D;
  p4: Point3D;
  avgZ: number;
  avgIv: number;
  strikeMid: number;
  dteMid: number;
}

const DEFAULT_STRATEGY_LEGS = [
  { strike: 625, type: 'PUT', action: 'BUY WING', color: '#00e5ff' },
  { strike: 630, type: 'PUT', action: 'SELL SHORT', color: '#ff5050' },
  { strike: 660, type: 'CALL', action: 'SELL SHORT', color: '#fec931' },
  { strike: 665, type: 'CALL', action: 'BUY WING', color: '#00e5ff' },
];

export const VolSurface3DCanvas: React.FC<VolSurface3DCanvasProps> = ({ surfaceData }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Rotation angles in degrees
  const [rotX, setRotX] = useState<number>(30);
  const [rotY, setRotY] = useState<number>(-35);
  const [zoom, setZoom] = useState<number>(1.05);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const [showStrategyOverlay, setShowStrategyOverlay] = useState<boolean>(true);
  const [hoveredPoint, setHoveredPoint] = useState<{ strike: number; dte: number; iv: number; screenX: number; screenY: number } | null>(null);

  // Grid Resolution
  const numStrikes = 18;
  const numDtes = 14;
  const minStrike = 615;
  const maxStrike = 675;
  const minDte = 7;
  const maxDte = 60;
  const spotPrice = surfaceData.spotPrice || 645.31;

  // Compute IV at a given strike and DTE
  const computeIV = useCallback((k: number, dte: number) => {
    const moneyness = (k - spotPrice) / spotPrice;
    // Volatility smile + skew + term structure
    const termFactor = Math.sqrt(30 / Math.max(dte, 1)) * 1.8;
    const skewFactor = moneyness < 0 
      ? Math.pow(moneyness * 100, 2) * 0.085 - moneyness * 36
      : Math.pow(moneyness * 100, 2) * 0.035;
    const baseIV = 18.2 + termFactor + skewFactor;
    return Math.max(13.0, Math.min(44.0, baseIV));
  }, [spotPrice]);

  // Generate 3D grid vertices
  const generateMesh = useCallback(() => {
    const grid: Point3D[][] = [];

    for (let i = 0; i < numStrikes; i++) {
      grid[i] = [];
      const strike = minStrike + (i / (numStrikes - 1)) * (maxStrike - minStrike);
      // Center strike around 0: [-160, 160]
      const x = ((strike - minStrike) / (maxStrike - minStrike) - 0.5) * 340;

      for (let j = 0; j < numDtes; j++) {
        const dte = minDte + (j / (numDtes - 1)) * (maxDte - minDte);
        // Center DTE around 0: [-150, 150]
        const y = ((dte - minDte) / (maxDte - minDte) - 0.5) * 300;

        const iv = computeIV(strike, dte);
        // Scale IV to Z-height: [0, 140]
        const z = (iv - 14.0) * 4.4;

        grid[i][j] = { x, y, z, strike, dte, iv };
      }
    }
    return grid;
  }, [computeIV]);

  // Main Render Loop
  const renderSurface = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2 + 20;

    ctx.clearRect(0, 0, width, height);

    // Convert angles to radians
    const radX = (rotX * Math.PI) / 180;
    const radY = (rotY * Math.PI) / 180;
    const cosX = Math.cos(radX);
    const sinX = Math.sin(radX);
    const cosY = Math.cos(radY);
    const sinY = Math.sin(radY);

    // 3D rotation & perspective transformation
    const project = (p: Point3D) => {
      // 1. Rotate Y (Yaw)
      const x1 = p.x * cosY + p.y * sinY;
      const y1 = -p.x * sinY + p.y * cosY;
      const z1 = p.z;

      // 2. Rotate X (Pitch)
      const x2 = x1;
      const y2 = y1 * cosX - z1 * sinX;
      const z2 = y1 * sinX + z1 * cosX;

      // 3. Camera perspective projection
      const cameraDistance = 700;
      const fov = 520 * zoom;
      const depth = cameraDistance + z2;
      const scale = fov / Math.max(depth, 1);

      return {
        screenX: centerX + x2 * scale,
        screenY: centerY - y2 * scale, // Flip Y for screen space
        depth: z2,
        raw: p,
      };
    };

    const grid = generateMesh();

    // Build quads for depth-sorted rendering
    const quads: Quad3D[] = [];
    for (let i = 0; i < numStrikes - 1; i++) {
      for (let j = 0; j < numDtes - 1; j++) {
        const p1 = grid[i][j];
        const p2 = grid[i + 1][j];
        const p3 = grid[i + 1][j + 1];
        const p4 = grid[i][j + 1];
        const avgZ = (p1.z + p2.z + p3.z + p4.z) / 4;
        const avgIv = (p1.iv + p2.iv + p3.iv + p4.iv) / 4;
        const strikeMid = (p1.strike + p2.strike) / 2;
        const dteMid = (p1.dte + p4.dte) / 2;
        quads.push({ p1, p2, p3, p4, avgZ, avgIv, strikeMid, dteMid });
      }
    }

    // Sort quads from back to front (painter's algorithm)
    quads.sort((a, b) => {
      const projA = project({ x: (a.p1.x + a.p3.x) / 2, y: (a.p1.y + a.p3.y) / 2, z: a.avgZ, strike: 0, dte: 0, iv: a.avgIv });
      const projB = project({ x: (b.p1.x + b.p3.x) / 2, y: (b.p1.y + b.p3.y) / 2, z: b.avgZ, strike: 0, dte: 0, iv: b.avgIv });
      return projA.depth - projB.depth;
    });

    // 1. Draw 3D Base Reference Grid
    ctx.strokeStyle = 'rgba(59, 73, 76, 0.35)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = -170; i <= 170; i += 34) {
      const start = project({ x: i, y: -150, z: 0, strike: 0, dte: 0, iv: 0 });
      const end = project({ x: i, y: 150, z: 0, strike: 0, dte: 0, iv: 0 });
      ctx.moveTo(start.screenX, start.screenY);
      ctx.lineTo(end.screenX, end.screenY);
    }
    for (let j = -150; j <= 150; j += 30) {
      const start = project({ x: -170, y: j, z: 0, strike: 0, dte: 0, iv: 0 });
      const end = project({ x: 170, y: j, z: 0, strike: 0, dte: 0, iv: 0 });
      ctx.moveTo(start.screenX, start.screenY);
      ctx.lineTo(end.screenX, end.screenY);
    }
    ctx.stroke();

    // 2. Draw 3D Surface Polygons with IV Height Color Shading
    for (const quad of quads) {
      const proj1 = project(quad.p1);
      const proj2 = project(quad.p2);
      const proj3 = project(quad.p3);
      const proj4 = project(quad.p4);

      // Color mapping: Cyan (< 20%) -> Yellow (20-28%) -> Crimson (> 28%)
      const normIv = (quad.avgIv - 16.0) / 16.0;
      let fillColor = 'rgba(0, 229, 255, 0.22)';
      let strokeColor = 'rgba(0, 229, 255, 0.55)';

      if (normIv > 0.55) {
        fillColor = 'rgba(255, 75, 75, 0.38)'; // High Put Skew Spike
        strokeColor = 'rgba(255, 100, 100, 0.85)';
      } else if (normIv > 0.25) {
        fillColor = 'rgba(254, 201, 49, 0.28)'; // Elevated Vol Zone
        strokeColor = 'rgba(254, 201, 49, 0.7)';
      }

      ctx.fillStyle = fillColor;
      ctx.strokeStyle = strokeColor;
      ctx.lineWidth = 1;

      ctx.beginPath();
      ctx.moveTo(proj1.screenX, proj1.screenY);
      ctx.lineTo(proj2.screenX, proj2.screenY);
      ctx.lineTo(proj3.screenX, proj3.screenY);
      ctx.lineTo(proj4.screenX, proj4.screenY);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }

    // 3. Draw Strategy Leg Overlays (Active Iron Condor on 3D Surface)
    if (showStrategyOverlay) {
      for (const leg of DEFAULT_STRATEGY_LEGS) {
        const legX = ((leg.strike - minStrike) / (maxStrike - minStrike) - 0.5) * 340;
        const legIv = computeIV(leg.strike, 45); // 45 DTE target
        const legZ = (legIv - 14.0) * 4.4;
        const legY = ((45 - minDte) / (maxDte - minDte) - 0.5) * 300;

        const surfacePoint = project({ x: legX, y: legY, z: legZ, strike: leg.strike, dte: 45, iv: legIv });
        const basePoint = project({ x: legX, y: legY, z: 0, strike: leg.strike, dte: 45, iv: 0 });

        // Vertical pillar
        ctx.strokeStyle = leg.color;
        ctx.lineWidth = 2;
        ctx.setLineDash([2, 2]);
        ctx.beginPath();
        ctx.moveTo(surfacePoint.screenX, surfacePoint.screenY);
        ctx.lineTo(basePoint.screenX, basePoint.screenY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Top Strike Ring
        ctx.fillStyle = leg.color;
        ctx.beginPath();
        ctx.arc(surfacePoint.screenX, surfacePoint.screenY, 4.5, 0, Math.PI * 2);
        ctx.fill();

        // 3D Tag Label
        ctx.fillStyle = 'rgba(10, 16, 18, 0.9)';
        ctx.strokeStyle = leg.color;
        ctx.lineWidth = 1;
        const lWidth = 85;
        const lHeight = 24;
        ctx.fillRect(surfacePoint.screenX - lWidth / 2, surfacePoint.screenY - 32, lWidth, lHeight);
        ctx.strokeRect(surfacePoint.screenX - lWidth / 2, surfacePoint.screenY - 32, lWidth, lHeight);

        ctx.fillStyle = leg.color;
        ctx.font = 'bold 9px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${leg.action} $${leg.strike}`, surfacePoint.screenX, surfacePoint.screenY - 17);
        ctx.textAlign = 'left';
      }
    }

    // 4. Draw 3D Coordinates Axes & Labels
    const origin = project({ x: -170, y: -150, z: 0, strike: 0, dte: 0, iv: 0 });
    
    // Strike Axis (X)
    const xEnd = project({ x: 190, y: -150, z: 0, strike: 0, dte: 0, iv: 0 });
    ctx.strokeStyle = '#00e5ff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.screenX, origin.screenY);
    ctx.lineTo(xEnd.screenX, xEnd.screenY);
    ctx.stroke();

    ctx.fillStyle = '#00e5ff';
    ctx.font = '11px "JetBrains Mono", monospace';
    ctx.fillText('STRIKE ($) →', xEnd.screenX + 8, xEnd.screenY + 4);

    // DTE Axis (Y)
    const yEnd = project({ x: -170, y: 170, z: 0, strike: 0, dte: 0, iv: 0 });
    ctx.strokeStyle = '#cdbdff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.screenX, origin.screenY);
    ctx.lineTo(yEnd.screenX, yEnd.screenY);
    ctx.stroke();

    ctx.fillStyle = '#cdbdff';
    ctx.fillText('DTE (Days) →', yEnd.screenX - 20, yEnd.screenY + 16);

    // IV Height Axis (Z)
    const zEnd = project({ x: -170, y: -150, z: 130, strike: 0, dte: 0, iv: 0 });
    ctx.strokeStyle = '#fec931';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.screenX, origin.screenY);
    ctx.lineTo(zEnd.screenX, zEnd.screenY);
    ctx.stroke();

    ctx.fillStyle = '#fec931';
    ctx.fillText('↑ VOLATILITY (IV %)', zEnd.screenX - 45, zEnd.screenY - 10);

    // 5. Draw ATM Focal Node in True 3D Space ($645.31 spot, 14 DTE)
    const atmX = ((spotPrice - minStrike) / (maxStrike - minStrike) - 0.5) * 340;
    const atmY = ((14 - minDte) / (maxDte - minDte) - 0.5) * 300;
    const atmIv = computeIV(spotPrice, 14);
    const atmZ = (atmIv - 14.0) * 4.4;

    const atmProj = project({ x: atmX, y: atmY, z: atmZ, strike: spotPrice, dte: 14, iv: atmIv });
    const atmBase = project({ x: atmX, y: atmY, z: 0, strike: spotPrice, dte: 14, iv: 0 });

    ctx.strokeStyle = 'rgba(0, 229, 255, 0.8)';
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(atmProj.screenX, atmProj.screenY);
    ctx.lineTo(atmBase.screenX, atmBase.screenY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = '#00e5ff';
    ctx.beginPath();
    ctx.arc(atmProj.screenX, atmProj.screenY, 6, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(atmProj.screenX, atmProj.screenY, 7, 0, Math.PI * 2);
    ctx.stroke();

    // 3D Tag Callout
    ctx.fillStyle = 'rgba(10, 16, 18, 0.9)';
    ctx.strokeStyle = '#00e5ff';
    ctx.lineWidth = 1;
    const tagWidth = 150;
    const tagHeight = 36;
    const tagX = atmProj.screenX + 14;
    const tagY = atmProj.screenY - 20;

    ctx.fillRect(tagX, tagY, tagWidth, tagHeight);
    ctx.strokeRect(tagX, tagY, tagWidth, tagHeight);

    ctx.fillStyle = '#00e5ff';
    ctx.font = 'bold 11px "JetBrains Mono", monospace';
    ctx.fillText(`SPOT PRICE: $${spotPrice.toFixed(2)}`, tagX + 8, tagY + 15);
    ctx.fillStyle = '#c5d8db';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillText(`ATM (14D) IV: ${atmIv.toFixed(1)}%`, tagX + 8, tagY + 28);

  }, [rotX, rotY, zoom, generateMesh, computeIV, spotPrice, showStrategyOverlay]);

  // Auto-rotation animation loop
  useEffect(() => {
    let animId: number;
    if (autoRotate && !isDragging) {
      const animate = () => {
        setRotY((prev) => (prev + 0.35) % 360);
        animId = requestAnimationFrame(animate);
      };
      animId = requestAnimationFrame(animate);
    }
    return () => cancelAnimationFrame(animId);
  }, [autoRotate, isDragging]);

  useEffect(() => {
    renderSurface();
  }, [renderSurface]);

  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      if (canvas && canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
        renderSurface();
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [renderSurface]);

  // Mouse drag handlers
  const onMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;
    setRotX((prev) => Math.max(-80, Math.min(80, prev - deltaY * 0.4)));
    setRotY((prev) => (prev + deltaX * 0.4) % 360);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const onMouseUp = () => {
    setIsDragging(false);
  };

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((prev) => Math.max(0.6, Math.min(1.8, prev - e.deltaY * 0.0012)));
  };

  // Camera Presets
  const setPresetView = (type: '3D' | 'SKEW' | 'TERM') => {
    if (type === '3D') {
      setRotX(30);
      setRotY(-35);
      setZoom(1.05);
    } else if (type === 'SKEW') {
      setRotX(5);
      setRotY(0);
      setZoom(1.2);
    } else if (type === 'TERM') {
      setRotX(5);
      setRotY(-90);
      setZoom(1.2);
    }
  };

  return (
    <div className="relative w-full h-full overflow-hidden flex flex-col">
      {/* 3D Canvas Viewport */}
      <canvas
        ref={canvasRef}
        className={`w-full h-full ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onWheel={onWheel}
      />

      {/* Top Explanation Banner (Plain-English Quant Guide) */}
      <div className="absolute top-4 left-4 max-w-lg bg-surface/90 backdrop-blur-md border border-outline-variant/30 p-3 rounded-sm font-mono text-[11px] shadow-xl pointer-events-none">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full bg-primary" />
          <span className="font-bold text-primary tracking-wider uppercase">How to Read the 3D Surface</span>
        </div>
        <p className="text-on-surface-variant leading-relaxed text-[10px]">
          The 3D landscape plots option pricing volatility across all strikes and expirations. 
          <strong className="text-error"> Red mountain peaks</strong> show elevated &quot;crash insurance&quot; put premiums. 
          VOLTRON harvests the edge by selling elevated peaks and buying defined-risk wings.
        </p>
      </div>

      {/* Camera Presets & HUD Controls */}
      <div className="absolute bottom-4 left-4 flex flex-wrap items-center gap-2 bg-surface/90 backdrop-blur-md border border-outline-variant/30 p-2 rounded-sm font-mono text-[11px] shadow-lg">
        <span className="text-outline text-[10px] uppercase font-bold mr-1">Camera Views:</span>
        <button
          type="button"
          onClick={() => setPresetView('3D')}
          className="px-2.5 py-1 bg-surface-container-high hover:bg-surface-variant text-on-surface border border-outline-variant/40 rounded text-[10px] uppercase transition-colors"
        >
          Perspective 3D
        </button>
        <button
          type="button"
          onClick={() => setPresetView('SKEW')}
          className="px-2.5 py-1 bg-surface-container-high hover:bg-surface-variant text-error border border-outline-variant/40 rounded text-[10px] uppercase transition-colors"
        >
          Front (Put Skew Smile)
        </button>
        <button
          type="button"
          onClick={() => setPresetView('TERM')}
          className="px-2.5 py-1 bg-surface-container-high hover:bg-surface-variant text-[#cdbdff] border border-outline-variant/40 rounded text-[10px] uppercase transition-colors"
        >
          Side (DTE Term Structure)
        </button>

        <div className="h-4 w-px bg-outline-variant mx-1" />

        <button
          type="button"
          onClick={() => setShowStrategyOverlay((prev) => !prev)}
          className={`px-2.5 py-1 rounded text-[10px] uppercase font-bold border transition-colors ${
            showStrategyOverlay
              ? 'bg-primary/20 text-primary border-primary/50'
              : 'bg-surface-container-high text-on-surface-variant border-outline-variant/40'
          }`}
        >
          {showStrategyOverlay ? '✓ Strategy Wings: ON' : 'Strategy Wings: OFF'}
        </button>

        <button
          type="button"
          onClick={() => setAutoRotate((prev) => !prev)}
          className={`px-2.5 py-1 rounded text-[10px] uppercase font-bold border transition-colors ${
            autoRotate
              ? 'bg-primary text-on-primary border-primary'
              : 'bg-surface-container-high text-on-surface-variant hover:text-primary border-outline-variant/40'
          }`}
        >
          {autoRotate ? 'Auto-Orbit: ON' : 'Auto-Orbit'}
        </button>
      </div>

      {/* Visual Color Legend */}
      <div className="absolute top-4 right-4 bg-surface/85 backdrop-blur-md border border-outline-variant/30 p-2.5 rounded-sm font-mono text-[10px] flex flex-col gap-1.5 shadow-lg">
        <span className="text-outline uppercase font-bold tracking-wider mb-0.5">Implied Volatility (IV)</span>
        <div className="flex items-center gap-2">
          <div className="w-3 h-2 rounded-xs bg-[#ff5050]" />
          <span className="text-error font-semibold">Elevated Put Skew (&gt; 28% IV)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-2 rounded-xs bg-[#fec931]" />
          <span className="text-[#fec931]">Mid Volatility Zone (20–28%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-2 rounded-xs bg-[#00e5ff]" />
          <span className="text-primary">Baseline ATM Volatility (&lt; 20%)</span>
        </div>
      </div>
    </div>
  );
};
