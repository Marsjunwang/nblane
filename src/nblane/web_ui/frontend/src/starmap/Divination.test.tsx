/* Divination: pure yao-row ordering + HexagramSymbol rendering. */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { HexagramSymbol, yaoRows } from './Divination';

describe('yaoRows (卦象爻序)', () => {
  it('renders bottom-up symbol_lines top-down (初爻在下)', () => {
    // 火天大有 lines bottom-up: 111101 → top-down display: 101111
    expect(yaoRows([1, 1, 1, 1, 0, 1])).toEqual([true, false, true, true, true, true]);
  });

  it('maps 1 → solid (阳) and 0 → broken (阴)', () => {
    expect(yaoRows([0, 0, 0, 0, 0, 0])).toEqual([false, false, false, false, false, false]);
    expect(yaoRows([1, 1, 1, 1, 1, 1])).toEqual([true, true, true, true, true, true]);
  });

  it('truncates defensively to 6 yao', () => {
    expect(yaoRows([1, 0, 1, 0, 1, 0, 1, 1])).toHaveLength(6);
  });
});

describe('HexagramSymbol', () => {
  it('renders 6 yao rows with solid/broken classes in display order', () => {
    render(<HexagramSymbol lines={[1, 1, 1, 1, 0, 1]} />);
    const sym = screen.getByTestId('hexagram-symbol');
    const rows = sym.querySelectorAll('.hex-yao');
    expect(rows).toHaveLength(6);
    expect(rows[0].className).toContain('solid'); // top yao = lines[5] = 1
    expect(rows[1].className).toContain('broken'); // lines[4] = 0
    expect(rows[5].className).toContain('solid'); // bottom yao = lines[0] = 1
  });

  it('supports the 摇卦 animated state', () => {
    render(<HexagramSymbol lines={[1, 1, 1, 1, 1, 1]} animated />);
    expect(screen.getByTestId('hexagram-symbol').className).toContain('casting');
  });
});
