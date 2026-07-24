import React from 'react';

interface FeedbackFormProps {
  difficulty: number;
  completion: number;
  hours: number;
  feedback: string;
  onDifficultyChange: (v: number) => void;
  onCompletionChange: (v: number) => void;
  onHoursChange: (v: number) => void;
  onFeedbackChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  readOnlyCompletion?: boolean;
}

const DIFFICULTY_LABELS = ['很简单', '偏简单', '适中', '偏难', '很难'];

export const FeedbackForm: React.FC<FeedbackFormProps> = ({
  difficulty,
  completion,
  hours,
  feedback,
  onDifficultyChange,
  onCompletionChange,
  onHoursChange,
  onFeedbackChange,
  onSubmit,
  disabled = false,
  readOnlyCompletion = false,
}) => {
  return (
    <div className="bg-gray-800 rounded-xl p-5 space-y-5 border border-gray-700/50">
      <h2 className="text-lg font-bold text-white">今日反馈</h2>
      <div>
        <div className="text-gray-400 text-sm mb-2">难度评分</div>
        <div className="flex gap-1.5 items-center">
          {[1, 2, 3, 4, 5].map(n => (
            <button
              key={n}
              onClick={() => onDifficultyChange(n)}
              disabled={disabled}
              className={`text-2xl transition-all hover:scale-110 ${
                n <= difficulty ? 'text-amber-400 drop-shadow-[0_0_4px_rgba(251,191,36,0.5)]' : 'text-gray-600'
              }`}
              title={DIFFICULTY_LABELS[n - 1]}
            >★</button>
          ))}
          <span className="text-gray-400 text-xs ml-2">{DIFFICULTY_LABELS[difficulty - 1]}</span>
        </div>
      </div>
      <div>
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-400">完成度</span>
          <span className="text-indigo-400 font-medium">{completion}%</span>
        </div>
        <input
          type="range" min="0" max="100" step="10"
          value={completion}
          onChange={e => onCompletionChange(Number(e.target.value))}
          disabled={disabled || readOnlyCompletion}
          className={`w-full h-2 bg-gray-700 rounded-full appearance-none ${readOnlyCompletion ? 'cursor-default' : 'cursor-pointer'} [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-indigo-500 [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:cursor-pointer`}
        />
        <div className="flex justify-between text-xs text-gray-600 mt-1"><span>0%</span><span>50%</span><span>100%</span></div>
        {readOnlyCompletion && (
          <p className="text-xs text-gray-500 mt-2">根据已完成任务数自动计算</p>
        )}
      </div>
      <div className="flex gap-4 items-center">
        <span className="text-gray-400 text-sm">实际学习时长</span>
        <input type="number" min="0" max="12" step="0.5" value={hours} onChange={e => onHoursChange(Number(e.target.value))} disabled={disabled} className="w-20 bg-gray-700 text-white rounded-lg px-3 py-2 text-center text-sm outline-none focus:ring-2 focus:ring-indigo-500" />
        <span className="text-gray-400 text-sm">小时</span>
      </div>
      <div>
        <div className="text-gray-400 text-sm mb-2">还想说什么？</div>
        <textarea value={feedback} onChange={e => onFeedbackChange(e.target.value)} disabled={disabled} placeholder="例如：这部分内容偏难 / 练习不够 / 希望加速..." className="w-full bg-gray-700 text-white rounded-lg px-4 py-3 h-20 resize-none outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-500 text-sm" />
      </div>
      <button onClick={onSubmit} disabled={disabled} className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-xl py-3 font-medium transition-colors text-sm">
        提交打卡
      </button>
    </div>
  );
};