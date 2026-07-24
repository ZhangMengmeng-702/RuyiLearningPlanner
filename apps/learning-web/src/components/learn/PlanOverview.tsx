import React from 'react';
import type { StudyPlan, Milestone, TaskItem, TaskResource, TaskExercise } from '../../types';
import { getTasksForWeekRange } from '../../utils/taskUtils';

interface Props {
  plan: StudyPlan;
}

const difficultyColor = (d: number) =>
  d >= 3 ? 'bg-red-900/50 text-red-300 border-red-700/50' :
  d === 2 ? 'bg-yellow-900/50 text-yellow-300 border-yellow-700/50' :
  'bg-green-900/50 text-green-300 border-green-700/50';

const difficultyLabel = (d: number) =>
  d >= 3 ? '困难' : d === 2 ? '中等' : '简单';

const ResourceIcon: Record<string, string> = {
  video: '🎬',
  article: '📄',
  book: '📚',
  course: '🎓',
  other: '📖',
};

function ResourceList({ resources }: { resources?: TaskResource[] }) {
  if (!resources || resources.length === 0) return null;
  return (
    <div className="mt-2 space-y-1">
      <div className="text-gray-500 text-xs">📚 学习资源</div>
      <div className="flex flex-wrap gap-1.5">
        {resources.map((res, i) => (
          <a
            key={i}
            href={res.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-gray-700/50 text-indigo-300 hover:text-indigo-200 hover:bg-gray-700 transition-colors border border-gray-600/50"
            onClick={e => !res.url && e.preventDefault()}
          >
            <span>{ResourceIcon[res.type || 'other'] || '📖'}</span>
            {res.title}
          </a>
        ))}
      </div>
    </div>
  );
}

function ExerciseList({ exercises }: { exercises?: TaskExercise[] }) {
  if (!exercises || exercises.length === 0) return null;
  return (
    <div className="mt-2 space-y-1">
      <div className="text-gray-500 text-xs">✏️ 练习题</div>
      <div className="flex flex-wrap gap-1.5">
        {exercises.map((ex, i) => (
          <a
            key={i}
            href={ex.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs bg-emerald-900/30 text-emerald-300 hover:text-emerald-200 hover:bg-emerald-900/50 transition-colors border border-emerald-700/40"
            onClick={e => !ex.url && e.preventDefault()}
            title={ex.description}
          >
            <span>📝</span>
            {ex.title}
          </a>
        ))}
      </div>
    </div>
  );
}

export const PlanOverview: React.FC<Props> = ({ plan }) => {
  const [expandedWeek, setExpandedWeek] = React.useState<number | null>(null);

  const getMilestoneTasks = (weekStart: number, weekEnd: number): TaskItem[] => {
    return getTasksForWeekRange(plan.daily_tasks, weekStart, weekEnd);
  };

  return (
    <>
      {/* 计划头部 */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">{plan.goal}</h1>
        <div className="flex flex-wrap gap-3 text-sm text-gray-400">
          <span className="inline-flex items-center gap-1 bg-gray-800 rounded-lg px-3 py-1">
            <span className="text-indigo-400">📅</span> 共 {plan.total_weeks} 周
          </span>
          <span className="inline-flex items-center gap-1 bg-gray-800 rounded-lg px-3 py-1">
            <span className="text-indigo-400">📌</span> {plan.milestones?.length || 0} 个阶段
          </span>
          <span className={`inline-flex items-center gap-1 rounded-lg px-3 py-1 ${
            plan.prerequisite_check?.status === 'passed'
              ? 'bg-green-900/30 text-green-400'
              : plan.prerequisite_check?.status === 'warning'
              ? 'bg-yellow-900/30 text-yellow-400'
              : 'bg-red-900/30 text-red-400'
          }`}>
            {plan.prerequisite_check?.status === 'passed' ? '✅' : '⚠️'}
            前置检查：{plan.prerequisite_check?.status === 'passed' ? '通过' : '需注意'}
          </span>
          {plan.evaluation && (
            <span className="inline-flex items-center gap-1 bg-gray-800 rounded-lg px-3 py-1">
              <span className="text-amber-400">⭐</span> 质量评分：{plan.evaluation.score}/10
            </span>
          )}
          {plan.adjusted && (
            <span className="inline-flex items-center gap-1 bg-purple-900/30 text-purple-300 rounded-lg px-3 py-1">
              🔄 已调整
            </span>
          )}
        </div>
        {plan.adjust_reason && (
          <p className="mt-2 text-sm text-gray-500 italic">调整原因：{plan.adjust_reason}</p>
        )}
      </div>

      {/* 里程碑卡片列表 */}
      <div className="space-y-4">
        {(plan.milestones || []).map((ms, i) => {
          const tasks = getMilestoneTasks(ms.week_start, ms.week_end);
          const completedTasks = tasks.filter(t => t.completed).length;
          return (
            <div key={i} className="bg-gray-800/80 rounded-xl overflow-hidden border border-gray-700/50">
              <button
                onClick={() => setExpandedWeek(expandedWeek === i ? null : i)}
                className="w-full flex items-center justify-between p-4 hover:bg-gray-750 transition-colors text-left"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg border ${difficultyColor(ms.difficulty)}`}>
                    {ms.week_start}
                  </div>
                  <div>
                    <div className="text-white font-medium text-base">{ms.phase}</div>
                    <div className="flex items-center gap-3 mt-0.5">
                      <span className="text-gray-400 text-xs">第 {ms.week_start}-{ms.week_end} 周</span>
                      <span className="text-gray-500 text-xs">·</span>
                      <span className="text-gray-400 text-xs">{tasks.length} 个任务</span>
                      <span className="text-gray-500 text-xs">·</span>
                      <span className={`text-xs ${ms.difficulty >= 3 ? 'text-red-400' : ms.difficulty === 2 ? 'text-yellow-400' : 'text-green-400'}`}>
                        {difficultyLabel(ms.difficulty)}
                      </span>
                      {tasks.length > 0 && (
                        <>
                          <span className="text-gray-500 text-xs">·</span>
                          <span className="text-indigo-400 text-xs">{completedTasks}/{tasks.length} 已完成</span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-gray-400 text-xl transition-transform" style={{ transform: expandedWeek === i ? 'rotate(90deg)' : 'rotate(0deg)' }}>
                  ▸
                </div>
              </button>

              {expandedWeek === i && (
                <div className="px-4 pb-4 space-y-4 border-t border-gray-700/50 pt-4">
                  <p className="text-gray-300 text-sm">{ms.description}</p>
                  {ms.objectives?.length > 0 && (
                    <div>
                      <div className="text-gray-400 text-xs font-medium mb-2 uppercase tracking-wide">学习目标</div>
                      <ul className="space-y-1.5">
                        {ms.objectives.map((obj, j) => (
                          <li key={j} className="flex items-start gap-2 text-gray-300 text-sm">
                            <span className="text-indigo-400 mt-0.5">▹</span> {obj}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {tasks.length > 0 && (
                    <div>
                      <div className="text-gray-400 text-xs font-medium mb-2 uppercase tracking-wide">每日任务 ({tasks.length})</div>
                      <div className="space-y-2">
                        {tasks.map((task, j) => (
                          <div key={task.id || j} className={`flex items-start gap-3 p-3 rounded-lg ${task.completed ? 'bg-indigo-900/20 border border-indigo-700/30' : 'bg-gray-700/50 border border-gray-600/30'}`}>
                            <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs flex-shrink-0 ${task.completed ? 'bg-indigo-600 text-white' : 'bg-gray-600 text-gray-400'}`}>
                              {task.completed ? '✓' : j + 1}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className={`text-sm ${task.completed ? 'text-gray-400 line-through' : 'text-white'}`}>{task.title}</div>
                              {task.description && <div className="text-gray-500 text-xs mt-0.5">{task.description}</div>}
                              {task.resource_title && !task.resources && (
                                <a href={task.resource_url || '#'} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 mt-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors" onClick={e => !task.resource_url && e.preventDefault()}>
                                  <span>📖</span> {task.resource_title}
                                </a>
                              )}
                              <ResourceList resources={task.resources} />
                              <ExerciseList exercises={task.exercises} />
                            </div>
                            <span className="text-gray-500 text-xs flex-shrink-0">{task.est_hours}h</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {tasks.length === 0 && (
                    <div className="text-gray-500 text-sm italic py-2">该阶段暂无每日任务，请等待计划生成。</div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 前置依赖检查 */}
      {plan.prerequisite_check?.details?.length > 0 && (
        <div className="mt-8 bg-gray-800/80 rounded-xl p-5 border border-gray-700/50">
          <h3 className="text-white font-semibold text-lg mb-4">前置知识依赖检查</h3>
          <div className="space-y-2">
            {plan.prerequisite_check.details.map((d, i) => (
              <div key={i} className="flex items-center gap-3 text-sm p-2 rounded-lg bg-gray-700/30">
                <span className={d.status === 'covered' ? 'text-green-400' : 'text-red-400'}>{d.status === 'covered' ? '✅' : '❌'}</span>
                <span className="text-gray-300">{d.chapter}</span>
                <span className="text-gray-500">需要：{d.prerequisites.join('、')}</span>
              </div>
            ))}
          </div>
          {plan.prerequisite_check.warnings?.length > 0 && (
            <div className="mt-3 p-3 bg-yellow-900/20 border border-yellow-700/30 rounded-lg">
              <div className="text-yellow-400 text-sm font-medium mb-1">⚠️ 注意事项</div>
              {plan.prerequisite_check.warnings.map((w, i) => <div key={i} className="text-yellow-300/80 text-sm">{w}</div>)}
            </div>
          )}
        </div>
      )}
    </>
  );
};