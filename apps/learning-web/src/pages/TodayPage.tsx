import React, { useEffect, useState } from 'react';
import type { DailyTask, StudyPlan } from '../types';

interface CheckinPayload {
  user_id: string;
  plan_id: string;
  day: number;
  tasks_completed: string[];
  difficulty_rating: number;
  completion_pct: number;
  time_spent_hours: number;
  feedback_text: string;
}

export default function TodayPage() {
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [todaysTasks, setTodaysTasks] = useState<DailyTask[]>([]);
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set());
  const [difficulty, setDifficulty] = useState(3);
  const [completion, setCompletion] = useState(50);
  const [hours, setHours] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    // 获取计划 + 今日任务
    const planId = new URLSearchParams(window.location.search).get('plan_id') || 'latest';
    fetch(`http://localhost:8000/api/v1/learn/plan/${planId}`)
      .then(r => r.json())
      .then(data => {
        setPlan(data);
        const today = new Date();
        const dayOfPlan = Math.ceil((today.getTime() - new Date(data.created_at).getTime()) / 86400000) + 1;
        const tasks = (data.daily_tasks || []).filter((t: DailyTask) => t.day === dayOfPlan || t.day === 1);
        setTodaysTasks(tasks.length > 0 ? tasks : (data.daily_tasks || []).slice(0, 3));
      });
    // 获取进度统计
    fetch(`http://localhost:8000/api/v1/progress/stats/demo_user?plan_id=${planId}`)
      .then(r => r.json()).then(d => setStats(d)).catch(() => {});
  }, []);

  const handleCheckin = async () => {
    const payload: CheckinPayload = {
      user_id: 'demo_user',
      plan_id: plan?.plan_id || 'latest',
      day: todaysTasks[0]?.day || 1,
      tasks_completed: Array.from(checkedIds),
      difficulty_rating: difficulty,
      completion_pct: completion,
      time_spent_hours: hours,
      feedback_text: feedback,
    };
    const resp = await fetch('http://localhost:8000/api/v1/progress/checkin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (resp.ok) {
      setSubmitted(true);
      setStats(prev => prev ? {
        ...prev,
        total_days: (prev.total_days || 0) + 1,
        streak: (prev.streak || 0) + 1,
      } : null);
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-950 p-6 space-y-6">
      {/* 进度卡片 */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{stats.total_days || 0}</div>
            <div className="text-gray-400 text-xs mt-1">已完成天数</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-emerald-400">{stats.streak || 0}</div>
            <div className="text-gray-400 text-xs mt-1">连续打卡</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-indigo-400">{stats.avg_completion_pct || 0}%</div>
            <div className="text-gray-400 text-xs mt-1">平均完成率</div>
          </div>
          <div className="bg-gray-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-amber-400">{stats.total_hours || 0}</div>
            <div className="text-gray-400 text-xs mt-1">总学习时长(h)</div>
          </div>
        </div>
      )}

      {/* 今日任务 */}
      <div className="bg-gray-800 rounded-xl p-4">
        <h2 className="text-lg font-bold text-white mb-4">📋 今日任务</h2>
        {todaysTasks.length === 0 ? (
          <div className="text-gray-400 text-sm py-8 text-center">今日没有安排任务，休息一天吧！</div>
        ) : (
          <div className="space-y-3">
            {todaysTasks.map((task, i) => (
              <label
                key={i}
                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                  checkedIds.has(task.title) ? 'bg-indigo-900/30 line-through text-gray-400' : 'bg-gray-700/50 hover:bg-gray-700'
                }`}
              >
                <input
                  type="checkbox"
                  checked={checkedIds.has(task.title)}
                  onChange={() => {
                    const next = new Set(checkedIds);
                    next.has(task.title) ? next.delete(task.title) : next.add(task.title);
                    setCheckedIds(next);
                  }}
                  className="w-4 h-4 rounded accent-indigo-500"
                />
                <div className="flex-1">
                  <div className="text-white text-sm">{task.title}</div>
                  {task.description && <div className="text-gray-400 text-xs mt-0.5">{task.description}</div>}
                </div>
                <div className="text-gray-500 text-xs">{task.est_hours}h</div>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* 打卡表单 */}
      {!submitted && todaysTasks.length > 0 && (
        <div className="bg-gray-800 rounded-xl p-4 space-y-4">
          <h2 className="text-lg font-bold text-white">📝 今日反馈</h2>

          <div>
            <div className="text-gray-400 text-sm mb-2">难度评分</div>
            <div className="flex gap-2">
              {[1,2,3,4,5].map(n => (
                <button
                  key={n}
                  onClick={() => setDifficulty(n)}
                  className={`w-10 h-10 rounded-lg text-lg ${
                    n <= difficulty ? 'bg-amber-500 text-white' : 'bg-gray-700 text-gray-400'
                  }`}
                >{n}</button>
              ))}
              <span className="text-gray-400 text-xs self-center ml-2">
                {['很简单','偏简单','适中','偏难','很难'][difficulty-1]}
              </span>
            </div>
          </div>

          <div>
            <div className="text-gray-400 text-sm mb-2">完成度：{completion}%</div>
            <input
              type="range"
              min="0" max="100" step="10"
              value={completion}
              onChange={e => setCompletion(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>

          <div className="flex gap-4 items-center">
            <div className="text-gray-400 text-sm">实际学习时长：</div>
            <input
              type="number" min="0" max="12" step="0.5" value={hours}
              onChange={e => setHours(Number(e.target.value))}
              className="w-20 bg-gray-700 text-white rounded-lg px-3 py-2 text-center"
            />
            <span className="text-gray-400 text-sm">小时</span>
          </div>

          <div>
            <div className="text-gray-400 text-sm mb-2">还想说什么？</div>
            <textarea
              value={feedback}
              onChange={e => setFeedback(e.target.value)}
              placeholder="例如：这部分内容偏难 / 练习不够 / 希望加速..."
              className="w-full bg-gray-700 text-white rounded-lg px-4 py-3 h-20 resize-none outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-500"
            />
          </div>

          <button
            onClick={handleCheckin}
            disabled={checkedIds.size === 0}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white rounded-xl py-3 font-medium transition-colors"
          >
            ✅ 提交打卡
          </button>
        </div>
      )}

      {submitted && (
        <div className="bg-emerald-900/30 border border-emerald-700 rounded-xl p-6 text-center">
          <div className="text-3xl mb-2">🎉</div>
          <div className="text-emerald-300 text-lg font-medium">打卡成功！</div>
          <div className="text-gray-400 text-sm mt-1">继续坚持，你今天又前进了一步。</div>
        </div>
      )}
    </div>
  );
}