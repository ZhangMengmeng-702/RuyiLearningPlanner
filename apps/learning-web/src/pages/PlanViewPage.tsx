import React, { useEffect, useState } from 'react';
import type { StudyPlan, Milestone } from '../types';

export default function PlanViewPage() {
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [expandedWeek, setExpandedWeek] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 从 URL 参数取 plan_id
    const params = new URLSearchParams(window.location.search);
    const planId = params.get('plan_id') || 'latest';
    fetch(`http://localhost:8000/api/v1/learn/plan/${planId}`)
      .then(r => r.json())
      .then(data => { setPlan(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-950">
        <div className="text-gray-400 text-lg animate-pulse">加载计划中...</div>
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-950">
        <div className="text-gray-400 text-lg">暂无学习计划。请先在对话页面创建一个计划。</div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-950 p-6">
      {/* 计划头部 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">{plan.goal}</h1>
        <div className="flex gap-4 text-sm text-gray-400">
          <span>📅 共 {plan.total_weeks} 周</span>
          <span>📌 {plan.milestones?.length || 0} 个阶段</span>
          <span>✅ 前置检查：{plan.prerequisite_check?.status === 'passed' ? '通过' : '需注意'}</span>
          {plan.evaluation && <span>⭐ 质量评分：{plan.evaluation.score}/10</span>}
        </div>
      </div>

      {/* 里程碑卡片列表（替代甘特图） */}
      <div className="space-y-4">
        {(plan.milestones || []).map((ms, i) => (
          <div key={i} className="bg-gray-800 rounded-xl overflow-hidden">
            <button
              onClick={() => setExpandedWeek(expandedWeek === i ? null : i)}
              className="w-full flex items-center justify-between p-4 hover:bg-gray-750 transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold text-lg ${
                  ms.difficulty >= 3 ? 'bg-red-900 text-red-200' :
                  ms.difficulty === 2 ? 'bg-yellow-900 text-yellow-200' :
                  'bg-green-900 text-green-200'
                }`}>
                  {ms.week_start}
                </div>
                <div className="text-left">
                  <div className="text-white font-medium">{ms.phase}</div>
                  <div className="text-gray-400 text-sm">第 {ms.week_start}-{ms.week_end} 周 · {ms.task_count} 个任务 · {'⭐'.repeat(ms.difficulty)}</div>
                </div>
              </div>
              <div className="text-gray-400 text-xl">{expandedWeek === i ? '▾' : '▸'}</div>
            </button>
            {expandedWeek === i && (
              <div className="px-4 pb-4 space-y-3">
                <p className="text-gray-300 text-sm">{ms.description}</p>
                {ms.objectives?.length > 0 && (
                  <div>
                    <div className="text-gray-400 text-xs mb-1">🎯 学习目标：</div>
                    <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
                      {ms.objectives.map((obj, j) => <li key={j}>{obj}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}