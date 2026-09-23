/* A small QR encoder, byte mode, error correction level M, versions 1 to 10.
 *
 * The approve page draws the pairing link as a QR so the desktop that started the pairing can
 * hand the approval to a phone. That is one short URL, so a dependency, a network call to an
 * image service or a canvas is all more than the page needs: this returns an SVG of squares.
 *
 * ISO/IEC 18004. Checked module for module against the reference `qrcode` package for every
 * mask pattern in scripts/test-connect-pair.mjs.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.GrinderQR = factory();
})(typeof window !== "undefined" ? window : globalThis, function () {
  // Total codewords per version, then [ec codewords per block, blocks, data, blocks, data] at M.
  const TOTAL = [26, 44, 70, 100, 134, 172, 196, 242, 292, 346];
  const LEVEL_M = [
    [10, 1, 16, 0, 0],
    [16, 1, 28, 0, 0],
    [26, 1, 44, 0, 0],
    [18, 2, 32, 0, 0],
    [24, 2, 43, 0, 0],
    [16, 4, 27, 0, 0],
    [18, 4, 31, 0, 0],
    [22, 2, 38, 2, 39],
    [22, 3, 36, 2, 37],
    [26, 4, 43, 1, 44],
  ];
  const ALIGNMENT = [[], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34], [6, 22, 38], [6, 24, 42], [6, 26, 46], [6, 28, 50]];
  const MASKS = [
    (x, y) => (x + y) % 2 === 0,
    (x, y) => y % 2 === 0,
    (x) => x % 3 === 0,
    (x, y) => (x + y) % 3 === 0,
    (x, y) => (Math.floor(x / 3) + Math.floor(y / 2)) % 2 === 0,
    (x, y) => ((x * y) % 2) + ((x * y) % 3) === 0,
    (x, y) => (((x * y) % 2) + ((x * y) % 3)) % 2 === 0,
    (x, y) => (((x + y) % 2) + ((x * y) % 3)) % 2 === 0,
  ];
  const FINDER = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0];

  const EXP = new Uint8Array(256);
  const LOG = new Uint8Array(256);
  for (let i = 0, value = 1; i < 255; i += 1) {
    EXP[i] = value;
    LOG[value] = i;
    value <<= 1;
    if (value & 0x100) value ^= 0x11d;
  }
  const mul = (a, b) => (a === 0 || b === 0 ? 0 : EXP[(LOG[a] + LOG[b]) % 255]);

  function generator(degree) {
    let poly = [1];
    for (let i = 0; i < degree; i += 1) {
      const next = new Array(poly.length + 1).fill(0);
      for (let j = 0; j < poly.length; j += 1) {
        next[j] ^= mul(poly[j], 1);
        next[j + 1] ^= mul(poly[j], EXP[i]);
      }
      poly = next;
    }
    return poly.slice(1);
  }

  function remainder(data, degree) {
    const gen = generator(degree);
    const out = new Array(degree).fill(0);
    for (const byte of data) {
      const factor = byte ^ out.shift();
      out.push(0);
      for (let i = 0; i < degree; i += 1) out[i] ^= mul(gen[i], factor);
    }
    return out;
  }

  function codewords(text) {
    const bytes = new TextEncoder().encode(text);
    let version = 1;
    for (; version <= 10; version += 1) {
      const [, blocks1, data1, blocks2, data2] = LEVEL_M[version - 1];
      const capacity = (blocks1 * data1 + blocks2 * data2) * 8;
      if (4 + (version <= 9 ? 8 : 16) + bytes.length * 8 <= capacity) break;
    }
    if (version > 10) throw new Error("That link is too long for this QR encoder.");
    const [ec, blocks1, data1, blocks2, data2] = LEVEL_M[version - 1];
    const total = blocks1 * data1 + blocks2 * data2;
    const bits = [];
    const push = (value, width) => {
      for (let i = width - 1; i >= 0; i -= 1) bits.push((value >>> i) & 1);
    };
    push(0b0100, 4);
    push(bytes.length, version <= 9 ? 8 : 16);
    for (const byte of bytes) push(byte, 8);
    push(0, Math.min(4, total * 8 - bits.length));
    while (bits.length % 8 !== 0) bits.push(0);
    const words = [];
    for (let i = 0; i < bits.length; i += 8) words.push(bits.slice(i, i + 8).reduce((acc, bit) => (acc << 1) | bit, 0));
    for (let pad = 0xec; words.length < total; pad ^= 0xec ^ 0x11) words.push(pad);

    const blocks = [];
    let taken = 0;
    for (const [count, size] of [
      [blocks1, data1],
      [blocks2, data2],
    ]) {
      for (let i = 0; i < count; i += 1) {
        const block = words.slice(taken, taken + size);
        taken += size;
        blocks.push({ data: block, ec: remainder(block, ec) });
      }
    }
    const out = [];
    for (let i = 0; i < Math.max(data1, data2); i += 1) {
      for (const block of blocks) if (i < block.data.length) out.push(block.data[i]);
    }
    for (let i = 0; i < ec; i += 1) for (const block of blocks) out.push(block.ec[i]);
    if (out.length !== TOTAL[version - 1]) throw new Error("QR codeword count is wrong.");
    return { version, words: out };
  }

  function draw(version, words, mask) {
    const size = version * 4 + 17;
    const modules = [];
    const fixed = [];
    for (let y = 0; y < size; y += 1) {
      modules.push(new Array(size).fill(0));
      fixed.push(new Array(size).fill(false));
    }
    const set = (x, y, dark) => {
      if (x < 0 || y < 0 || x >= size || y >= size) return;
      modules[y][x] = dark ? 1 : 0;
      fixed[y][x] = true;
    };
    const bit = (value, index) => ((value >>> index) & 1) !== 0;

    for (let i = 0; i < size; i += 1) {
      set(6, i, i % 2 === 0);
      set(i, 6, i % 2 === 0);
    }
    for (const [cx, cy] of [
      [3, 3],
      [size - 4, 3],
      [3, size - 4],
    ]) {
      for (let dy = -4; dy <= 4; dy += 1) {
        for (let dx = -4; dx <= 4; dx += 1) {
          const reach = Math.max(Math.abs(dx), Math.abs(dy));
          set(cx + dx, cy + dy, reach !== 2 && reach !== 4);
        }
      }
    }
    const centres = ALIGNMENT[version - 1];
    for (const cx of centres) {
      for (const cy of centres) {
        const corner = (cx === 6 && cy === 6) || (cx === 6 && cy === size - 7) || (cx === size - 7 && cy === 6);
        if (corner) continue;
        for (let dy = -2; dy <= 2; dy += 1) {
          for (let dx = -2; dx <= 2; dx += 1) set(cx + dx, cy + dy, Math.max(Math.abs(dx), Math.abs(dy)) !== 1);
        }
      }
    }
    // Format information, twice, with the level M bits (00) and the chosen mask.
    let format = mask;
    let rest = format;
    for (let i = 0; i < 10; i += 1) rest = (rest << 1) ^ ((rest >>> 9) * 0x537);
    const formatBits = ((format << 10) | rest) ^ 0x5412;
    for (let i = 0; i <= 5; i += 1) set(8, i, bit(formatBits, i));
    set(8, 7, bit(formatBits, 6));
    set(8, 8, bit(formatBits, 7));
    set(7, 8, bit(formatBits, 8));
    for (let i = 9; i < 15; i += 1) set(14 - i, 8, bit(formatBits, i));
    for (let i = 0; i < 8; i += 1) set(size - 1 - i, 8, bit(formatBits, i));
    for (let i = 8; i < 15; i += 1) set(8, size - 15 + i, bit(formatBits, i));
    set(8, size - 8, true);
    if (version >= 7) {
      let versionRest = version;
      for (let i = 0; i < 12; i += 1) versionRest = (versionRest << 1) ^ ((versionRest >>> 11) * 0x1f25);
      const versionBits = (version << 12) | versionRest;
      for (let i = 0; i < 18; i += 1) {
        const dark = bit(versionBits, i);
        const far = size - 11 + (i % 3);
        const near = Math.floor(i / 3);
        set(far, near, dark);
        set(near, far, dark);
      }
    }

    let index = 0;
    for (let right = size - 1; right >= 1; right -= 2) {
      if (right === 6) right = 5;
      for (let step = 0; step < size; step += 1) {
        for (let column = 0; column < 2; column += 1) {
          const x = right - column;
          const upward = ((right + 1) & 2) === 0;
          const y = upward ? size - 1 - step : step;
          if (fixed[y][x] || index >= words.length * 8) continue;
          modules[y][x] = bit(words[index >>> 3], 7 - (index & 7)) ? 1 : 0;
          index += 1;
        }
      }
    }
    for (let y = 0; y < size; y += 1) {
      for (let x = 0; x < size; x += 1) {
        if (!fixed[y][x] && MASKS[mask](x, y)) modules[y][x] ^= 1;
      }
    }
    return modules;
  }

  function runs(line) {
    let score = 0;
    let length = 1;
    for (let i = 1; i <= line.length; i += 1) {
      if (i < line.length && line[i] === line[i - 1]) {
        length += 1;
        continue;
      }
      if (length >= 5) score += 3 + (length - 5);
      length = 1;
    }
    for (let i = 0; i + 11 <= line.length; i += 1) {
      const window = line.slice(i, i + 11);
      if (FINDER.every((value, at) => value === window[at])) score += 40;
      if (FINDER.every((value, at) => value === window[10 - at])) score += 40;
    }
    return score;
  }

  function penalty(modules) {
    const size = modules.length;
    let score = 0;
    let dark = 0;
    for (let i = 0; i < size; i += 1) {
      score += runs(modules[i]);
      score += runs(modules.map((row) => row[i]));
    }
    for (let y = 0; y + 1 < size; y += 1) {
      for (let x = 0; x + 1 < size; x += 1) {
        const first = modules[y][x];
        if (first === modules[y][x + 1] && first === modules[y + 1][x] && first === modules[y + 1][x + 1]) score += 3;
      }
    }
    for (const row of modules) for (const value of row) dark += value;
    const share = (dark * 100) / (size * size);
    score += Math.floor(Math.abs(share - 50) / 5) * 10;
    return score;
  }

  // The module grid, one row per array, 1 for dark. mask is chosen by penalty unless given.
  function matrix(text, mask) {
    const { version, words } = codewords(String(text));
    if (Number.isInteger(mask)) return { version, modules: draw(version, words, mask), mask };
    let best = null;
    for (let candidate = 0; candidate < 8; candidate += 1) {
      const modules = draw(version, words, candidate);
      const score = penalty(modules);
      if (!best || score < best.score) best = { modules, score, mask: candidate };
    }
    return { version, modules: best.modules, mask: best.mask };
  }

  // One SVG path of dark squares, sized in modules so CSS can scale it.
  function svg(text, { label = "QR code", quiet = 4 } = {}) {
    const { modules } = matrix(text);
    const size = modules.length + quiet * 2;
    let path = "";
    modules.forEach((row, y) => {
      row.forEach((dark, x) => {
        if (dark) path += `M${x + quiet} ${y + quiet}h1v1h-1z`;
      });
    });
    return (
      `<svg class="qr" viewBox="0 0 ${size} ${size}" width="${size * 4}" height="${size * 4}" role="img" ` +
      `aria-label="${String(label).replace(/[&<>"]/g, "")}" shape-rendering="crispEdges">` +
      `<rect width="${size}" height="${size}" fill="#fff"></rect><path d="${path}" fill="#111"></path></svg>`
    );
  }

  return { matrix, svg, penalty };
});
