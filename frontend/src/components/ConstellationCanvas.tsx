import React, { useEffect, useRef, useState } from 'react';

type GlyphKind = 'dot' | 'cross' | 'ring' | 'bit0' | 'bit1';

interface BrainParticle {
  // 3D target coordinates in brain space
  tx: number;
  ty: number;
  tz: number;
  // Outward 3D surface normal (for crisp 3D front/back lighting & shading)
  nx: number;
  ny: number;
  nz: number;
  // Initial 2D scattered grid position (snapped to 6px pitch across full screen)
  scatterX: number;
  scatterY: number;
  // Interactive spring offset & velocity
  ox: number;
  oy: number;
  vx: number;
  vy: number;
  // Visual & structural metadata
  size: number;
  kind: GlyphKind;
  isSignal: boolean;
  isHub: boolean;
  hemisphere: -1 | 1 | 0;
  stagger: number;
  driftPhase: number;
  calloutLabel?: string;
}

interface NeuralEdge {
  a: number;
  b: number;
  isBridge: boolean;
}

interface NerveTract {
  /** Ordered particle indices forming a continuous 3D nerve / arterial vessel */
  indices: number[];
  isMainArtery: boolean;
}

interface CirculatingCorpuscle {
  tractIdx: number;
  /** 0..1 position along the nerve tract */
  progress: number;
  /** Smooth steady circulation speed */
  speed: number;
  /** Radius of the red mini-circle */
  radius: number;
}

interface ConstellationCanvasProps {
  className?: string;
  onPhaseChange?: (phase: 'SCATTERED' | 'CONVERGING' | 'ORBITING') => void;
}

const HUB_CALLOUTS: Array<{
  label: string;
  hemi: -1 | 1;
  u: number; // 0..1 anterior-posterior
  v: number; // 0..1 dorsal-ventral
}> = [
  { label: 'ACTOR::GEN_SUITE()', hemi: -1, u: 0.24, v: 0.36 },
  { label: 'PYDANTIC_V2::VALID', hemi: -1, u: 0.52, v: 0.22 },
  { label: 'HYBRID_RRF[k=60]', hemi: -1, u: 0.76, v: 0.48 },
  { label: 'CRITIC::RUBRIC(93.5)', hemi: 1, u: 0.28, v: 0.34 },
  { label: 'HTTPX::DNS_PINNED', hemi: 1, u: 0.56, v: 0.26 },
  { label: 'SSRF_GUARD::403', hemi: 1, u: 0.78, v: 0.46 },
];

