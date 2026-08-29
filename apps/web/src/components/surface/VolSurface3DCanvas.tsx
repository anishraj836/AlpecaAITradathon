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
}

export const VolSurface3DCanvas: React.FC<VolSurface3DCanvasProps> = ({ surfaceData }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Rotation angles in degrees
  const [rotX, setRotX] = useState<number>(32);
  const [rotY, setRotY] = useState<number>(-38);
  const [zoom, setZoom] = useState<number>(1.0);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const [hoveredPoint, setHoveredPoint] = useState<{ strike: number; dte: number; iv: number; screenX: number; screenY: number } | null>(null);

  // Grid Resolution
  const numStrikes = 16;
  const numDtes = 12;
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
    const skewFactor = moneyness < 0 ? Math.pow(moneyness * 100, 2) * 0.08 - moneyness * 32 : Math.pow(moneyness * 100, 2) * 0.04;
    const baseIV = 18.2 + termFactor + skewFactor;
    return Math.max(12.0, Math.min(42.0, baseIV));
  }, [spotPrice]);

  // Generate 3D grid vertices
  const generateMesh = useCallback(() => {
    const grid: Point3D[][] = [];

    for (let i = 0; i < numStrikes; i++) {
      grid[i] = [];
      const strike = minStrike + (i / (numStrikes - 1)) * (maxStrike - minStrike);
      // Center strike around 0: [-150, 150]
      const x = ((strike - minStrike) / (maxStrike - minStrike) - 0.5) * 320;

      for (let j = 0; j < numDtes; j++) {
        const dte = minDte + (j / (numDtes - 1)) * (maxDte - minDte);
        // Center DTE around 0: [-150, 150]
        const y = ((dte - minDte) / (maxDte - minDte) - 0.5) * 300;

        const iv = computeIV(strike, dte);
        // Scale IV to Z-height: [0, 120]
        const z = (iv - 14.0) * 4.2;

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
    const centerY = height / 2;

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
      const cameraDistance = 650;
      const fov = 500 * zoom;
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
        quads.push({ p1, p2, p3, p4, avgZ, avgIv });
      }
    }

    // Sort quads from back to front (painter's algorithm)
    quads.sort((a, b) => {
      const projA = project({ x: (a.p1.x + a.p3.x) / 2, y: (a.p1.y + a.p3.y) / 2, z: a.avgZ, strike: 0, dte: 0, iv: a.avgIv });
      const projB = project({ x: (b.p1.x + b.p3.x) / 2, y: (b.p1.y + b.p3.y) / 2, z: b.avgZ, strike: 0, dte: 0, iv: b.avgIv });
      return projA.depth - projB.depth;
    });

    // 1. Draw 3D Base Reference Grid
    ctx.strokeStyle = 'rgba(59, 73, 76, 0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = -160; i <= 160; i += 40) {
      const start = project({ x: i, y: -150, z: 0, strike: 0, dte: 0, iv: 0 });
      const end = project({ x: i, y: 150, z: 0, strike: 0, dte: 0, iv: 0 });
      ctx.moveTo(start.screenX, start.screenY);
      ctx.lineTo(end.screenX, end.screenY);
    }
    for (let j = -150; j <= 150; j += 30) {
      const start = project({ x: -160, y: j, z: 0, strike: 0, dte: 0, iv: 0 });
      const end = project({ x: 160, y: j, z: 0, strike: 0, dte: 0, iv: 0 });
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
      let fillColor = 'rgba(0, 229, 255, 0.25)';
      let strokeColor = 'rgba(0, 229, 255, 0.6)';

      if (normIv > 0.6) {
        fillColor = 'rgba(255, 80, 80, 0.35)'; // High Put Skew Spike
        strokeColor = 'rgba(255, 100, 100, 0.8)';
      } else if (normIv > 0.3) {
        fillColor = 'rgba(254, 201, 49, 0.3)'; // Elevated Vol Zone
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

    // 3. Draw 3D Coordinates Axes & Labels
    // Strike Axis (X)
    const origin = project({ x: -160, y: -150, z: 0, strike: 0, dte: 0, iv: 0 });
    const xEnd = project({ x: 180, y: -150, z: 0, strike: 0, dte: 0, iv: 0 });
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
    const yEnd = project({ x: -160, y: 170, z: 0, strike: 0, dte: 0, iv: 0 });
    ctx.strokeStyle = '#cdbdff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.screenX, origin.screenY);
    ctx.lineTo(yEnd.screenX, yEnd.screenY);
    ctx.stroke();

    ctx.fillStyle = '#cdbdff';
    ctx.fillText('DTE (Days) →', yEnd.screenX - 20, yEnd.screenY + 16);

    // IV Height Axis (Z)
    const zEnd = project({ x: -160, y: -150, z: 120, strike: 0, dte: 0, iv: 0 });
    ctx.strokeStyle = '#fec931';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(origin.screenX, origin.screenY);
    ctx.lineTo(zEnd.screenX, zEnd.screenY);
    ctx.stroke();

    ctx.fillStyle = '#fec931';
    ctx.fillText('↑ IV (%)', zEnd.screenX - 35, zEnd.screenY - 8);

    // 4. Draw ATM Focal Node in True 3D Space ($645.31 spot, 14 DTE)
    const atmX = ((spotPrice - minStrike) / (maxStrike - minStrike) - 0.5) * 320;
    const atmY = ((14 - minDte) / (maxDte - minDte) - 0.5) * 300;
    const atmIv = computeIV(spotPrice, 14);
    const atmZ = (atmIv - 14.0) * 4.2;

    const atmProj = project({ x: atmX, y: atmY, z: atmZ, strike: spotPrice, dte: 14, iv: atmIv });

    // Dropdown shadow line to 3D base
    const atmBase = project({ x: atmX, y: atmY, z: 0, strike: spotPrice, dte: 14, iv: 0 });
    ctx.strokeStyle = 'rgba(0, 229, 255, 0.7)';
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(atmProj.screenX, atmProj.screenY);
    ctx.lineTo(atmBase.screenX, atmBase.screenY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Glowing 3D ATM sphere node
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
    ctx.fillStyle = 'rgba(10, 16, 18, 0.85)';
    ctx.strokeStyle = '#00e5ff';
    ctx.lineWidth = 1;
    const tagWidth = 140;
    const tagHeight = 36;
    const tagX = atmProj.screenX + 14;
    const tagY = atmProj.screenY - 20;

    ctx.fillRect(tagX, tagY, tagWidth, tagHeight);
    ctx.strokeRect(tagX, tagY, tagWidth, tagHeight);

    ctx.fillStyle = '#00e5ff';
    ctx.font = 'bold 11px "JetBrains Mono", monospace';
    ctx.fillText(`ATM: $${spotPrice.toFixed(2)}`, tagX + 8, tagY + 15);
    ctx.fillStyle = '#c5d8db';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillText(`14D IV: ${atmIv.toFixed(1)}%`, tagX + 8, tagY + 28);

  }, [rotX, rotY, zoom, generateMesh, computeIV, spotPrice]);

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

  // Redraw when angle/zoom/data changes
  useEffect(() => {
    renderSurface();
  }, [renderSurface]);

  // Handle Resize
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

  const resetView = () => {
    setRotX(32);
    setRotY(-38);
    setZoom(1.0);
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

      {/* Floating 3D HUD Controls */}
      <div className="absolute bottom-4 left-4 flex items-center gap-2 bg-surface/90 backdrop-blur-md border border-outline-variant/30 px-3 py-1.5 rounded-sm font-mono text-[11px] shadow-lg">
        <span className="text-outline">
          Pitch: <strong className="text-on-surface">{rotX.toFixed(0)}°</strong> | Yaw: <strong className="text-on-surface">{rotY.toFixed(0)}°</strong> | Zoom: <strong className="text-on-surface">{zoom.toFixed(2)}x</strong>
        </span>
        <div className="h-3 w-px bg-outline-variant mx-1" />
        <button
          type="button"
          onClick={() => setAutoRotate((prev) => !prev)}
          className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border transition-colors ${
            autoRotate
              ? 'bg-primary text-on-primary border-primary'
              : 'bg-surface-container-high text-on-surface-variant hover:text-primary border-outline-variant/40'
          }`}
        >
          {autoRotate ? 'Auto-Orbit: ON' : 'Auto-Orbit'}
        </button>
        <button
          type="button"
          onClick={resetView}
          className="px-2 py-0.5 bg-surface-container-high hover:bg-surface-variant text-on-surface-variant hover:text-on-surface rounded text-[10px] uppercase border border-outline-variant/40 transition-colors"
        >
          Reset
        </button>
      </div>

      {/* Quick Legend Overlay */}
      <div className="absolute top-4 right-4 bg-surface/85 backdrop-blur-md border border-outline-variant/30 p-2.5 rounded-sm font-mono text-[10px] flex flex-col gap-1.5 shadow-lg">
        <span className="text-outline uppercase font-bold tracking-wider mb-0.5">Surface Height (IV)</span>
        <div className="flex items-center gap-2">
          <div className="w-3 h-2 rounded-xs bg-[#ff5050]" />
          <span className="text-error font-semibold">Elevated Put Skew (&gt; 28%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-2 rounded-xs bg-[#fec931]" />
          <span className="text-[#fec931]">Mid Vol Range (20-28%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-2 rounded-xs bg-[#00e5ff]" />
          <span className="text-primary">Low Baseline IV (&lt; 20%)</span>
        </div>
      </div>
    </div>
  );
};
