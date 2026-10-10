import Lenis from 'lenis';

export let lenisInstance: Lenis | null = null;
let rafId: number | null = null;

export const destroySmoothScroll = (): void => {
  if (rafId !== null && typeof window !== 'undefined') {
    cancelAnimationFrame(rafId);
    rafId = null;
  }
  if (lenisInstance) {
    lenisInstance.destroy();
    lenisInstance = null;
  }
};

export const initSmoothScroll = (): Lenis | null => {
  if (typeof window === 'undefined') return null;

  destroySmoothScroll();

  lenisInstance = new Lenis({
    duration: 1.15,
    easing: (t: number) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    orientation: 'vertical',
    gestureOrientation: 'vertical',
    smoothWheel: true,
    wheelMultiplier: 0.9,
    touchMultiplier: 1.5,
  });

  function raf(time: number) {
    if (!lenisInstance) return;
    lenisInstance.raf(time);
    rafId = requestAnimationFrame(raf);
  }

  rafId = requestAnimationFrame(raf);
  return lenisInstance;
};

export const scrollToElement = (id: string, offset: number = -90) => {
  const el = document.getElementById(id);
  if (!el) return;

  if (lenisInstance) {
    lenisInstance.scrollTo(el, { offset, duration: 1.15 });
  } else {
    const top = el.getBoundingClientRect().top + window.scrollY + offset;
    window.scrollTo({ top, behavior: 'smooth' });
  }
};

