import { useEffect, useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { apiGet, apiDownloadICS } from '../services/api';
import { PlanOverview } from '../components/learn/PlanOverview';
import { useAuth } from '../hooks/useAuth';
import type { StudyPlan, TaskItem } from '../types';
import { normalizePlan, getTasksForDay } from '../utils/taskUtils';

export default function PlanViewPage() {
  const { userId } = useAuth();
  const { planId } = useParams<{ planId?: string }>();
  const { currentPlan, currentPlanId, todayCheckedIds, todayCheckin, toggleTodayTask, setTodayCheckin, setTodayCheckedIds } = useAppStore();
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const targetPlanId = planId || currentPlanId || 'latest';

  useEffect(() => {
    if (!userId) return;
    if (currentPlan && (currentPlan.plan_id === targetPlanId || targetPlanId === 'latest')) {
      setPlan(currentPlan);
      setLoading(false);
    } else {
      setLoading(true);
      setError('');
      const url = targetPlanId === 'latest'
        ? `/v1/learn/plan/latest?user_id=${userId}`
        : `/v1/learn/plan/${targetPlanId}`;
      apiGet<StudyPlan>(url)
        .then(data => {
          const normalized = normalizePlan(data);
          setPlan(normalized);
        })
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [targetPlanId, currentPlan, userId]);

  useEffect(() => {
    if (!userId) return;
    apiGet<any>(`/v1/progress/checkin/today/${userId}?plan_id=${targetPlanId}`)
      .then(data => {
        setTodayCheckin(data);
        if (data.checked_in && data.tasks_completed) {
          setTodayCheckedIds(data.tasks_completed);
        }
      })
      .catch(() => {});
  }, [targetPlanId, userId, setTodayCheckin, setTodayCheckedIds]);

  const todaysTasks = useMemo<TaskItem[]>(() => {
    if (!plan) return [];
    const today = new Date();
    const dayOfPlan = Math.max(1, Math.ceil((today.getTime() - new Date(plan.created_at).getTime()) / 86400000) + 1);
    const tasks = getTasksForDay(plan.daily_tasks, dayOfPlan);
    return tasks.length > 0 ? tasks : plan.daily_tasks.slice(0, 3);
  }, [plan]);

  const [downloading, setDownloading] = useState(false);

  const checkedIdsSet = useMemo(() => new Set(todayCheckedIds), [todayCheckedIds]);

  const handleDownloadICS = async () => {
    if (!plan) return;
    setDownloading(true);
    try {
      await apiDownloadICS(plan.plan_id);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : '下载失败');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-950">
        <div className="flex items-center gap-2 text-gray-400 text-lg">
          <svg className="h-5 w-5 animate-spin text-indigo-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          加载计划中...
        </div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-950 gap-4">
        <div className="text-6xl">📋</div>
        <h3 className="text-gray-300 text-lg font-medium">暂无学习计划</h3>
        <p className="text-gray-500 text-sm max-w-md text-center">
          请先在「对话规划」页面创建你的学习计划。输入学习目标，AI 将为你生成个性化学习路径。
        </p>
        <a href="/learn" className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl px-6 py-3 font-medium transition-colors text-sm">
          去创建计划
        </a>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-950 p-6 space-y-6">
      {/* 今日任务 */}
      {todaysTasks.length > 0 && (
        <div className="bg-gradient-to-br from-indigo-900/50 to-purple-900/50 rounded-xl p-5 border border-indigo-700/50">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>📌</span> 今日任务
              <span className="text-sm font-normal text-indigo-300">
                ({checkedIdsSet.size}/{todaysTasks.length} 已完成)
              </span>
            </h2>
            <Link
              to="/learn/today"
              className="text-sm text-indigo-300 hover:text-indigo-200 transition-colors"
            >
              {todayCheckin?.checked_in ? '查看打卡 →' : '去打卡 →'}
            </Link>
          </div>
          <div className="space-y-2">
            {todaysTasks.slice(0, 3).map((task) => {
              const isChecked = checkedIdsSet.has(task.id);
              return (
                <div
                  key={task.id}
                  className={`flex items-start gap-3 p-3 rounded-lg transition-colors cursor-pointer ${
                    isChecked
                      ? 'bg-emerald-900/30 border border-emerald-700/40'
                      : 'bg-gray-800/60 border border-gray-700/50 hover:bg-gray-700/60'
                  }`}
                  onClick={() => !todayCheckin?.checked_in && toggleTodayTask(task.id)}
                >
                  <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs flex-shrink-0 ${
                    isChecked ? 'bg-emerald-500 text-white' : 'bg-gray-600 text-gray-400'
                  }`}>
                    {isChecked ? '✓' : '•'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm ${isChecked ? 'text-gray-400 line-through' : 'text-white'}`}>
                      {task.title}
                    </div>
                  </div>
                  <span className="text-gray-500 text-xs flex-shrink-0">{task.est_hours}h</span>
                </div>
              );
            })}
          </div>
          {todayCheckin?.checked_in && (
            <div className="mt-4 pt-4 border-t border-indigo-700/30 flex items-center gap-2">
              <span className="text-emerald-400">✅</span>
              <span className="text-sm text-emerald-300">今日已打卡 · 完成度 {todayCheckin.completion}% · {todayCheckin.hours} 小时</span>
            </div>
          )}
        </div>
      )}

      {/* 计划信息栏 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <span>📅</span> 学习计划看板
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            {plan.total_weeks} 周 · {plan.milestones?.length || 0} 个阶段 · 共 {plan.daily_tasks?.length || 0} 个任务
          </p>
        </div>
        <button
          onClick={handleDownloadICS}
          disabled={downloading}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
        >
          {downloading ? (
            <svg className="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <span>📥</span>
          )}
          下载日历(.ics)
        </button>
      </div>

      <PlanOverview plan={plan} />
    </div>
  );
}
