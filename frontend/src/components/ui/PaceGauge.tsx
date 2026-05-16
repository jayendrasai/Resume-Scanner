interface PaceGaugeProps {
    wpm: number;
}

// Ideal interview speaking pace: 120–160 WPM
const getPaceLabel = (wpm: number): { label: string; color: string; bg: string } => {
    if (wpm < 100) return { label: 'Too slow', color: 'text-blue-400', bg: 'bg-blue-900/40' };
    if (wpm < 120) return { label: 'Slightly slow', color: 'text-sky-400', bg: 'bg-sky-900/40' };
    if (wpm <= 160) return { label: 'Ideal pace', color: 'text-emerald-400', bg: 'bg-emerald-900/40' };
    if (wpm <= 190) return { label: 'Slightly fast', color: 'text-orange-400', bg: 'bg-orange-900/40' };
    return { label: 'Too fast', color: 'text-red-400', bg: 'bg-red-900/40' };
};

// Map WPM to gauge arc 0–180 degrees. Clamp 60–240 WPM range.
const wpmToAngle = (wpm: number): number => {
    const min = 60, max = 240;
    const clamped = Math.min(Math.max(wpm, min), max);
    return ((clamped - min) / (max - min)) * 180;
};

export const PaceGauge = ({ wpm }: PaceGaugeProps) => {
    const { label, color, bg } = getPaceLabel(wpm);
    const angle = wpmToAngle(wpm);

    // SVG arc needle
    const cx = 80, cy = 80, r = 60;
    const rad = ((angle - 180) * Math.PI) / 180;
    const nx = cx + r * Math.cos(rad);
    const ny = cy + r * Math.sin(rad);

    return (
        <div className="bg-zinc-900 rounded-xl p-5 border border-zinc-800">
            <h3 className="text-zinc-200 font-semibold text-sm uppercase tracking-wider mb-4">
                Speaking Pace
            </h3>
            <div className="flex items-center gap-6">
                <svg width="160" height="90" viewBox="0 0 160 90">
                    {/* Background arc */}
                    <path
                        d="M 20 80 A 60 60 0 0 1 140 80"
                        fill="none" stroke="#3f3f46" strokeWidth="10"
                        strokeLinecap="round"
                    />
                    {/* Coloured zones */}
                    <path d="M 20 80 A 60 60 0 0 1 50 27" fill="none" stroke="#3b82f6" strokeWidth="10" strokeLinecap="round" opacity="0.6" />
                    <path d="M 50 27 A 60 60 0 0 1 80 20" fill="none" stroke="#22d3ee" strokeWidth="10" strokeLinecap="round" opacity="0.6" />
                    <path d="M 80 20 A 60 60 0 0 1 113 28" fill="none" stroke="#34d399" strokeWidth="10" strokeLinecap="round" opacity="0.8" />
                    <path d="M 113 28 A 60 60 0 0 1 133 55" fill="none" stroke="#fb923c" strokeWidth="10" strokeLinecap="round" opacity="0.6" />
                    <path d="M 133 55 A 60 60 0 0 1 140 80" fill="none" stroke="#f87171" strokeWidth="10" strokeLinecap="round" opacity="0.6" />
                    {/* Needle */}
                    <line
                        x1={cx} y1={cy}
                        x2={nx} y2={ny}
                        stroke="#e4e4e7" strokeWidth="2.5"
                        strokeLinecap="round"
                    />
                    <circle cx={cx} cy={cy} r="4" fill="#e4e4e7" />
                </svg>
                <div className="flex flex-col gap-2">
                    <span className="text-3xl font-bold text-zinc-100">
                        {wpm}
                    </span>
                    <span className="text-zinc-500 text-xs">words/min</span>
                    <span className={`text-xs font-semibold px-2 py-1 rounded-full ${bg} ${color}`}>
                        {label}
                    </span>
                </div>
            </div>
        </div>
    );
};