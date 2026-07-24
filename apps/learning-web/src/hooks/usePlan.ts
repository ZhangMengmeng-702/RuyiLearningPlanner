import { useState, useEffect } from 'react';
import type { StudyPlan } from '../types';
import { apiGet } from '../services/api';
import { normalizePlan } from '../utils/taskUtils';

export function usePlan(planId: string) {
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    setError('');
    apiGet<StudyPlan>(`/v1/learn/plan/${planId}`)
      .then(data => setPlan(normalizePlan(data)))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [planId]);

  return { plan, loading, error };
}