import { useState, useEffect, useRef } from 'react';
import { useAppStore } from '../store/appStore';
import { apiGet, apiPost } from '../services/api';
import { LearningChat } from '../components/learn/LearningChat';
import { useLearningChat } from '../hooks/useLearningChat';
import { useAuth } from '../hooks/useAuth';
import type { ProfileData, ChatMessage } from '../types';

export default function LearnChatPage() {
  const { userId } = useAuth();
  const {
    profile,
    setProfile,
    useMock,
    setUseMock,
    sessionId,
    setSessionId,
    setMessages,
    setCurrentPlan,
  } = useAppStore();

  const { messages, loading, sendMessage, stop, clearMessages } = useLearningChat(userId);

  const [profileLoading, setProfileLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [input, setInput] = useState('');
  const [profileForm, setProfileForm] = useState({
    goal: 'Python数据分析',
    current_level: 'beginner' as 'beginner' | 'intermediate' | 'advanced',
    hours_per_week: 10,
    preference: 'hands-on' as 'video' | 'reading' | 'hands-on',
  });
  const [saving, setSaving] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!userId) return;
    apiGet<ProfileData>(`/v1/profile/${userId}`)
      .then(data => {
        setProfile(data);
        if (data.profile?.current_level) {
          setProfileForm({
            goal: data.profile.goal || 'Python数据分析',
            current_level: data.profile.current_level as any,
            hours_per_week: data.profile.hours_per_week || 10,
            preference: data.profile.preference as any || 'hands-on',
          });
        }
        if (!data.profile?.is_complete) {
          setShowProfile(true);
        }
      })
      .catch(() => {})
      .finally(() => setProfileLoading(false));
  }, [userId]);

  // 从后端加载历史消息
  useEffect(() => {
    if (!userId || useMock) return;
    
    let cancelled = false;
    
    const loadHistory = async () => {
      setHistoryLoading(true);
      try {
        // 先获取用户会话列表
        const sessionList: any = await apiGet('/v1/learn/session/list');
        const sessions = sessionList.sessions || [];
        
        if (!cancelled && sessions.length > 0) {
          // 使用最近的一个会话
          const latestSession = sessions[0];
          const sid = latestSession.session_id;
          setSessionId(sid);
          
          // 获取该会话的消息
          const msgData: any = await apiGet(`/v1/learn/session/${sid}/messages?limit=100`);
          const msgs = (msgData.messages || [])
            .filter((m: any) => m.role === 'user' || m.role === 'assistant')
            .map((m: any) => ({
              role: m.role,
              content: m.content,
            }));
          
          if (!cancelled && msgs.length > 0) {
            setMessages(msgs);
          }
          
          // 如果会话有关联的计划，也加载计划
          if (latestSession.plan_id) {
            try {
              const plan: any = await apiGet(`/v1/learn/plan/${latestSession.plan_id}`);
              if (!cancelled && plan && plan.plan_id) {
                setCurrentPlan(plan);
              }
            } catch {}
          }
        }
      } catch (e) {
        console.error('加载历史消息失败:', e);
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    };
    
    loadHistory();
    
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, useMock]);

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      await apiPost(`/v1/profile/${userId}`, profileForm);
      const updated = await apiGet<ProfileData>(`/v1/profile/${userId}`);
      setProfile(updated);
      setShowProfile(false);
    } finally {
      setSaving(false);
    }
  };

  const handleSend = () => {
    if (!input.trim() || loading) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const profileComplete = profile?.profile?.is_complete ?? false;

  return (
    <div className="flex flex-col h-full bg-gray-950">
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🎯</span>
          <div>
            <h2 className="text-white font-semibold text-base">对话规划</h2>
            <p className="text-gray-500 text-xs">AI 智能生成个性化学习路径</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {profileComplete && (
            <button
              onClick={() => setShowProfile(s => !s)}
              className="text-xs text-gray-400 hover:text-indigo-400 transition-colors"
            >
              {showProfile ? '隐藏画像' : '学习画像'}
            </button>
          )}
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={useMock}
              onChange={e => setUseMock(e.target.checked)}
              className="accent-indigo-500"
            />
            <span className="text-xs text-gray-400">Mock 模式</span>
          </label>
        </div>
      </div>

      {showProfile && !profileLoading && (
        <div className="px-6 py-4 bg-gray-900/50 border-b border-gray-800 max-h-[50vh] overflow-y-auto">
          <h3 className="text-white font-medium mb-4 text-sm">完善你的学习画像</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-gray-300 text-xs mb-2">学习目标</label>
              <input
                type="text"
                value={profileForm.goal}
                onChange={e => setProfileForm(f => ({ ...f, goal: e.target.value }))}
                placeholder="例如：学会Python数据分析"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="block text-gray-300 text-xs mb-2">当前水平</label>
              <div className="flex gap-2 flex-wrap">
                {[
                  { value: 'beginner', label: '零基础' },
                  { value: 'intermediate', label: '有一定基础' },
                  { value: 'advanced', label: '已入门，想进阶' },
                ].map(level => (
                  <button
                    key={level.value}
                    onClick={() => setProfileForm(f => ({ ...f, current_level: level.value as any }))}
                    className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
                      profileForm.current_level === level.value
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {level.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-gray-300 text-xs mb-2">每周可投入时间</label>
              <div className="flex gap-2 flex-wrap">
                {[5, 10, 15, 20].map(hours => (
                  <button
                    key={hours}
                    onClick={() => setProfileForm(f => ({ ...f, hours_per_week: hours }))}
                    className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
                      profileForm.hours_per_week === hours
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {hours}小时/周
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-gray-300 text-xs mb-2">偏好学习方式</label>
              <div className="flex gap-2 flex-wrap">
                {[
                  { value: 'video', label: '视频教程' },
                  { value: 'reading', label: '文档阅读' },
                  { value: 'hands-on', label: '边做边学' },
                ].map(pref => (
                  <button
                    key={pref.value}
                    onClick={() => setProfileForm(f => ({ ...f, preference: pref.value as any }))}
                    className={`px-4 py-1.5 rounded-full text-xs font-medium transition-colors ${
                      profileForm.preference === pref.value
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {pref.label}
                  </button>
                ))}
              </div>
            </div>
            <button
              onClick={handleSaveProfile}
              disabled={saving}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900 disabled:cursor-not-allowed text-white rounded-lg py-2.5 font-medium transition-colors text-sm"
            >
              {saving ? '保存中...' : '保存画像'}
            </button>
          </div>
        </div>
      )}

      <LearningChat messages={messages} loading={loading} />

      <div className="px-4 py-3 border-t border-gray-800 bg-gray-950">
        <div className="flex items-end gap-3 max-w-4xl mx-auto">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的学习目标，例如：我想用3个月学会Python数据分析..."
            rows={1}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-2xl px-4 py-3 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none max-h-32"
          />
          <div className="flex gap-2">
            {loading && (
              <button
                onClick={stop}
                className="bg-red-600 hover:bg-red-700 text-white rounded-xl px-4 py-3 font-medium transition-colors text-sm flex-shrink-0"
                title="暂停生成"
              >
                ⏸ 暂停
              </button>
            )}
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-xl px-4 py-3 font-medium transition-colors text-sm flex-shrink-0"
                title="清除对话"
              >
                🗑 清除
              </button>
            )}
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 font-medium transition-colors text-sm flex-shrink-0"
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
