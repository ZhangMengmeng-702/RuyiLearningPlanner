import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { TaskItem, TaskResource, TaskExercise } from '../../types';

interface Props {
  tasks: TaskItem[];
  checkedIds: Set<string>;
  onToggle: (id: string) => void;
  disabled?: boolean;
}

const ResourceIcon: Record<string, string> = {
  video: '🎬',
  article: '📄',
  book: '📚',
  course: '🎓',
  other: '📖',
};

function ResourceList({ resources }: { resources?: TaskResource[] }) {
  const navigate = useNavigate();
  if (!resources || resources.length === 0) return null;

  const handleClick = (url: string, e: React.MouseEvent) => {
    if (!url) {
      e.preventDefault();
      return;
    }
    if (url.startsWith('/')) {
      e.preventDefault();
      navigate(url);
    }
  };

  return (
    <div className="mt-2 space-y-1">
      <div className="text-gray-400 text-xs font-medium">📚 学习资源</div>
      <div className="flex flex-wrap gap-2">
        {resources.map((res, i) => (
          <a
            key={i}
            href={res.url || '#'}
            target={res.url?.startsWith('http') ? '_blank' : undefined}
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-gray-700/50 text-xs text-indigo-300 hover:text-indigo-200 hover:bg-gray-700 transition-colors border border-gray-600/50"
            onClick={e => handleClick(res.url || '', e)}
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
  const navigate = useNavigate();
  if (!exercises || exercises.length === 0) return null;

  const handleClick = (url: string, e: React.MouseEvent) => {
    if (!url) {
      e.preventDefault();
      return;
    }
    if (url.startsWith('/')) {
      e.preventDefault();
      navigate(url);
    }
  };

  return (
    <div className="mt-2 space-y-1">
      <div className="text-gray-400 text-xs font-medium">✏️ 练习题</div>
      <div className="flex flex-wrap gap-2">
        {exercises.map((ex, i) => (
          <a
            key={i}
            href={ex.url || '#'}
            target={ex.url?.startsWith('http') ? '_blank' : undefined}
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-emerald-900/30 text-xs text-emerald-300 hover:text-emerald-200 hover:bg-emerald-900/50 transition-colors border border-emerald-700/40"
            onClick={e => handleClick(ex.url || '', e)}
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

export const TaskList: React.FC<Props> = ({ tasks, checkedIds, onToggle, disabled = false }) => {
  const navigate = useNavigate();

  const handleResourceClick = (url: string, e: React.MouseEvent) => {
    if (!url) {
      e.preventDefault();
      return;
    }
    if (url.startsWith('/')) {
      e.preventDefault();
      navigate(url);
    }
  };

  if (tasks.length === 0) {
    return (
      <div className="text-gray-400 text-sm py-8 text-center">
        <div className="text-4xl mb-2">☕</div>
        今日没有安排任务，休息一天吧！
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tasks.map((task) => (
        <label
          key={task.id}
          className={`flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors border ${
            checkedIds.has(task.id)
              ? 'bg-indigo-900/20 border-indigo-700/30'
              : 'bg-gray-700/50 border-gray-600/30 hover:bg-gray-700'
          }`}
        >
          <input
            type="checkbox"
            checked={checkedIds.has(task.id)}
            onChange={() => onToggle(task.id)}
            disabled={disabled}
            className="mt-0.5 w-4 h-4 rounded accent-indigo-500"
          />
          <div className="flex-1 min-w-0">
            <div className={`text-sm ${checkedIds.has(task.id) ? 'text-gray-400 line-through' : 'text-white'}`}>
              {task.title}
            </div>
            {task.description && <div className="text-gray-500 text-xs mt-0.5">{task.description}</div>}
            {task.resource_title && !task.resources && (
              <a
                href={task.resource_url || '#'}
                target={task.resource_url?.startsWith('http') ? '_blank' : undefined}
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                onClick={e => handleResourceClick(task.resource_url || '', e)}
              >
                <span>📖</span> {task.resource_title}
              </a>
            )}
            <ResourceList resources={task.resources} />
            <ExerciseList exercises={task.exercises} />
          </div>
          <span className="text-gray-500 text-xs flex-shrink-0 mt-0.5">{task.est_hours}h</span>
        </label>
      ))}
    </div>
  );
};