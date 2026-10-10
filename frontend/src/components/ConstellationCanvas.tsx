import React, { useEffect, useRef } from 'react';

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
    let width = (canvas.width = canvas.parentElement?.clientWidth || 600);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 600);

    const handleResize = () => {
      if (!canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
      initParticles();
    };

    window.addEventListener('resize', handleResize);

    // Mouse coordinates relative to canvas center
    let mouseX = 0;
    let mouseY = 0;
    let targetMouseX = 0;
    let targetMouseY = 0;
    let isHovered = false;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      targetMouseX = e.clientX - rect.left - width / 2;
      targetMouseY = e.clientY - rect.top - height / 2;
      isHovered = true;
    };

    const handleMouseLeave = () => {
      targetMouseX = 0;
      targetMouseY = 0;
      isHovered = false;
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    const particles: Particle[] = [];
    const TOTAL_BRAIN_PARTICLES = 1400;
    const TOTAL_AMBIENT_PARTICLES = 160;

    // Generate mathematical 3D brain shape with dual hemispheres
    const generateBrainCoordinates = (index: number, total: number) => {
      // Split into left and right hemispheres
      const hemisphere = index % 2 === 0 ? 1 : -1;
      const u = Math.random();
      const v = Math.random();
      const theta = u * 2 * Math.PI;
      const phi = Math.acos(2 * v - 1);

      // Parametric brain ellipsoid with cranial curvature and sulci/gyri modulation
      const radiusX = 140 + 15 * Math.sin(phi * 4) * Math.cos(theta * 3);
      const radiusY = 110 + 20 * Math.cos(phi * 3);
      const radiusZ = 160 + 15 * Math.sin(theta * 5);

      // Separation between hemispheres
      const separation = 28 * hemisphere;

      let x = (Math.sin(phi) * Math.cos(theta) * radiusX * 0.72) + separation;
      let y = (Math.cos(phi) * radiusY * 0.85);
      let z = (Math.sin(phi) * Math.sin(theta) * radiusZ * 0.85);

      // Flatten bottom slightly for temporal lobes
      if (y > 30) {
        y *= 0.8;
      }
      // Add frontal lobe projection
      if (z > 40) {
        x *= 0.92;
        y *= 0.95;
      }

      return { x, y, z };
    };

    const initParticles = () => {
      particles.length = 0;

      // Brain particles
      for (let i = 0; i < TOTAL_BRAIN_PARTICLES; i++) {
        const coords = generateBrainCoordinates(i, TOTAL_BRAIN_PARTICLES);
        const color = CHROMATIC_PALETTE[Math.floor(Math.random() * CHROMATIC_PALETTE.length)];
        particles.push({
          x: coords.x,
          y: coords.y,
          z: coords.z,
          baseX: coords.x,
          baseY: coords.y,
          baseZ: coords.z,
          vx: (Math.random() - 0.5) * 0.3,
          vy: (Math.random() - 0.5) * 0.3,
          vz: (Math.random() - 0.5) * 0.3,
          size: 2.2 + Math.random() * 2.8,
          color,
          angle: Math.random() * Math.PI * 2,
          rotSpeed: (Math.random() - 0.5) * 0.04,
          isAmbient: false,
          alpha: 0.65 + Math.random() * 0.35,
        });
      }

      // Ambient drifting particles in void
      for (let i = 0; i < TOTAL_AMBIENT_PARTICLES; i++) {
        const ambientSpreadX = (Math.random() - 0.5) * width * 1.1;
        const ambientSpreadY = (Math.random() - 0.5) * height * 1.1;
        const ambientSpreadZ = (Math.random() - 0.5) * 400;
        const color = CHROMATIC_PALETTE[Math.floor(Math.random() * CHROMATIC_PALETTE.length)];
        particles.push({
          x: ambientSpreadX,
          y: ambientSpreadY,
          z: ambientSpreadZ,
          baseX: ambientSpreadX,
          baseY: ambientSpreadY,
          baseZ: ambientSpreadZ,
          vx: (Math.random() - 0.5) * 0.2,
          vy: (Math.random() - 0.5) * 0.2,
          vz: (Math.random() - 0.5) * 0.2,
          size: 2.0 + Math.random() * 2.0,
          color,
          angle: Math.random() * Math.PI * 2,
          rotSpeed: (Math.random() - 0.5) * 0.02,
          isAmbient: true,
          alpha: 0.25 + Math.random() * 0.25,
        });
      }
    };

    initParticles();

    // Helper: Draw tiny outlined equilateral triangle
    const drawOutlinedTriangle = (
      context: CanvasRenderingContext2D,
      cx: number,
      cy: number,
      size: number,
      angle: number,
      color: string,
      alpha: number
    ) => {
      context.save();
      context.translate(cx, cy);
      context.rotate(angle);
      context.beginPath();

      const r = size;
      const angleStep = (Math.PI * 2) / 3;
      // Equilateral triangle vertices
      for (let i = 0; i < 3; i++) {
        const a = i * angleStep - Math.PI / 2;
        const px = r * Math.cos(a);
        const py = r * Math.sin(a);
        if (i === 0) context.moveTo(px, py);
        else context.lineTo(px, py);
      }
      context.closePath();

      context.strokeStyle = color;
      context.lineWidth = 1.2;
      context.globalAlpha = Math.max(0.05, Math.min(1, alpha));
      context.stroke();
      context.restore();
    };

    let rotationAngleY = 0;
    let rotationAngleX = 0;
    let pulseTime = 0;

    const render = () => {
      pulseTime += 0.015;

      // Smooth mouse follow
      mouseX += (targetMouseX - mouseX) * 0.05;
      mouseY += (targetMouseY - mouseY) * 0.05;

      // Base rotation with gentle mouse tilt
      rotationAngleY += 0.0035;
      rotationAngleX = Math.sin(pulseTime * 0.5) * 0.08 + (mouseY / height) * 0.25;
      const dynamicRotY = rotationAngleY + (mouseX / width) * 0.45;

      // Clear with pure void
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, width, height);

      const cosY = Math.cos(dynamicRotY);
      const sinY = Math.sin(dynamicRotY);
      const cosX = Math.cos(rotationAngleX);
      const sinX = Math.sin(rotationAngleX);

      const fov = 420;
      const centerX = width / 2;
      const centerY = height / 2;

      // Transform and sort particles by depth for correct rendering
      const projected = [];

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Dynamic organic breathing oscillation
        p.angle += p.rotSpeed;

        let curX = p.baseX;
        let curY = p.baseY;
        let curZ = p.baseZ;

        if (!p.isAmbient) {
          const breathing = 1 + Math.sin(pulseTime * 2 + p.baseZ * 0.02) * 0.035;
          curX *= breathing;
          curY *= breathing;
          curZ *= breathing;

          // Interactive mouse repelling wave
          if (isHovered) {
            const dx = curX - mouseX;
            const dy = curY - mouseY;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 120 && dist > 1) {
              const force = (120 - dist) / 120;
              curX += (dx / dist) * force * 18;
              curY += (dy / dist) * force * 18;
            }
          }
        } else {
          // Drift ambient particles
          p.baseX += p.vx;
          p.baseY += p.vy;
          if (Math.abs(p.baseX) > width * 0.6) p.vx *= -1;
          if (Math.abs(p.baseY) > height * 0.6) p.vy *= -1;
        }

        // 3D rotation Y
        let x1 = curX * cosY - curZ * sinY;
        let z1 = curZ * cosY + curX * sinY;

        // 3D rotation X
        let y2 = curY * cosX - z1 * sinX;
        let z2 = z1 * cosX + curY * sinX;

        // Perspective projection
        const depth = z2 + 380;
        if (depth > 10) {
          const scale = fov / depth;
          const screenX = centerX + x1 * scale;
          const screenY = centerY + y2 * scale;
          const renderedSize = Math.max(1, p.size * scale);
          const depthAlpha = p.alpha * Math.min(1, Math.max(0.1, (depth / 420)));

          projected.push({
            p,
            screenX,
            screenY,
            z: z2,
            size: renderedSize,
            color: p.color,
            angle: p.angle,
            alpha: depthAlpha,
          });
        }
      }

      // Sort back-to-front
      projected.sort((a, b) => a.z - b.z);

      // Render subtle synaptic connection lines between close brain nodes
      ctx.lineWidth = 0.5;
      for (let i = 0; i < projected.length; i += 7) {
        const p1 = projected[i];
        if (p1.p.isAmbient) continue;

        for (let j = i + 1; j < Math.min(i + 14, projected.length); j += 2) {
          const p2 = projected[j];
          if (p2.p.isAmbient) continue;

          const dx = p1.screenX - p2.screenX;
          const dy = p1.screenY - p2.screenY;
          const distSq = dx * dx + dy * dy;

          if (distSq < 1600) {
            const lineAlpha = (1 - Math.sqrt(distSq) / 40) * 0.22;
            ctx.beginPath();
            ctx.moveTo(p1.screenX, p1.screenY);
            ctx.lineTo(p2.screenX, p2.screenY);
            ctx.strokeStyle = p1.color;
            ctx.globalAlpha = lineAlpha;
            ctx.stroke();
          }
        }
      }

      // Render all triangular particles
      for (let i = 0; i < projected.length; i++) {
        const item = projected[i];
        drawOutlinedTriangle(
          ctx,
          item.screenX,
          item.screenY,
          item.size,
          item.angle,
          item.color,
          item.alpha
        );
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <div className={`relative w-full h-[520px] md:h-[620px] lg:h-[700px] flex items-center justify-center overflow-hidden ${className}`}>
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-crosshair block"
        style={{ background: '#000000' }}
      />
    </div>
  );
};
