const PROFESSIONAL_COLORS = [
    "#4E79A7", // Blue
    "#F28E2B", // Orange
    "#59A14F", // Green
    "#E15759", // Red
    "#B07AA1", // Purple
    "#76B7B2", // Teal
    "#EDC948", // Gold
    "#9C755F", // Brown
    "#BAB0AC", // Gray
    "#577590", // Slate Blue
];

let hue = Math.random();

function hslToHex(h: number, s: number, l: number): string {
    l /= 100;

    const a = (s * Math.min(l, 1 - l)) / 100;

    const f = (n: number) => {
        const k = (n + h * 12) % 12;
        const color = l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));

        return Math.round(color * 255)
            .toString(16)
            .padStart(2, "0");
    };

    return `#${f(0)}${f(8)}${f(4)}`;
}

export function getColor(index: number): string {
    if (index < PROFESSIONAL_COLORS.length) {
        return PROFESSIONAL_COLORS[index];
    }

    // Spread new hues evenly
    hue = (hue + 0.61803398875) % 1;

    // Muted colors (not neon)
    return hslToHex(hue, 45, 55);
}