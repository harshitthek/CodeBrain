import React, { useEffect, useRef } from 'react';
import { lenisInstance } from '../utils/smoothScroll';

interface Particle {
  x: number;
  y: number;
  z: number;
  baseX: number;
  baseY: number;
  baseZ: number;
  vx: number;
  vy: number;
  vz: number;
  size: number;
  color: string;
  angle: number;
  rotSpeed: number;
  isAmbient: boolean;
  alpha: number;
}

const CHROMATIC_PALETTE = [
  '#8052ff', // Electric Iris (violet)
  '#ffb829', // Saffron Spark (amber)
  '#15846e', // Deep Verdant (teal)
  '#ec4899', // Vivid Magenta
  '#38bdf8', // Neon Sky Blue
  '#a855f7', // Vivid Purple
];

export const ConstellationCanvas: React.FC<{ className?: string }> = ({ className = '' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = 600;
    let height = 600;

    const setupCanvasResolution = () => {
      const parent = canvas.parentElement;
      if (!parent) return;

      const dpr = window.devicePixelRatio || 1;
      width = parent.clientWidth || 600;
      height = parent.clientHeight || 600;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.scale(dpr, dpr);
    };

    setupCanvasResolution();

    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      targetMouseX = e.clientX - rect.left - width / 2;
      targetMouseY = e.clientY - rect.top - height / 2;
    };

    const handleMouseLeave = () => {
      targetMouseX = 0;
      targetMouseY = 0;
    };

    window.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    const particles: Particle[] = [];
    const TOTAL_BRAIN_PARTICLES = 1850;
    const TOTAL_AMBIENT_PARTICLES = 190;

    // Generate grand spherical 3D brain shape with dual hemispheres
    const generateBrainCoordinates = (index: number) => {
      const hemisphere = index % 2 === 0 ? 1 : -1;
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2 * Math.PI;
      const phi = Math.acos(2 * v - 1);

      // Grand volumetric brain radii with sulci/gyri modulation
      const radiusX = 250 + 25 * Math.sin(phi * 4) * Math.cos(theta * 3);
      const radiusY = 220 + 30 * Math.cos(phi * 3);
      const radiusZ = 240 + 25 * Math.sin(theta * 5);

      const separation = 36 * hemisphere;

      let x = Math.sin(phi) * Math.cos(theta) * radiusX * 0.86 + separation;
      let y = Math.cos(phi) * radiusY * 0.95;
      let z = Math.sin(phi) * Math.sin(theta) * radiusZ * 0.88;

      const internalScatter = 0.8 + Math.random() * 0.28;
      x *= internalScatter;
      y *= internalScatter;
      z *= internalScatter;

      return { x, y, z };
    };

    const initParticles = () => {
      particles.length = 0;

      // 1. Brain constellation particles
      for (let i = 0; i < TOTAL_BRAIN_PARTICLES; i++) {
        const coords = generateBrainCoordinates(i);
        const color = CHROMATIC_PALETTE[Math.floor(Math.random() * CHROMATIC_PALETTE.length)];
        const size = Math.random() < 0.25 ? 3.6 : Math.random() < 0.65 ? 2.6 : 1.9;

        particles.push({
          x: coords.x,
          y: coords.y,
          z: coords.z,
          baseX: coords.x,
          baseY: coords.y,
          baseZ: coords.z,
          vx: (Math.random() - 0.5) * 0.35,
          vy: (Math.random() - 0.5) * 0.35,
          vz: (Math.random() - 0.5) * 0.35,
          size,
          color,
          angle: Math.random() * Math.PI * 2,
          rotSpeed: (Math.random() - 0.5) * 0.04,
          isAmbient: false,
          alpha: 0.65 + Math.random() * 0.35,
        });
      }

      // 2. Ambient drifting particles in surrounding void
      for (let i = 0; i < TOTAL_AMBIENT_PARTICLES; i++) {
        const spreadX = (Math.random() - 0.5) * (width * 1.3);
        const spreadY = (Math.random() - 0.5) * (height * 1.3);
        const spreadZ = (Math.random() - 0.5) * 450;
        const color = CHROMATIC_PALETTE[Math.floor(Math.random() * CHROMATIC_PALETTE.length)];

        particles.push({
          x: spreadX,
          y: spreadY,
          z: spreadZ,
          baseX: spreadX,
          baseY: spreadY,
          baseZ: spreadZ,
          vx: (Math.random() - 0.5) * 0.2,
          vy: (Math.random() - 0.5) * 0.2,
          vz: (Math.random() - 0.5) * 0.2,
          size: 1.6 + Math.random() * 1.6,
          color,
          angle: Math.random() * Math.PI * 2,
          rotSpeed: (Math.random() - 0.5) * 0.02,
          isAmbient: true,
          alpha: 0.15 + Math.random() * 0.3,
        });
      }
    };

    initParticles();

    const handleResize = () => {
      setupCanvasResolution();
      initParticles();
    };

    window.addEventListener('resize', handleResize);

    let rotationY = 0;
    let rotationX = 0.15;
    const fov = 580;

    const drawTriangle = (
      px: number,
      py: number,
      size: number,
      angle: number,
      color: string,
      alpha: number
    ) => {
      ctx.save();
      ctx.translate(px, py);
      ctx.rotate(angle);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.15;
      ctx.globalAlpha = Math.max(0.08, Math.min(1, alpha));

      ctx.beginPath();
      const h = size * 1.3;
      ctx.moveTo(0, -h * 0.66);
      ctx.lineTo(size * 0.86, h * 0.33);
      ctx.lineTo(-size * 0.86, h * 0.33);
      ctx.closePath();
      ctx.stroke();

      if (size > 2.7) {
        ctx.fillStyle = color;
        ctx.globalAlpha = alpha * 0.6;
        ctx.beginPath();
        ctx.arc(0, 0, 0.8, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    };

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Smooth mouse interpolation
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Lenis scroll velocity coupling
      const scrollVelocity = lenisInstance?.velocity || 0;
      const velocityTilt = Math.max(-0.35, Math.min(0.35, scrollVelocity * 0.012));

      rotationY += 0.0035 + (mouseX / width) * 0.004;
      rotationX = 0.14 + (mouseY / height) * 0.12 + velocityTilt;

      const cosY = Math.cos(rotationY);
      const sinY = Math.sin(rotationY);
      const cosX = Math.cos(rotationX);
      const sinX = Math.sin(rotationX);

      const centerX = width / 2;
      const centerY = height / 2;

      const projected = [];

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        p.baseX += p.vx;
        p.baseY += p.vy;
        p.baseZ += p.vz;
        p.angle += p.rotSpeed;

        if (!p.isAmbient) {
          const distSq = p.baseX * p.baseX + p.baseY * p.baseY + p.baseZ * p.baseZ;
          if (distSq > 380 * 380) {
            p.vx *= -1;
            p.vy *= -1;
            p.vz *= -1;
          }
        }

        let x1 = p.baseX * cosY - p.baseZ * sinY;
        let z1 = p.baseZ * cosY + p.baseX * sinY;

        let y2 = p.baseY * cosX - z1 * sinX;
        let z2 = z1 * cosX + p.baseY * sinX;

        const depth = fov / (fov + z2 + 280);
        const projX = centerX + x1 * depth;
        const projY = centerY + y2 * depth;

        const depthAlpha = p.isAmbient
          ? p.alpha
          : Math.max(0.18, Math.min(1, ((z2 + 320) / 640) * p.alpha));

        projected.push({
          x: projX,
          y: projY,
          z: z2,
          size: p.size * depth * 1.15,
          angle: p.angle,
          color: p.color,
          alpha: depthAlpha,
        });
      }

      projected.sort((a, b) => a.z - b.z);

      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        if (p.x >= -30 && p.x <= width + 30 && p.y >= -30 && p.y <= height + 30) {
          drawTriangle(p.x, p.y, p.size, p.angle, p.color, p.alpha);
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <div className={`relative w-full h-[540px] md:h-[620px] lg:h-[680px] flex items-center justify-center overflow-hidden ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-crosshair block"
        style={{ background: 'transparent' }}
      />
    </div>
  );
};
