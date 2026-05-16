import {
    BarChart, Bar, XAxis, YAxis, Tooltip,
    ResponsiveContainer, Cell
} from 'recharts';
import { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';
import type { FillerWords } from '../../types';

interface FillerWordChartProps {
    fillerWords: FillerWords;
}

const COLORS: Record<string, string> = {
    um: '#818cf8',
    uh: '#a78bfa',
    like: '#f472b6',
    'you know': '#fb923c',
    so: '#34d399',
};

const THRESHOLDS = { good: 2, warn: 5 };

const getBarColor = (count: number): string => {
    if (count <= THRESHOLDS.good) return '#34d399';
    if (count <= THRESHOLDS.warn) return '#fb923c';
    return '#f87171';
};

export const FillerWordChart = ({ fillerWords }: FillerWordChartProps) => {
    const data = Object.entries(fillerWords).map(([word, count]) => ({
        word,
        count,
        color: getBarColor(count),
    }));

    const total = data.reduce((sum, d) => sum + d.count, 0);

    return (
        <div className="bg-zinc-900 rounded-xl p-5 border border-zinc-800">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-zinc-200 font-semibold text-sm uppercase tracking-wider">
                    Filler Words
                </h3>
                <span className={`
                    text-xs font-bold px-2 py-1 rounded-full
                    ${total <= 3
                        ? 'bg-emerald-900/50 text-emerald-400'
                        : total <= 8
                            ? 'bg-orange-900/50 text-orange-400'
                            : 'bg-red-900/50 text-red-400'}
                `}>
                    {total} total
                </span>
            </div>
            <ResponsiveContainer width="100%" height={160}>
                <BarChart data={data} barCategoryGap="30%">
                    <XAxis
                        dataKey="word"
                        tick={{ fill: '#a1a1aa', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                    />
                    <YAxis
                        allowDecimals={false}
                        tick={{ fill: '#71717a', fontSize: 11 }}
                        axisLine={false}
                        tickLine={false}
                        width={24}
                    />
                    <Tooltip
                        contentStyle={{
                            background: '#18181b',
                            border: '1px solid #3f3f46',
                            borderRadius: '8px',
                            color: '#e4e4e7',
                            fontSize: '12px',
                        }}
                        cursor={{ fill: 'rgba(255,255,255,0.04)' }}
                        formatter={(value: ValueType | undefined, name: NameType | undefined) => [value ?? 0, 'occurrences']}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                        {data.map((entry, i) => (
                            <Cell key={i} fill={entry.color} />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};