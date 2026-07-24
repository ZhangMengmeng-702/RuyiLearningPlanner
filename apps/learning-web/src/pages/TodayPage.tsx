import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useAppStore } from '../store/appStore';
import { apiGet, apiPost } from '../services/api';
import { TaskList } from '../components/learn/TaskList';
import { ProgressRing } from '../components/learn/ProgressRing';
import { FeedbackForm } from '../components/learn/FeedbackForm';
import { useAuth } from '../hooks/useAuth';
import type { TaskItem, StudyPlan, ProgressStats } from '../types';
import { getTasksForDay, normalizePlan } from '../utils/taskUtils';

export default function TodayPage() {
  const { userId: authUserId } = useAuth();
  const { currentPlan, currentPlanId, todayCheckedIds, todayCheckin, toggleTodayTask, setTodayCheckin, setTodayCheckedIds, setCurrentPlan } = useAppStore();
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [adjustedInfo, setAdjustedInfo] = useState<{ adjusted: boolean; reason: string } | null>(null);

  const targetPlanId = currentPlanId || 'latest';

  useEffect(() => {
    if (!authUserId) return;
    if (currentPlan && (currentPlan.plan_id === targetPlanId || targetPlanId === 'latest')) {
      setPlan(currentPlan);
      setLoading(false);
    } else {
      setLoading(true);
      const url = targetPlanId === 'latest'
        ? `/v1/learn/plan/latest?user_id=${authUserId}`
        : `/v1/learn/plan/${targetPlanId}`;
      apiGet<StudyPlan>(url)
        .then(data => setPlan(normalizePlan(data)))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [targetPlanId, currentPlan, authUserId]);

  useEffect(() => {
    if (!authUserId) return;
    apiGet<ProgressStats>(`/v1/progress/stats/${authUserId}?plan_id=${targetPlanId}`)
      .then(setStats)
      .catch(() => {});
  }, [targetPlanId, authUserId]);

  useEffect(() => {
    if (!authUserId) return;
    apiGet<any>(`/v1/progress/checkin/today/${authUserId}?plan_id=${targetPlanId}`)
      .then(data => {
        setTodayCheckin(data);
        if (data.checked_in && data.tasks_completed) {
          setTodayCheckedIds(data.tasks_completed);
        }
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetPlanId, authUserId]);

  const [todaysTasks, setTodaysTasks] = useState<TaskItem[]>([]);
  const [difficulty, setDifficulty] = useState(3);
  const [hours, setHours] = useState(0);
  const [feedback, setFeedback] = useState('');

  useEffect(() => {
    if (!plan?.daily_tasks) return;
    const today = new Date();
    const dayOfPlan = Math.max(1, Math.ceil((today.getTime() - new Date(plan.created_at).getTime()) / 86400000) + 1);
    const tasks = getTasksForDay(plan.daily_tasks, dayOfPlan);
    setTodaysTasks(tasks.length > 0 ? tasks : plan.daily_tasks.slice(0, 3).map((t, i) => ({ ...t, id: t.id || `task_${i}` })));
    
    // 如果计划已被调整，显示调整信息
    if (plan.adjusted && plan.adjust_reason) {
      setAdjustedInfo({ adjusted: true, reason: plan.adjust_reason });
    }
  }, [plan]);

  const checkedIdsSet = useMemo(() => new Set(todayCheckedIds), [todayCheckedIds]);

  const completion = useMemo(() => {
    if (todaysTasks.length === 0) return 0;
    return Math.round((checkedIdsSet.size / todaysTasks.length) * 100);
  }, [checkedIdsSet, todaysTasks]);

  const submitted = todayCheckin?.checked_in ?? false;

  const handleCheckin = async () => {
    if (!authUserId) return;
    try {
      const result: any = await apiPost('/v1/progress/checkin', {
        user_id: authUserId,
        plan_id: targetPlanId,
        day: todaysTasks[0]?.day || 1,
        tasks_completed: Array.from(todayCheckedIds),
        difficulty_rating: difficulty,
        completion_pct: completion,
        time_spent_hours: hours,
        feedback_text: feedback,
      });
      const data = await apiGet<any>(`/v1/progress/checkin/today/${authUserId}?plan_id=${targetPlanId}`);
      setTodayCheckin(data);
      const statsData = await apiGet<ProgressStats>(`/v1/progress/stats/${authUserId}?plan_id=${targetPlanId}`);
      setStats(statsData);

      // 如果计划被自动调整了，显示提示并重新加载计划
      if (result?.adjusted) {
        setAdjustedInfo({ adjusted: true, reason: result.adjust_reason || '计划已自动调整' });
        // 重新加载计划数据
        const url = targetPlanId === 'latest'
          ? `/v1/learn/plan/latest?user_id=${authUserId}`
          : `/v1/learn/plan/${targetPlanId}`;
        const newPlanData = await apiGet<StudyPlan>(url);
        const normalized = normalizePlan(newPlanData);
        setPlan(normalized);
        setCurrentPlan(normalized);
        // 重新计算今日任务
        if (normalized?.daily_tasks) {
          const today = new Date();
          const dayOfPlan = Math.max(1, Math.ceil((today.getTime() - new Date(normalized.created_at).getTime()) / 86400000) + 1);
          const tasks = getTasksForDay(normalized.daily_tasks, dayOfPlan);
          setTodaysTasks(tasks.length > 0 ? tasks : normalized.daily_tasks.slice(0, 3).map((t, i) => ({ ...t, id: t.id || `task_${i}` })));
        }
      }
    } catch (err: any) {
      alert(err?.message || '打卡失败');
    }
  };

  return (
    <div className="h-full overflow-y-auto bg-gray-950 p-6 space-y-6">
      {/* 进度统计 */}
      <div className="bg-gray-800/80 rounded-xl p-6 border border-gray-700/50">
        <h2 className="text-lg font-bold text-white mb-4">学习进度</h2>
        <div className="flex items-center justify-around">
          <ProgressRing
            percentage={stats?.avg_completion_pct || 0}
            color="#6366f1"
            label={`${stats?.avg_completion_pct || 0}%`}
            sublabel="平均完成率"
          />
          <div className="grid grid-cols-1 gap-4">
            <div className="bg-gray-700/50 rounded-xl px-5 py-3 text-center">
              <div className="text-2xl font-bold text-white">{stats?.total_days || 0}</div>
              <div className="text-gray-400 text-xs mt-0.5">已完成天数</div>
            </div>
            <div className="bg-gray-700/50 rounded-xl px-5 py-3 text-center">
              <div className="text-2xl font-bold text-emerald-400">{stats?.streak || 0}</div>
              <div className="text-gray-400 text-xs mt-0.5">连续打卡</div>
            </div>
            <div className="bg-gray-700/50 rounded-xl px-5 py-3 text-center">
              <div className="text-2xl font-bold text-amber-400">{stats?.total_hours || 0}</div>
              <div className="text-gray-400 text-xs mt-0.5">总学习时长(h)</div>
            </div>
          </div>
        </div>
      </div>

      {/* 今日任务 */}
      <div className="bg-gray-800/80 rounded-xl p-5 border border-gray-700/50">
        <h2 className="text-lg font-bold text-white mb-2">
          今日任务
          <span className="text-sm font-normal text-gray-400 ml-2">
            ({checkedIdsSet.size}/{todaysTasks.length} 已完成)
          </span>
        </h2>
        {adjustedInfo?.adjusted && (
          <div className="mb-3 p-2 bg-indigo-900/20 border border-indigo-700/30 rounded-lg">
            <div className="text-indigo-300 text-xs font-medium">📊 计划已自适应调整</div>
            <div className="text-gray-400 text-xs mt-0.5">{adjustedInfo.reason}</div>
          </div>
        )}
        <TaskList
          tasks={todaysTasks}
          checkedIds={checkedIdsSet}
          onToggle={toggleTodayTask}
          disabled={submitted}
        />
      </div>

      {/* 打卡反馈 */}
      {!submitted && todaysTasks.length > 0 && (
        <FeedbackForm
          difficulty={difficulty}
          completion={completion}
          hours={hours}
          feedback={feedback}
          onDifficultyChange={setDifficulty}
          onCompletionChange={() => {}}
          onHoursChange={setHours}
          onFeedbackChange={setFeedback}
          onSubmit={handleCheckin}
          disabled={checkedIdsSet.size === 0}
          readOnlyCompletion
        />
      )}

      {submitted && (
        <div className="bg-emerald-900/20 border border-emerald-700/30 rounded-xl p-6 text-center">
          <div className="text-4xl mb-3">🎉</div>
          <div className="text-emerald-300 text-lg font-medium">打卡成功！</div>
          <div className="text-gray-400 text-sm mt-1">继续坚持，你今天又前进了一步。</div>
          {todayCheckin && (
            <div className="mt-4 text-sm text-gray-400">
              <div>完成度：{todayCheckin.completion}%</div>
              <div>学习时长：{todayCheckin.hours} 小时</div>
            </div>
          )}
          <div className="mt-4 p-3 bg-indigo-900/20 border border-indigo-700/30 rounded-lg text-left">
            <div className="text-indigo-300 text-sm font-medium mb-1">📊 计划自适应</div>
            {adjustedInfo?.adjusted ? (
              <>
                <div className="text-gray-300 text-xs mb-1">{adjustedInfo.reason}</div>
                <div className="text-gray-500 text-xs">后续任务已根据你的完成情况动态调整，明天的任务会自动更新。</div>
              </>
            ) : (
              <div className="text-gray-400 text-xs">
                系统会持续追踪你的学习进度。如果连续几天提前完成或任务难度不合适，
                会自动调整后续任务量和难度，让学习计划始终贴合你的节奏。
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}