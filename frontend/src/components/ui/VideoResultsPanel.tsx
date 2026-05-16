import { FillerWordChart } from './FillerWordChart';
import { PaceGauge } from './PaceGauge';
import type { JobResult } from '../../types';

interface VideoResultsPanelProps {
    result: JobResult;
    onReset: () => void;
}

const getClarityColor = (score: number) => {
    if (score >= 70) return 'text-emerald-400';
    if (score >= 50) return 'text-orange-400';
    return 'text-red-400';
};

const getClarityLabel = (score: number) => {
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Needs work';
    return 'Poor';
};

export const VideoResultsPanel = ({ result, onReset }: VideoResultsPanelProps) => {
    const { transcript, duration_seconds, analysis } = result;
    const { filler_words, pace_wpm, clarity_score, tips } = analysis;

    const minutes = Math.floor(duration_seconds / 60);
    const seconds = Math.round(duration_seconds % 60);

    return (
        <div className="flex flex-col gap-5 w-full max-w-2xl mx-auto">

            {/* Header */}
            <div className="flex items-center justify-between">
                <h2 className="text-zinc-100 text-xl font-bold">
                    Interview Analysis
                </h2>
                <button
                    onClick={onReset}
                    className="text-sm text-zinc-400 hover:text-zinc-200 transition-colors
                               px-3 py-1.5 rounded-lg border border-zinc-700 hover:border-zinc-500"
                >
                    Analyse another
                </button>
            </div>

            {/* Clarity score */}
            <div className="bg-zinc-900 rounded-xl p-5 border border-zinc-800 flex items-center gap-5">
                <div className="flex flex-col items-center justify-center
                                w-20 h-20 rounded-full border-4 border-zinc-700 shrink-0">
                    <span className={`text-2xl font-bold ${getClarityColor(clarity_score)}`}>
                        {clarity_score}
                    </span>
                    <span className="text-zinc-500 text-xs">/ 100</span>
                </div>
                <div>
                    <p className="text-zinc-200 font-semibold">Clarity Score</p>
                    <p className={`text-sm font-medium ${getClarityColor(clarity_score)}`}>
                        {getClarityLabel(clarity_score)}
                    </p>
                    <p className="text-zinc-500 text-xs mt-1">
                        Duration: {minutes}m {seconds}s
                    </p>
                </div>
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <FillerWordChart fillerWords={filler_words} />
                <PaceGauge wpm={pace_wpm} />
            </div>

            {/* Tips */}
            <div className="bg-zinc-900 rounded-xl p-5 border border-zinc-800">
                <h3 className="text-zinc-200 font-semibold text-sm uppercase tracking-wider mb-4">
                    Improvement Tips
                </h3>
                <ol className="flex flex-col gap-3">
                    {tips.map((tip, i) => (
                        <li key={i} className="flex gap-3 items-start">
                            {/* <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-900/60
                                             text-indigo-400 text-xs font-bold flex items-center
                                             justify-center mt-0.5">
                                {i + 1}
                            </span> */}
                            <p className="text-zinc-300 text-sm leading-relaxed">{tip}</p>
                        </li>
                    ))}
                </ol>
            </div>

            {/* Transcript */}
            <details className="bg-zinc-900 rounded-xl border border-zinc-800">
                <summary className="px-5 py-4 text-zinc-400 text-sm cursor-pointer
                                    hover:text-zinc-200 transition-colors select-none">
                    View full transcript
                </summary>
                <p className="px-5 pb-5 text-zinc-400 text-sm leading-relaxed
                               border-t border-zinc-800 pt-4 whitespace-pre-wrap">
                    {transcript}
                </p>
            </details>
        </div>
    );
};