export const ConstellationCanvas: React.FC<ConstellationCanvasProps> = ({
  className = '',
  onPhaseChange,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const assemblyProgressRef = useRef<number>(0);
  const triggerTimeRef = useRef<number | null>(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId = 0;
    let width = 1200;
    let height = 900;
    let stageW = 1000;
    let stageH = 460;
    const STAGE_TOP_OFFSET = 36;
    let dpr = 1;

    const particles: BrainParticle[] = [];
    const edges: NeuralEdge[] = [];
    const nerveTracts: NerveTract[] = [];
    const corpuscles: CirculatingCorpuscle[] = [];
    const calloutIndices: number[] = [];
    const GRID_PITCH = 6;

    const startTime = performance.now();

    if (prefersReducedMotion) {
      assemblyProgressRef.current = 1;
      if (triggerTimeRef.current === null) {
        triggerTimeRef.current = startTime;
      }
    } else if ((window.scrollY || 0) > 2 && triggerTimeRef.current === null) {
      triggerTimeRef.current = startTime;
    }

    // Preserve formed state across effect reruns when reduced-motion preference changes
    let triggerTime = triggerTimeRef.current;
    let maxAssemblyProgress = prefersReducedMotion ? 1 : assemblyProgressRef.current;
    let lastReportedPhase: 'SCATTERED' | 'CONVERGING' | 'ORBITING' =
      maxAssemblyProgress >= 0.96
        ? 'ORBITING'
        : maxAssemblyProgress >= 0.08
        ? 'CONVERGING'
        : 'SCATTERED';

    if (prefersReducedMotion || maxAssemblyProgress >= 0.96) {
      onPhaseChange?.('ORBITING');
    }
    let pulseSurgeTime = -999;

    let mouseX = -9999;
    let mouseY = -9999;

    const triggerFormationOnce = () => {
      if (triggerTime === null) {
        triggerTime = performance.now();
        triggerTimeRef.current = triggerTime;
      }
    };

    /**
     * Exact original brain position & scale inside the parent Upper Stage div:
     * (stageW * 0.78, stageH * 0.48), offset by the full-bleed canvas margin.
     */
    const getBrainCenter = () => {
      const stageLeft = (width - stageW) * 0.5;
      if (stageW >= 1024) {
        return {
          cx: stageLeft + stageW * 0.78,
          cy: STAGE_TOP_OFFSET + stageH * 0.48,
          scale: Math.min(1.06, Math.max(0.84, stageW / 1100)),
        };
      }
      return {
        cx: stageLeft + stageW * 0.5,
        cy: STAGE_TOP_OFFSET + stageH * 0.7,
        scale: Math.min(0.88, Math.max(0.68, stageW / 640)),
      };
    };

    const placedVisibleScatters: Array<[number, number]> = [];

    /**
     * Organic Random Scatter across the screen (Poisson-disc dart throwing)
     * Places dots at genuinely random coordinates with varying distances (not equal grid rows/cols),
     * while enforcing a 42px personal-space buffer so they never overlap onto each other.
     */
    const generateScatterPosition = (idx: number) => {
      const scatterH = height - 32;
      const isVisibleScatter = idx % 4 === 0;
      const minDistance = 42;

      let bestX = 24 + Math.random() * (width - 48);
      let bestY = 20 + Math.random() * (scatterH - 40);

      if (isVisibleScatter) {
        let maxMinDist = -1;
        // Try 14 random candidates and pick one that keeps organic random spacing
        for (let attempt = 0; attempt < 14; attempt++) {
          const candX = 24 + Math.random() * (width - 48);
          const candY = 20 + Math.random() * (scatterH - 40);

          let closest = Infinity;
          for (let k = 0; k < placedVisibleScatters.length; k++) {
            const [px, py] = placedVisibleScatters[k];
            const d = Math.hypot(candX - px, candY - py);
            if (d < closest) closest = d;
          }

          if (closest >= minDistance) {
            bestX = candX;
            bestY = candY;
            break;
          }
          if (closest > maxMinDist) {
            maxMinDist = closest;
            bestX = candX;
            bestY = candY;
          }
        }
        placedVisibleScatters.push([bestX, bestY]);
      }

      return {
        scatterX: Math.round(bestX / GRID_PITCH) * GRID_PITCH,
        scatterY: Math.round(bestY / GRID_PITCH) * GRID_PITCH,
      };
    };

    /**
     * Sculpted 3D Dual-Hemisphere Cerebral Surface Evaluator
     */
    const evaluateCorticalPoint = (
      u: number, // 0 (Anterior Frontal Pole) .. 1 (Posterior Occipital Pole)
      v: number, // 0 (Medial Fissure Crown) .. 1 (Ventral Base)
      hemi: -1 | 1
    ) => {
      const theta = u * Math.PI;
      const phi = v * Math.PI;

      const sinTheta = Math.sin(theta);
      const cosTheta = Math.cos(theta);
      const sinPhi = Math.sin(phi);
      const cosPhi = Math.cos(phi);

      let z = cosTheta * 124;

      const beanArch = -14 * Math.sin(theta);
      const temporalDrop =
        v > 0.48 && u > 0.25 && u < 0.72
          ? 24 * Math.sin(((u - 0.25) / 0.47) * Math.PI) * Math.sin(((v - 0.48) / 0.52) * Math.PI)
          : 0;
      const orbitalAndOccipitalTuck =
        v > 0.55 ? -22 * Math.pow(cosTheta, 2) * ((v - 0.55) / 0.45) : 0;

      const verticalRadius = cosPhi >= 0 ? 86 : 58;
      let y =
        -cosPhi * verticalRadius * (0.35 + 0.65 * sinTheta) +
        beanArch +
        temporalDrop +
        orbitalAndOccipitalTuck;

      const anteroposteriorTaper = 0.88 + 0.18 * Math.sin(theta - 0.25);
      const temporalLateralFlare =
        v > 0.42 && v < 0.85 && u > 0.28 && u < 0.72
          ? 1 + 0.22 * Math.sin(((u - 0.28) / 0.44) * Math.PI)
          : 1.0;

      const sylvianCrease =
        Math.abs(v - (0.52 - 0.12 * cosTheta)) < 0.08 && u > 0.22 && u < 0.68
          ? 0.86
          : 1.0;

      const gyralWave =
        5.2 *
        Math.sin(u * Math.PI * 7.5 + Math.sin(v * Math.PI * 3) * 1.4) *
        Math.cos(v * Math.PI * 5.5 - u * Math.PI * 2.5);

      const fissureGap = 10.5 + 3.5 * Math.pow(1 - sinPhi, 1.5);
      const lateralSpan =
        78 * sinTheta * sinPhi * anteroposteriorTaper * temporalLateralFlare * sylvianCrease;

      const x = hemi * (fissureGap + lateralSpan + Math.max(0, sinPhi) * gyralWave);
      y += cosPhi * gyralWave * 0.55;
      z += cosTheta * gyralWave * 0.45;

      const mag = Math.hypot(x, y, z) || 1;
      return {
        x,
        y,
        z,
        nx: x / mag,
        ny: y / mag,
        nz: z / mag,
      };
    };

    const initCodeBrain = () => {
      particles.length = 0;
      edges.length = 0;
      nerveTracts.length = 0;
      corpuscles.length = 0;
      calloutIndices.length = 0;
      placedVisibleScatters.length = 0;

      const { cx, cy } = getBrainCenter();

      const pushParticle = (
        x: number,
        y: number,
        z: number,
        nx: number,
        ny: number,
        nz: number,
        hemisphere: -1 | 1 | 0,
        opts: {
          isSignal?: boolean;
          isHub?: boolean;
          kind?: GlyphKind;
          size?: number;
          calloutLabel?: string;
        } = {}
      ): number => {
        const idx = particles.length;
        const { scatterX, scatterY } = generateScatterPosition(idx);
        const rand = Math.random();
        const kind: GlyphKind =
          opts.kind ??
          (rand < 0.8
            ? 'dot'
            : rand < 0.89
            ? 'cross'
            : rand < 0.94
            ? 'ring'
            : rand < 0.97
            ? 'bit0'
            : 'bit1');

        const isHub = opts.isHub ?? false;
        const isSignal = opts.isSignal ?? (isHub || Math.random() < 0.065);
        const size =
          opts.size ?? (isHub ? 2.4 : isSignal ? 2.05 : rand < 0.38 ? 1.7 : 1.35);

        const distFromCenter = Math.hypot(scatterX - cx, scatterY - cy);
        const maxDist = Math.hypot(width, window.innerHeight || 800) * 0.9;
        const stagger = Math.min(
          0.46,
          (distFromCenter / Math.max(1, maxDist)) * 0.44
        );

        particles.push({
          tx: x,
          ty: y,
          tz: z,
          nx,
          ny,
          nz,
          scatterX,
          scatterY,
          ox: 0,
          oy: 0,
          vx: 0,
          vy: 0,
          size,
          kind,
          isSignal,
          isHub,
          hemisphere,
          stagger,
          driftPhase: Math.random() * Math.PI * 2,
          calloutLabel: opts.calloutLabel,
        });
        return idx;
      };

      // =====================================================================
      // 1. LEFT & RIGHT CEREBRAL HEMISPHERES + CONTINUOUS CORTICAL NERVE TRACTS
      // =====================================================================
      for (const hemi of [-1, 1] as const) {
        const numBands = 13;
        const ptsPerBand = 22;
        const bandGrid: number[][] = [];

        for (let b = 0; b < numBands; b++) {
          const uBase = 0.06 + (b / (numBands - 1)) * 0.88;
          const rowIndices: number[] = [];

          for (let k = 0; k < ptsPerBand; k++) {
            const vBase = 0.06 + (k / (ptsPerBand - 1)) * 0.86;
            const uFold =
              uBase + 0.024 * Math.sin(vBase * Math.PI * 4 + b * 0.9);
            const vFold =
              vBase + 0.02 * Math.cos(uBase * Math.PI * 5 - k * 0.7);

            const pt = evaluateCorticalPoint(
              Math.max(0.03, Math.min(0.97, uFold)),
              Math.max(0.04, Math.min(0.95, vFold)),
              hemi
            );

            const isHubNode = (b + k) % 19 === 0;
            const idx = pushParticle(pt.x, pt.y, pt.z, pt.nx, pt.ny, pt.nz, hemi, {
              isHub: isHubNode,
              isSignal: isHubNode || (b * ptsPerBand + k) % 15 === 0,
              kind: isHubNode ? 'ring' : undefined,
            });
            rowIndices.push(idx);
          }

          bandGrid.push(rowIndices);

          if (b % 2 === 1) {
            nerveTracts.push({
              indices: rowIndices,
              isMainArtery: b === 5 || b === 7,
            });
          }
        }

        // Longitudinal Anterior-to-Posterior cerebral arteries / nerve tracts
        for (const kCol of [4, 9, 14, 18]) {
          const longIndices: number[] = [];
          for (let b = 0; b < numBands; b++) {
            const wobbleK = Math.max(
              0,
              Math.min(ptsPerBand - 1, kCol + Math.round(Math.sin(b * 0.9) * 1.5))
            );
            longIndices.push(bandGrid[b][wobbleK]);
          }
          nerveTracts.push({
            indices: longIndices,
            isMainArtery: true,
          });
        }
      }

      // =====================================================================
      // 2. ASCENDING CAROTID / BASILAR BRAINSTEM-TO-CORTEX ARTERIAL NERVE TRUNKS
      // =====================================================================
      for (const hemi of [-1, 1] as const) {
        const anteriorTrunk: number[] = [];
        const trunkWaypoints: Array<[number, number, number]> = [
          [hemi * 6, 98, -32],
          [hemi * 8, 72, -24],
          [hemi * 11, 46, -14],
          [hemi * 16, 18, 2],
          [hemi * 32, -4, 34],
          [hemi * 54, -28, 64],
          [hemi * 44, -58, 86],
          [hemi * 26, -74, 42],
          [hemi * 36, -64, -18],
          [hemi * 42, -38, -68],
          [hemi * 28, -8, -104],
        ];

        for (let w = 0; w < trunkWaypoints.length; w++) {
          const [wx, wy, wz] = trunkWaypoints[w];
          const mag = Math.hypot(wx, wy, wz) || 1;
          const idx = pushParticle(wx, wy, wz, wx / mag, wy / mag, wz / mag, hemi, {
            isSignal: w % 2 === 0,
            isHub: w === 3 || w === 5,
            kind: w === 3 ? 'ring' : 'dot',
            size: 1.9,
          });
          anteriorTrunk.push(idx);
        }

        nerveTracts.push({
          indices: anteriorTrunk,
          isMainArtery: true,
        });
      }

      // =====================================================================
      // 3. CEREBELLUM (Tucked Posteriorly Under the Occipital Lobes)
      // =====================================================================
      for (const hemi of [-1, 1] as const) {
        const rings = 6;
        for (let r = 0; r < rings; r++) {
          const v = (r / (rings - 1)) * 2 - 1;
          const ringRad = Math.sqrt(Math.max(0.1, 1 - v * v));
          const steps = 12;
          const ringIndices: number[] = [];
          for (let s = 0; s < steps; s++) {
            const ang = (s / steps) * Math.PI;
            const lx = Math.sin(ang) * ringRad;
            const lz = Math.cos(ang) * ringRad;

            const x = hemi * (9 + lx * 48);
            const y = 40 + v * 24;
            const z = -74 + lz * 34;
            const mag = Math.hypot(x, y, z) || 1;

            const idx = pushParticle(x, y, z, x / mag, y / mag, z / mag, hemi, {
              size: 1.45,
              isSignal: r === 2 && s % 4 === 0,
            });
            ringIndices.push(idx);
          }
          if (r === 2 || r === 3) {
            nerveTracts.push({
              indices: ringIndices,
              isMainArtery: false,
            });
          }
        }
      }

      // =====================================================================
      // 4. BRAINSTEM & SPINAL CORD NEURAL BUS (Ventral Core)
      // =====================================================================
      for (let col = 0; col < 8; col++) {
        const ang = (col / 8) * Math.PI * 2;
        const colIndices: number[] = [];
        for (let row = 0; row < 8; row++) {
          const t = row / 7;
          const rad = 14 * (1 - 0.25 * t);
          const x = Math.cos(ang) * rad;
          const y = 46 + t * 52;
          const z = -18 - t * 20 + Math.sin(ang) * (rad * 0.8);
          const idx = pushParticle(x, y, z, Math.cos(ang), 0.2, Math.sin(ang), 0, {
            kind: (row + col) % 3 === 0 ? 'bit1' : (row + col) % 3 === 1 ? 'bit0' : 'dot',
            size: 1.5,
            isSignal: row === 0 || row === 7,
          });
          colIndices.push(idx);
        }
        if (col % 2 === 0) {
          nerveTracts.push({
            indices: colIndices.reverse(),
            isMainArtery: true,
          });
        }
      }

      // =====================================================================
      // 5. ANCHOR 3D FLOATING CODEBRAIN CALLOUT HUBS
      // =====================================================================
      for (const item of HUB_CALLOUTS) {
        const pt = evaluateCorticalPoint(item.u, item.v, item.hemi);
        const idx = pushParticle(
          pt.x * 1.03,
          pt.y * 1.03,
          pt.z * 1.03,
          pt.nx,
          pt.ny,
          pt.nz,
          item.hemi,
          {
            isSignal: true,
            isHub: true,
            kind: 'ring',
            size: 2.6,
            calloutLabel: item.label,
          }
        );
        calloutIndices.push(idx);
      }

      // =====================================================================
      // 6. BUILD 3D DELAUNAY-STYLE K-NEAREST-NEIGHBOR NEURAL PLEXUS MESH
      // =====================================================================
      const edgeSet = new Set<string>();
      const addEdge = (a: number, b: number, isBridge: boolean = false) => {
        const key = a < b ? `${a}:${b}` : `${b}:${a}`;
        if (!edgeSet.has(key)) {
          edgeSet.add(key);
          edges.push({ a, b, isBridge });
        }
      };

      for (let i = 0; i < particles.length; i++) {
        const pA = particles[i];
        let best1 = -1, best2 = -1, best3 = -1;
        let d1 = 26, d2 = 26, d3 = 26;

        for (let j = 0; j < particles.length; j++) {
          if (i === j) continue;
          const pB = particles[j];
          if (pA.hemisphere !== pB.hemisphere) continue;

          const dist = Math.hypot(pA.tx - pB.tx, pA.ty - pB.ty, pA.tz - pB.tz);
          if (dist < d1) {
            d3 = d2; best3 = best2;
            d2 = d1; best2 = best1;
            d1 = dist; best1 = j;
          } else if (dist < d2) {
            d3 = d2; best3 = best2;
            d2 = dist; best2 = j;
          } else if (dist < d3) {
            d3 = dist; best3 = j;
          }
        }

        if (best1 !== -1) addEdge(i, best1);
        if (best2 !== -1) addEdge(i, best2);
        if (best3 !== -1 && pA.isHub) addEdge(i, best3);
      }

      // Add 10 Corpus Callosum cross-fissure bridges connecting Left (Actor) & Right (Critic)
      const leftMedial = particles
        .map((p, idx) => ({ p, idx }))
        .filter(({ p }) => p.hemisphere === -1 && Math.abs(p.tx) < 26 && p.ty < 10);
      const rightMedial = particles
        .map((p, idx) => ({ p, idx }))
        .filter(({ p }) => p.hemisphere === 1 && Math.abs(p.tx) < 26 && p.ty < 10);

      for (let m = 0; m < leftMedial.length; m += Math.max(1, Math.floor(leftMedial.length / 10))) {
        const lNode = leftMedial[m];
        let closestR = -1;
        let minD = 42;
        for (const rNode of rightMedial) {
          const d = Math.hypot(
            lNode.p.tx + rNode.p.tx,
            lNode.p.ty - rNode.p.ty,
            lNode.p.tz - rNode.p.tz
          );
          if (d < minD) {
            minD = d;
            closestR = rNode.idx;
          }
        }
        if (closestR !== -1) {
          addEdge(lNode.idx, closestR, true);
        }
      }

      // =====================================================================
      // 7. INITIALIZE SMOOTH CIRCULATING RED MINI-CIRCLES ("BLOOD CIRCULATION")
      // =====================================================================
      for (let tIdx = 0; tIdx < nerveTracts.length; tIdx++) {
        const tract = nerveTracts[tIdx];
        const count = tract.isMainArtery ? 3 : 2;
        const baseSpeed = (0.14 + (tIdx % 5) * 0.022) * (tIdx % 2 === 0 ? 1 : -1);

        for (let c = 0; c < count; c++) {
          corpuscles.push({
            tractIdx: tIdx,
            progress: (c / count + tIdx * 0.13) % 1,
            speed: baseSpeed,
            radius: tract.isMainArtery ? 2.5 : 2.1,
          });
        }
      }
    };

    const setupResolution = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      stageW = parent.clientWidth || 1000;
      stageH = parent.clientHeight || 460;
      width = Math.max(window.innerWidth || 1200, stageW);
      height = Math.max(window.innerHeight || 900, stageH + STAGE_TOP_OFFSET);

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    setupResolution();
    initCodeBrain();

    const handleResize = () => {
      setupResolution();
      initCodeBrain();
      if (prefersReducedMotion) {
        render(performance.now());
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    };

    const handleClick = (e: MouseEvent) => {
      // Any click anywhere on the screen triggers the brain formation!
      triggerFormationOnce();

      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const { cx, cy } = getBrainCenter();
      if (!prefersReducedMotion && Math.hypot(mx - cx, my - cy) < 220) {
        pulseSurgeTime = performance.now();
      }
    };

    const handleMouseLeave = () => {
      mouseX = -9999;
      mouseY = -9999;
    };

    const handleScrollTrigger = () => {
      if ((window.scrollY || 0) > 1) {
        triggerFormationOnce();
      }
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('scroll', handleScrollTrigger, { passive: true });
    window.addEventListener('wheel', triggerFormationOnce, { passive: true });
    window.addEventListener('touchmove', triggerFormationOnce, { passive: true });
    window.addEventListener('click', handleClick);
    document.addEventListener('mouseleave', handleMouseLeave);

    let rotY = -0.65;
    let rotX = 0.28;
    const FOV = 540;
    let lastFrameTime = performance.now();

    const easeInOutCubic = (t: number): number =>
      t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;

    /**
     * Smoothly interpolates a 2D/3D screen point along a nerve tract at `u` in [0, 1]
     */
    const samplePointOnTract = (
      indices: number[],
      uNorm: number,
      coords: Array<{ x: number; y: number; z: number; tLocal: number }>
    ) => {
      const len = indices.length;
      const u = ((uNorm % 1) + 1) % 1;
      const floatIdx = u * (len - 1);
      const i1 = Math.floor(floatIdx);
      const i0 = Math.max(0, i1 - 1);
      const i2 = Math.min(len - 1, i1 + 1);
      const i3 = Math.min(len - 1, i1 + 2);
      const t = floatIdx - i1;
      const t2 = t * t;
      const t3 = t2 * t;

      const p0 = coords[indices[i0]];
      const p1 = coords[indices[i1]];
      const p2 = coords[indices[i2]];
      const p3 = coords[indices[i3]];

      const x =
        0.5 *
        (2 * p1.x +
          (-p0.x + p2.x) * t +
          (2 * p0.x - 5 * p1.x + 4 * p2.x - p3.x) * t2 +
          (-p0.x + 3 * p1.x - 3 * p2.x + p3.x) * t3);
      const y =
        0.5 *
        (2 * p1.y +
          (-p0.y + p2.y) * t +
          (2 * p0.y - 5 * p1.y + 4 * p2.y - p3.y) * t2 +
          (-p0.y + 3 * p1.y - 3 * p2.y + p3.y) * t3);
      const z = p1.z + (p2.z - p1.z) * t;
      const tLocal = Math.min(p1.tLocal, p2.tLocal);

      return { x, y, z, tLocal };
    };

    /**
     * Draws the Precision Architectural Compass & Telemetry Circle Frame around the 3D Brain
     */
    const drawOuterPrecisionCircle = (
      cx: number,
      cy: number,
      scale: number,
      alpha: number,
      elapsedSec: number
    ) => {
      if (alpha <= 0.02) return;
      ctx.save();

      const outerR = 158 * scale;
      const innerR = 144 * scale;

      // 1. Primary Outer Solid Architectural Circle
      ctx.strokeStyle = '#B8B4AA';
      ctx.lineWidth = 0.9;
      ctx.globalAlpha = alpha * 0.65;
      ctx.beginPath();
      ctx.arc(cx, cy, outerR, 0, Math.PI * 2);
      ctx.stroke();

      // 2. Inner Dashed Calibration Circle
      ctx.strokeStyle = '#C8C4BA';
      ctx.lineWidth = 0.75;
      ctx.globalAlpha = alpha * 0.5;
      ctx.setLineDash([3, 5]);
      ctx.beginPath();
      ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);

      // 3. 72 Precision Degree Ticks around the Circle Perimeter
      for (let i = 0; i < 72; i++) {
        const ang = (i / 72) * Math.PI * 2;
        const isCardinal = i % 18 === 0;
        const isMajor = i % 6 === 0;
        const tickIn = outerR - (isCardinal ? 7 : isMajor ? 4.5 : 2.2);
        const tickOut = outerR + (isCardinal ? 4 : 0);

        ctx.strokeStyle = isCardinal ? '#D95338' : '#87847C';
        ctx.lineWidth = isCardinal ? 1.2 : 0.75;
        ctx.globalAlpha = alpha * (isCardinal ? 0.85 : isMajor ? 0.55 : 0.3);

        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(ang) * tickIn, cy + Math.sin(ang) * tickIn);
        ctx.lineTo(cx + Math.cos(ang) * tickOut, cy + Math.sin(ang) * tickOut);
        ctx.stroke();
      }

      // 4. Slow Counter-Rotating Vermilion Telemetry Arc Brackets on the Outer Circle
      const sweepAngle = prefersReducedMotion ? 0.2 : elapsedSec * 0.25;
      ctx.strokeStyle = '#D95338';
      ctx.lineWidth = 1.6;
      ctx.globalAlpha = alpha * 0.8;

      ctx.beginPath();
      ctx.arc(cx, cy, outerR, sweepAngle, sweepAngle + 0.42);
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(cx, cy, outerR, sweepAngle + Math.PI, sweepAngle + Math.PI + 0.42);
      ctx.stroke();

      // 5. Cardinal Compass Labels on the Circle
      ctx.font = '500 8px "IBM Plex Mono", monospace';
      ctx.fillStyle = '#87847C';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.globalAlpha = alpha * 0.75;
      ctx.fillText('ANT // 000°', cx, cy - outerR - 10);
      ctx.fillText('POST // 180°', cx, cy + outerR + 10);

      ctx.restore();
    };

    let disposed = false;

    const render = (now: number) => {
      if (disposed) return;
      const dt = Math.min(0.05, (now - lastFrameTime) / 1000);
      lastFrameTime = now;

      ctx.clearRect(0, 0, width, height);

      const elapsedSec = (now - startTime) / 1000;
      const scrollY = window.scrollY || 0;

      if (scrollY > 1 && triggerTime === null) {
        triggerTime = now;
        triggerTimeRef.current = now;
      }

      // =====================================================================
      // SCROLL-OR-CLICK TRIGGERED ONE-WAY SILKY-SMOOTH CONVERGENCE
      // =====================================================================
      const timeSinceTrigger =
        triggerTime !== null ? Math.max(0, (now - triggerTime) / 1000) : 0;
      const rawProgress =
        triggerTime !== null ? Math.max(0, Math.min(1, timeSinceTrigger / 1.85)) : 0;
      maxAssemblyProgress = Math.max(maxAssemblyProgress, rawProgress);
      assemblyProgressRef.current = maxAssemblyProgress;

      const currentPhase: 'SCATTERED' | 'CONVERGING' | 'ORBITING' =
        maxAssemblyProgress < 0.08
          ? 'SCATTERED'
          : maxAssemblyProgress < 0.96
          ? 'CONVERGING'
          : 'ORBITING';

      if (currentPhase !== lastReportedPhase) {
        lastReportedPhase = currentPhase;
        onPhaseChange?.(currentPhase);
      }

      const { cx, cy, scale } = getBrainCenter();

      // =====================================================================
      // SMOOTH CONSTANT-VELOCITY 3D TURNTABLE ROTATION (Zero Jugging/Wobble!)
      // =====================================================================
      const mouseTiltY =
        mouseX > 0 && mouseX < width ? ((mouseX - cx) / width) * 0.003 : 0;
      const mouseTiltX =
        mouseY > 0 && mouseY < height ? ((mouseY - cy) / height) * 0.12 : 0;

      if (!prefersReducedMotion) {
        rotY += 0.0032 + mouseTiltY;
        const targetRotX = 0.28 + mouseTiltX;
        rotX += (targetRotX - rotX) * 0.06;
      }

      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);
      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);

      // Draw the Precision Architectural Circle around the 3D Brain
      drawOuterPrecisionCircle(cx, cy, scale, maxAssemblyProgress, elapsedSec);

      const surgeElapsed = (now - pulseSurgeTime) / 1000;
      const isSurging = surgeElapsed >= 0 && surgeElapsed < 1.2;
      const surgeRadius = surgeElapsed * 220;

      const screenCoords: Array<{
        x: number;
        y: number;
        z: number;
        lighting: number;
        size: number;
        kind: GlyphKind;
        isSignal: boolean;
        isHub: boolean;
        nearCursor: boolean;
        inSurge: boolean;
        showInScatter: boolean;
        tLocal: number;
        calloutLabel?: string;
      }> = new Array(particles.length);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        const tRaw = (maxAssemblyProgress - p.stagger) / (1 - p.stagger);
        const tLocal = easeInOutCubic(Math.max(0, Math.min(1, tRaw)));

        const bx = p.tx * scale;
        const by = p.ty * scale;
        const bz = p.tz * scale;

        const x1 = bx * cosY - bz * sinY;
        const z1 = bz * cosY + bx * sinY;
        const y2 = by * cosX - z1 * sinX;
        const z2 = z1 * cosX + by * sinX;

        const nx1 = p.nx * cosY - p.nz * sinY;
        const nz1 = p.nz * cosY + p.nx * sinY;
        const ny2 = p.ny * cosX - nz1 * sinX;
        const nz2 = nz1 * cosX + p.ny * sinX;
        const lighting = Math.max(
          0,
          Math.min(1, (-nx1 * 0.35 - ny2 * 0.45 - nz2 * 0.82 + 0.65) * 0.75)
        );

        const perspective = FOV / (FOV + z2 + 210);
        const targetScreenX = cx + x1 * perspective;
        const targetScreenY = cy + y2 * perspective;

        const arcCurl = Math.sin(tLocal * Math.PI) * 24 * (p.hemisphere || 1);

        // Firmly stationed at (scatterX, scatterY) when tLocal === 0, smoothly sweeping into 3D Brain
        const baseScreenX =
          p.scatterX +
          (targetScreenX - p.scatterX) * tLocal +
          arcCurl * (1 - tLocal);
        const baseScreenY =
          p.scatterY +
          (targetScreenY - p.scatterY) * tLocal -
          Math.sin(tLocal * Math.PI) * 12;

        // Cursor pin-screen displacement physics
        const dx = baseScreenX + p.ox - mouseX;
        const dy = baseScreenY + p.oy - mouseY;
        const distSq = dx * dx + dy * dy;
        const interactionRadius = 64;
        let nearCursor = false;

        if (!prefersReducedMotion && distSq < interactionRadius * interactionRadius && distSq > 0.01) {
          const dist = Math.sqrt(distSq);
          const force = (1 - dist / interactionRadius) * 2.1;
          p.vx += (dx / dist) * force;
          p.vy += (dy / dist) * force;
          nearCursor = dist < 44;
        }

        if (!prefersReducedMotion) {
          p.vx += -p.ox * 0.14;
          p.vy += -p.oy * 0.14;
          p.vx *= 0.78;
          p.vy *= 0.78;
          p.ox += p.vx;
          p.oy += p.vy;
        } else {
          p.ox = 0;
          p.oy = 0;
        }

        const dist3DFromOrigin = Math.hypot(p.tx, p.ty, p.tz);
        const inSurge = isSurging && Math.abs(dist3DFromOrigin - surgeRadius) < 28;

        // Full crisp size when firmly scattered on 2D screen, transitioning to 3D perspective size
        const sizeScale = (1 - tLocal) * 0.95 + tLocal * (0.36 + 0.64 * perspective);

        screenCoords[i] = {
          x: baseScreenX + p.ox,
          y: baseScreenY + p.oy,
          z: z2,
          lighting,
          size: p.size * sizeScale,
          kind: p.kind,
          isSignal: p.isSignal,
          isHub: p.isHub,
          nearCursor,
          inSurge,
          showInScatter: i % 4 === 0,
          tLocal,
          calloutLabel: p.calloutLabel,
        };
      }

      // =====================================================================
      // 1. DRAW 3D TRIANGULATED NEURAL PLEXUS MESH
      // =====================================================================
      if (maxAssemblyProgress > 0.32) {
        const meshAlpha = Math.min(1, (maxAssemblyProgress - 0.32) / 0.55);
        ctx.save();

        for (let e = 0; e < edges.length; e++) {
          const { a, b, isBridge } = edges[e];
          const ptA = screenCoords[a];
          const ptB = screenCoords[b];

          if (ptA.tLocal < 0.6 || ptB.tLocal < 0.6) continue;

          const avgZ = (ptA.z + ptB.z) * 0.5;
          if (avgZ > 55 && !isBridge) continue;

          const depthFade = Math.max(0.06, Math.min(1, (75 - avgZ) / 185));
          const highlight = ptA.nearCursor || ptB.nearCursor || ptA.inSurge || ptB.inSurge;

          ctx.strokeStyle = highlight || isBridge ? '#D95338' : '#262523';
          ctx.lineWidth = highlight || isBridge ? 0.95 : 0.6;
          ctx.globalAlpha =
            meshAlpha *
            depthFade *
            (highlight ? 0.68 : isBridge ? 0.5 : 0.24);

          ctx.beginPath();
          ctx.moveTo(ptA.x, ptA.y);
          ctx.lineTo(ptB.x, ptB.y);
          ctx.stroke();
        }

        // =====================================================================
        // 2. DRAW CONTINUOUS 3D NERVE / ARTERIAL TRACTS & CIRCULATING RED MINI-CIRCLES
        // =====================================================================
        for (let tIdx = 0; tIdx < nerveTracts.length; tIdx++) {
          const tract = nerveTracts[tIdx];
          const idxs = tract.indices;
          if (idxs.length < 3) continue;

          let sumZ = 0;
          let minT = 1;
          for (let k = 0; k < idxs.length; k++) {
            const sc = screenCoords[idxs[k]];
            sumZ += sc.z;
            if (sc.tLocal < minT) minT = sc.tLocal;
          }
          if (minT < 0.65) continue;

          const avgZ = sumZ / idxs.length;
          if (avgZ > 65) continue;

          const depthFade = Math.max(0.12, Math.min(1, (80 - avgZ) / 170));

          ctx.strokeStyle = tract.isMainArtery ? '#D95338' : '#57554F';
          ctx.lineWidth = tract.isMainArtery ? 1.05 : 0.8;
          ctx.globalAlpha =
            meshAlpha * depthFade * (tract.isMainArtery ? 0.42 : 0.28);

          ctx.beginPath();
          for (let k = 0; k < idxs.length; k++) {
            const pt = screenCoords[idxs[k]];
            if (k === 0) {
              ctx.moveTo(pt.x, pt.y);
            } else if (k < idxs.length - 1) {
              const nextPt = screenCoords[idxs[k + 1]];
              const midX = (pt.x + nextPt.x) * 0.5;
              const midY = (pt.y + nextPt.y) * 0.5;
              ctx.quadraticCurveTo(pt.x, pt.y, midX, midY);
            } else {
              ctx.lineTo(pt.x, pt.y);
            }
          }
          ctx.stroke();
        }

        // Advance and draw the Red Mini-Circles ("Blood / Synaptic Circulation") along the nerves
        if (maxAssemblyProgress > 0.65) {
          const circAlpha = Math.min(1, (maxAssemblyProgress - 0.65) / 0.3);
          const speedBoost = isSurging ? 2.2 : 1.0;

          for (let cIdx = 0; cIdx < corpuscles.length; cIdx++) {
            const corp = corpuscles[cIdx];
            const tract = nerveTracts[corp.tractIdx];
            if (!tract || tract.indices.length < 3) continue;

            if (!prefersReducedMotion) {
              corp.progress =
                (corp.progress + corp.speed * speedBoost * dt + 10) % 1;
            }

            const head = samplePointOnTract(
              tract.indices,
              corp.progress,
              screenCoords
            );
            if (head.tLocal < 0.8 || head.z > 65) continue;

            const depthAlpha = Math.max(0.2, Math.min(1, (80 - head.z) / 160));
            const dirSign = corp.speed >= 0 ? 1 : -1;

            // 1. Two trailing micro-droplets behind the main red mini-circle
            for (let tail = 1; tail <= 2; tail++) {
              const tailPt = samplePointOnTract(
                tract.indices,
                corp.progress - dirSign * tail * 0.028,
                screenCoords
              );
              ctx.fillStyle = '#D95338';
              ctx.globalAlpha = circAlpha * depthAlpha * (tail === 1 ? 0.55 : 0.28);
              ctx.beginPath();
              ctx.arc(
                tailPt.x,
                tailPt.y,
                corp.radius * (tail === 1 ? 0.72 : 0.48),
                0,
                Math.PI * 2
              );
              ctx.fill();
            }

            // 2. Core Vermilion Red Mini-Circle
            ctx.fillStyle = '#D95338';
            ctx.globalAlpha = circAlpha * depthAlpha * 0.96;
            ctx.beginPath();
            ctx.arc(head.x, head.y, corp.radius, 0, Math.PI * 2);
            ctx.fill();

            // 3. Delicate Outer Red Mini-Ring around the circulating corpuscle
            ctx.strokeStyle = '#D95338';
            ctx.lineWidth = 0.9;
            ctx.globalAlpha = circAlpha * depthAlpha * 0.55;
            ctx.beginPath();
            ctx.arc(head.x, head.y, corp.radius + 2.1, 0, Math.PI * 2);
            ctx.stroke();
          }
        }

        ctx.restore();
      }

      // =====================================================================
      // 3. DRAW PINS, DRAFTING BITS, AND CORTICAL HUBS (Back-to-Front)
      // =====================================================================
      const renderOrder = screenCoords.slice().sort((a, b) => b.z - a.z);

      ctx.font = '600 7.5px "IBM Plex Mono", monospace';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      for (let i = 0; i < renderOrder.length; i++) {
        const pt = renderOrder[i];
        if (!pt.showInScatter && pt.tLocal < 0.03) continue;
        if (pt.x < -10 || pt.x > width + 10 || pt.y < -10 || pt.y > height + 10) {
          continue;
        }

        const depthNorm = Math.max(0, Math.min(1, (130 - pt.z) / 260));
        const shade3D = depthNorm * 0.65 + pt.lighting * 0.35;
        const shade = (1 - pt.tLocal) * 0.76 + pt.tLocal * shade3D;

        let fillColor = '#262523';
        let alpha = 0.2 + shade * 0.72;

        if (pt.isSignal || pt.nearCursor || pt.inSurge) {
          fillColor = '#D95338';
          alpha = Math.max(0.84, alpha);
        } else if (shade < 0.36) {
          fillColor = '#C2BEB4';
          alpha = 0.34;
        } else if (shade < 0.62) {
          fillColor = '#6E6B64';
          alpha = 0.64;
        }

        if (!pt.showInScatter) {
          alpha *= pt.tLocal;
        }

        ctx.fillStyle = fillColor;
        ctx.strokeStyle = fillColor;
        ctx.globalAlpha = alpha;

        const r = pt.inSurge ? pt.size * 1.25 : pt.size;

        if (pt.kind === 'dot') {
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, r, 0, Math.PI * 2);
          ctx.fill();
        } else if (pt.kind === 'cross') {
          const arm = r * 1.45;
          ctx.lineWidth = 1.0;
          ctx.beginPath();
          ctx.moveTo(pt.x - arm, pt.y);
          ctx.lineTo(pt.x + arm, pt.y);
          ctx.moveTo(pt.x, pt.y - arm);
          ctx.lineTo(pt.x, pt.y + arm);
          ctx.stroke();
        } else if (pt.kind === 'ring') {
          ctx.lineWidth = 1.15;
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, r * 1.35, 0, Math.PI * 2);
          ctx.stroke();
        } else if (pt.kind === 'bit0' || pt.kind === 'bit1') {
          ctx.fillText(pt.kind === 'bit0' ? '0' : '1', pt.x, pt.y);
        }
      }

      // =====================================================================
      // 4. DRAW 3D FLOATING CODEBRAIN TELEMETRY CALLOUT TAGS (Front-Facing Hubs)
      // =====================================================================
      if (maxAssemblyProgress > 0.82) {
        const calloutAlpha = Math.min(1, (maxAssemblyProgress - 0.82) / 0.18);
        ctx.save();
        ctx.font = '500 8.5px "IBM Plex Mono", monospace';
        ctx.textBaseline = 'middle';

        for (const cIdx of calloutIndices) {
          const sc = screenCoords[cIdx];
          if (!sc || !sc.calloutLabel || sc.z > 18) continue;

          const frontFade = Math.max(0, Math.min(1, (18 - sc.z) / 50));
          const dir = sc.x >= cx ? 1 : -1;
          const elbowX = sc.x + dir * 14;
          const elbowY = sc.y - 10;
          const endX = elbowX + dir * 16;

          ctx.globalAlpha = calloutAlpha * frontFade * 0.9;
          ctx.strokeStyle = '#D95338';
          ctx.lineWidth = 0.9;

          ctx.beginPath();
          ctx.moveTo(sc.x, sc.y);
          ctx.lineTo(elbowX, elbowY);
          ctx.lineTo(endX, elbowY);
          ctx.stroke();

          const textWidth = ctx.measureText(sc.calloutLabel).width;
          const padX = 5;
          const boxW = textWidth + padX * 2;
          const boxH = 14;
          const boxX = dir === 1 ? endX : endX - boxW;
          const boxY = elbowY - boxH / 2;

          ctx.fillStyle = '#F2F0EC';
          ctx.fillRect(boxX, boxY, boxW, boxH);
          ctx.strokeStyle = '#262523';
          ctx.lineWidth = 0.8;
          ctx.strokeRect(boxX, boxY, boxW, boxH);

          ctx.fillStyle = '#262523';
          ctx.textAlign = 'left';
          ctx.fillText(sc.calloutLabel, boxX + padX, elbowY + 0.5);
        }

        ctx.restore();
      }

      ctx.globalAlpha = 1;
      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render);
      }
    };

    if (prefersReducedMotion) {
      render(performance.now());
      if (typeof document !== 'undefined' && 'fonts' in document && document.fonts?.ready) {
        document.fonts.ready.then(() => {
          if (!disposed) {
            render(performance.now());
          }
        });
      }
    } else {
      animationFrameId = requestAnimationFrame(render);
    }

    return () => {
      disposed = true;
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('scroll', handleScrollTrigger);
      window.removeEventListener('wheel', triggerFormationOnce);
      window.removeEventListener('touchmove', triggerFormationOnce);
      window.removeEventListener('click', handleClick);
      document.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [onPhaseChange, prefersReducedMotion]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: '-36px',
        left: '50%',
        transform: 'translateX(-50%)',
      }}
      className={`block pointer-events-none ${className}`}
      aria-hidden="true"
    />
  );
};
