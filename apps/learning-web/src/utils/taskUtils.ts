import type { TaskItem, DailyTask, StudyPlan } from '../types';

export function isGroupedDailyTask(item: any): item is DailyTask {
  return item && Array.isArray(item.tasks) && typeof item.day === 'number';
}

export function flattenDailyTasks(dailyTasks: any[]): TaskItem[] {
  if (!dailyTasks || dailyTasks.length === 0) return [];

  if (isGroupedDailyTask(dailyTasks[0])) {
    const result: TaskItem[] = [];
    dailyTasks.forEach((dt: DailyTask) => {
      dt.tasks.forEach((task, idx) => {
        result.push({
          ...task,
          day: dt.day,
          week: dt.week,
          id: task.id || `task_${dt.day}_${idx}`,
        });
      });
    });
    return result;
  }

  return dailyTasks.map((t, i) => ({
    ...t,
    id: t.id || `task_${i}`,
  }));
}

export function normalizePlan(plan: any): StudyPlan | null {
  if (!plan) return null;
  return {
    ...plan,
    daily_tasks: flattenDailyTasks(plan.daily_tasks || []),
  } as StudyPlan;
}

export function groupTasksByDay(tasks: TaskItem[]): DailyTask[] {
  const dayMap = new Map<number, DailyTask>();

  tasks.forEach((task, index) => {
    const day = task.day ?? 1;
    const week = task.week ?? Math.ceil(day / 7);
    const taskId = task.id || `task_${day}_${index}`;
    const taskWithId: TaskItem = { ...task, id: taskId };

    if (!dayMap.has(day)) {
      dayMap.set(day, {
        day,
        week,
        tasks: [],
      });
    }
    dayMap.get(day)!.tasks.push(taskWithId);
  });

  return Array.from(dayMap.values()).sort((a, b) => a.day - b.day);
}

export function getTasksForDay(tasks: TaskItem[], day: number): TaskItem[] {
  return tasks
    .filter(t => (t.day ?? 1) === day)
    .map((t, i) => ({ ...t, id: t.id || `task_${day}_${i}` }));
}

export function getTasksForWeekRange(
  tasks: TaskItem[],
  weekStart: number,
  weekEnd: number,
): TaskItem[] {
  return tasks
    .filter(t => {
      const week = t.week ?? Math.ceil((t.day ?? 1) / 7);
      return week >= weekStart && week <= weekEnd;
    })
    .map((t, i) => ({ ...t, id: t.id || `task_${i}` }));
}
