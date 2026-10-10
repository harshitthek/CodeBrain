import React from 'react';

const GLYPHS_5X7: Record<string, string[]> = {
  A: ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
  B: ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
  C: ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
  D: ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
  E: ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
  F: ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
  G: ['01110', '10001', '10000', '10111', '10001', '10001', '01110'],
  H: ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
  I: ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
  J: ['00111', '00010', '00010', '00010', '10010', '10010', '01100'],
  K: ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
  L: ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
  M: ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
  N: ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
  O: ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
  P: ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
  Q: ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],
  R: ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
  S: ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
  T: ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
  U: ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
  V: ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
  W: ['10001', '10001', '10001', '10101', '10101', '11011', '10001'],
  X: ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
  Y: ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
  Z: ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
  '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
  '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
  '2': ['01110', '10001', '00001', '00110', '01000', '10000', '11111'],
  '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
  '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
  '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
  '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'],
  '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
  '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
  '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
  '?': ['01110', '10001', '00001', '00110', '00100', '00000', '00100'],
  '!': ['00100', '00100', '00100', '00100', '00100', '00000', '00100'],
  '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
  '_': ['00000', '00000', '00000', '00000', '00000', '00000', '11111'],
  '/': ['00001', '00010', '00100', '00100', '01000', '10000', '00000'],
  ':': ['00000', '00100', '00100', '00000', '00100', '00100', '00000'],
  '.': ['00000', '00000', '00000', '00000', '00000', '01100', '01100'],
  '+': ['00000', '00100', '00100', '11111', '00100', '00100', '00000'],
  '>': ['10000', '01000', '00100', '00010', '00100', '01000', '10000'],
  '<': ['00001', '00010', '00100', '01000', '00100', '00010', '00001'],
  '(': ['00010', '00100', '01000', '01000', '01000', '00100', '00010'],
  ')': ['01000', '00100', '00010', '00010', '00010', '00100', '01000'],
  '%': ['11001', '11010', '00100', '00100', '01011', '10011', '00000'],
  '&': ['01100', '10010', '10100', '01000', '10101', '10010', '01101'],
  ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
};

export interface DotMatrixTextProps {
  text: string;
  /** Pixel pitch between dot centers (default 6) */
  pitch?: number;
  /** Radius of lit dots (default 2.15) */
  dotRadius?: number;
  /** Radius of unlit background bed dots (default 1.15) */
  ghostRadius?: number;
  /** Pad character cells to a fixed column count (like the reference row bed) */
  padToChars?: number;
  /** Show the underlying unlit dot matrix bed */
  showBed?: boolean;
  /** Color of lit dots (default #262523) */
  color?: string;
  /** Color of accented characters (default #D95338 vermilion) */
  accentColor?: string;
  /** Characters or indices that should light up in accentColor (e.g. ['?']) */
  accentChars?: string[];
  /** Render the entire text in accentColor */
  accentAll?: boolean;
  className?: string;
}

export const DotMatrixText: React.FC<DotMatrixTextProps> = ({
  text,
  pitch = 6,
  dotRadius = 2.15,
  ghostRadius = 1.1,
  padToChars,
  showBed = true,
  color = '#262523',
  accentColor = '#D95338',
  accentChars = ['?'],
  accentAll = false,
  className = '',
}) => {
  const normalized = text.toUpperCase();
  const totalCharCells = Math.max(normalized.length, padToChars || normalized.length);
  // Each char is 5 cols wide + 1 col spacing (except trailing cell)
  const totalDotCols = Math.max(1, totalCharCells * 6 - 1);
  const totalDotRows = 7;

  const svgWidth = totalDotCols * pitch;
  const svgHeight = totalDotRows * pitch;

  // Build lookup of active dots: key = `${col},${row}` -> fill color
  const activeMap = new Map<string, string>();

  for (let cIdx = 0; cIdx < normalized.length; cIdx++) {
    const ch = normalized[cIdx];
    const glyph = GLYPHS_5X7[ch] || GLYPHS_5X7[' '];
    const isAccentChar = accentAll || accentChars.includes(ch);
    const fillColor = isAccentChar ? accentColor : color;
    const colOffset = cIdx * 6;

    for (let r = 0; r < 7; r++) {
      const rowStr = glyph[r] || '00000';
      for (let c = 0; c < 5; c++) {
        if (rowStr[c] === '1') {
          activeMap.set(`${colOffset + c},${r}`, fillColor);
        }
      }
    }
  }

  const circles: React.ReactNode[] = [];

  for (let r = 0; r < totalDotRows; r++) {
    const cy = r * pitch + pitch / 2;
    for (let c = 0; c < totalDotCols; c++) {
      const cx = c * pitch + pitch / 2;
      const key = `${c},${r}`;
      const litColor = activeMap.get(key);

      if (litColor) {
        circles.push(
          <circle
            key={key}
            cx={cx}
            cy={cy}
            r={dotRadius}
            fill={litColor}
          />
        );
      } else if (showBed) {
        circles.push(
          <circle
            key={key}
            cx={cx}
            cy={cy}
            r={ghostRadius}
            fill="#DFDCD4"
          />
        );
      }
    }
  }

  return (
    <svg
      width={svgWidth}
      height={svgHeight}
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      className={`inline-block select-none overflow-visible max-w-full h-auto ${className}`}
      role="img"
      aria-label={text}
    >
      {circles}
    </svg>
  );
};
