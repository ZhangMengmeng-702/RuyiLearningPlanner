// === 学习规划助手 TypeScript 类型定义 ===
// 与后端 JSON Schema 严格对应

export interface Milestone {
  week_start: number;
  week_end: number;
  phase: string;
  description: string;
  objectives: string[];
  task_count: number;
  difficulty: 1 | 2 | 3;
}

export interface DailyTask {
  day: number;
  title: string;
  description: string;
  est_hours: number;
  resource_title?: string;
  resource_url?: string;
  completed?: boolean;
}

export interface PrerequisiteCheck {
  status: 'passed' | 'warning' | 'failed';
  details: { chapter: string; prerequisites: string[]; status: string }[];
  warnings: string[];
}

export interface PlanEvaluation {
  score: number;
  issues: string[];
  suggestions: string[];
}

export interface StudyPlan {
  plan_id: string;
  goal: string;
  user_id: string;
  total_weeks: number;
  created_at: string;
  milestones: Milestone[];
  daily_tasks: DailyTask[];
  prerequisite_check: PrerequisiteCheck;
  evaluation?: PlanEvaluation;
  adjusted?: boolean;
  adjust_reason?: string;
}

export interface CheckinPayload {
  user_id: string;
  plan_id: string;
  day: number;
  tasks_completed: string[];
  difficulty_rating: number;
  completion_pct: number;
  time_spent_hours: number;
  feedback_text: string;
}

export interface ProgressStats {
  total_days: number;
  completed_days: number;
  streak: number;
  avg_completion_pct: number;
  avg_difficulty: number;
  total_hours: number;
  checkins: {
    day: number;
    date: string;
    difficulty: number;
    completion: number;
    hours: number;
    feedback: string;
  }[];
}

export interface ProfileData {
  user_id: string;
  exists: boolean;
  profile?: {
    goal: string;
    current_level: string;
    hours_per_week: number;
    preference: string;
    known_topics: string[];
    is_complete: boolean;
  };
}