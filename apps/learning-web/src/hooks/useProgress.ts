import { useState, useEffect, useCallback, useMemo } from 'react';
import type { ProgressStats } from '../types';
import { apiGet, apiPost } from '../services/api';
import { useAppStore } from '../store/appStore';

export function useProgress(userId: string, planId: string) {
  const {
    todayCheckedIds,
    todayCheckin,
    setTodayCheckin,
    setTodayCheckedIds,
    toggleTodayTask,
  } = useAppStore();

  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(() => {
    setLoading(true);
    apiGet<ProgressStats>(`/v1/progress/stats/${userId}?plan_id=${planId}`)
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userId, planId]);

  const fetchTodayCheckin = useCallback(() => {
    apiGet<any>(`/v1/progress/checkin/today/${userId}?plan_id=${planId}`)
      .then(data => {
        setTodayCheckin(data);
        if (data.checked_in && data.tasks_completed) {
          setTodayCheckedIds(data.tasks_completed);
        }
      })
      .catch(() => {});
  }, [userId, planId]);

  useEffect(() => {
    fetchStats();
    fetchTodayCheckin();
  }, [fetchStats, fetchTodayCheckin]);

  const checkin = async (payload: {
    user_id: string;
    plan_id: string;
    day: number;
    tasks_completed: string[];
    difficulty_rating: number;
    completion_pct: number;
    time_spent_hours: number;
    feedback_text: string;
  }) => {
    const result = await apiPost('/v1/progress/checkin', payload);
    fetchStats();
    fetchTodayCheckin();
    return result;
  };

  const checkedIdsSet = useMemo(() => new Set(todayCheckedIds), [todayCheckedIds]);

  return {
    stats,
    loading,
    checkin,
    todayCheckin,
    todayCheckedIds: checkedIdsSet,
    toggleTask: toggleTodayTask,
    refetchTodayCheckin: fetchTodayCheckin,
  };
}
