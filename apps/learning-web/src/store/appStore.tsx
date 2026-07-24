import { createContext, useContext, useState, useEffect, useMemo, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { ChatMessage, StudyPlan, ProfileData, PrerequisiteCheck, PlanEvaluation, TodayCheckin } from '../types';
import { normalizePlan } from '../utils/taskUtils';

const STORAGE_KEY_PREFIX = 'ruyi_learning_state_';

function getStorageKey(userId: string) {
  return `${STORAGE_KEY_PREFIX}${userId}`;
}

interface AppState {
  userId: string;
  profile: ProfileData | null;
  messages: ChatMessage[];
  currentPlan: StudyPlan | null;
  currentPlanId: string;
  sessionId: string;
  prerequisiteCheck: PrerequisiteCheck | null;
  evaluation: PlanEvaluation | null;
  useMock: boolean;
  todayCheckedIds: string[];
  todayCheckin: TodayCheckin | null;
}

interface AppStore extends AppState {
  setUserId: (id: string) => void;
  setProfile: (p: ProfileData | null) => void;
  setMessages: (m: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
  addMessage: (msg: ChatMessage) => void;
  setCurrentPlan: (p: StudyPlan | null) => void;
  setCurrentPlanId: (id: string) => void;
  setSessionId: (id: string) => void;
  setPrerequisiteCheck: (c: PrerequisiteCheck | null) => void;
  setEvaluation: (e: PlanEvaluation | null) => void;
  setUseMock: (v: boolean) => void;
  resetChat: () => void;
  resetForUser: (userId: string) => void;
  toggleTodayTask: (taskId: string) => void;
  setTodayCheckedIds: (ids: string[]) => void;
  setTodayCheckin: (c: TodayCheckin | null) => void;
}

function getDefaultState(userId: string): AppState {
  return {
    userId,
    profile: null,
    messages: [
      { role: 'assistant', content: '你好！我是你的学习规划助手。在开始之前，请先完善你的**学习画像**，这样我才能为你定制最合适的学习计划。' },
    ],
    currentPlan: null,
    currentPlanId: 'latest',
    sessionId: '',
    prerequisiteCheck: null,
    evaluation: null,
    useMock: false,
    todayCheckedIds: [],
    todayCheckin: null,
  };
}

function loadState(userId: string): AppState {
  try {
    const saved = localStorage.getItem(getStorageKey(userId));
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed.currentPlan) {
        parsed.currentPlan = normalizePlan(parsed.currentPlan);
      }
      return { ...getDefaultState(userId), ...parsed, userId };
    }
  } catch {
    // ignore
  }
  return getDefaultState(userId);
}

function saveState(state: AppState) {
  try {
    localStorage.setItem(getStorageKey(state.userId), JSON.stringify(state));
  } catch {
    // ignore
  }
}

const AppContext = createContext<AppStore | null>(null);

export function AppStoreProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(() => getDefaultState('demo_user'));

  useEffect(() => {
    saveState(state);
  }, [state]);

  const resetForUser = useCallback((userId: string) => {
    setState(loadState(userId));
  }, []);

  const store = useMemo<AppStore>(() => ({
    ...state,
    setUserId: (id) => setState(s => ({ ...s, userId: id })),
    setProfile: (p) => setState(s => ({ ...s, profile: p })),
    setMessages: (m) => setState(s => ({ ...s, messages: typeof m === 'function' ? (m as any)(s.messages) : m })),
    addMessage: (msg) => setState(s => ({ ...s, messages: [...s.messages, msg] })),
    setCurrentPlan: (p) => setState(s => {
      const newPlanId = p?.plan_id || '';
      const planChanged = newPlanId && newPlanId !== s.currentPlanId;
      return {
        ...s,
        currentPlan: normalizePlan(p),
        currentPlanId: newPlanId || s.currentPlanId,
        ...(planChanged ? { todayCheckedIds: [], todayCheckin: null } : {}),
      };
    }),
    setCurrentPlanId: (id) => setState(s => ({ ...s, currentPlanId: id })),
    setSessionId: (id) => setState(s => ({ ...s, sessionId: id })),
    setPrerequisiteCheck: (c) => setState(s => ({ ...s, prerequisiteCheck: c })),
    setEvaluation: (e) => setState(s => ({ ...s, evaluation: e })),
    setUseMock: (v) => setState(s => ({ ...s, useMock: v })),
    resetChat: () => setState(s => ({ ...getDefaultState(s.userId), userId: s.userId })),
    resetForUser,
    toggleTodayTask: (taskId) => setState(s => {
      const ids = new Set(s.todayCheckedIds);
      if (ids.has(taskId)) {
        ids.delete(taskId);
      } else {
        ids.add(taskId);
      }
      const newCheckedIds = Array.from(ids);
      let newPlan = s.currentPlan;
      if (s.currentPlan?.daily_tasks) {
        newPlan = {
          ...s.currentPlan,
          daily_tasks: s.currentPlan.daily_tasks.map(t =>
            t.id === taskId ? { ...t, completed: ids.has(taskId) } : t
          ),
        };
      }
      return { ...s, todayCheckedIds: newCheckedIds, currentPlan: newPlan };
    }),
    setTodayCheckedIds: (ids) => setState(s => {
      const idsSet = new Set(ids);
      let newPlan = s.currentPlan;
      if (s.currentPlan?.daily_tasks) {
        newPlan = {
          ...s.currentPlan,
          daily_tasks: s.currentPlan.daily_tasks.map(t => ({
            ...t,
            completed: idsSet.has(t.id || ''),
          })),
        };
      }
      return { ...s, todayCheckedIds: ids, currentPlan: newPlan };
    }),
    setTodayCheckin: (c) => setState(s => ({ ...s, todayCheckin: c })),
  }), [state, resetForUser]);

  return <AppContext.Provider value={store}>{children}</AppContext.Provider>;
}

export function useAppStore() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppStore must be used within AppStoreProvider');
  return ctx;
}
