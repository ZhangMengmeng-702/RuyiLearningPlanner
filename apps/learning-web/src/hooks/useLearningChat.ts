import { useState, useCallback, useRef } from 'react';
import { useAppStore } from '../store/appStore';
import type { StudyPlan, PrerequisiteCheck, PlanEvaluation } from '../types';
import { apiPostSSE, apiDeleteSession } from '../services/api';

function mockSSE(
  userMsg: string,
  onToken: (t: string) => void,
  onPlan: (p: StudyPlan) => void,
  onPrerequisite?: (check: PrerequisiteCheck) => void,
  onEvaluation?: (evaluation: PlanEvaluation) => void,
) {
  const mockTexts = [
    '正在检查用户画像...\n',
    '已检索到相关知识库内容。\n',
    '正在生成个性化学习计划...\n',
    '正在检查前置依赖...\n',
    '正在评估计划质量...\n',
    '计划生成完成！\n',
  ];
  let textIdx = 0;
  let charIdx = 0;

  return new Promise<void>((resolve) => {
    const timer = setInterval(() => {
      if (textIdx < mockTexts.length) {
        const currentText = mockTexts[textIdx];
        if (charIdx < currentText.length) {
          onToken(currentText[charIdx]);
          charIdx++;
        } else {
          if (textIdx === 3) {
            onPrerequisite?.({
              status: 'passed',
              details: [],
              warnings: [],
            });
          }
          if (textIdx === 4) {
            onEvaluation?.({
              score: 8,
              issues: [],
              suggestions: ['建议增加更多实战项目'],
            });
          }
          textIdx++;
          charIdx = 0;
        }
      } else {
        clearInterval(timer);
        onPlan({
          plan_id: `plan_mock_${Date.now()}`,
          goal: userMsg,
          user_id: 'demo_user',
          total_weeks: 12,
          created_at: new Date().toISOString(),
          milestones: [
            { week_start: 1, week_end: 2, phase: 'Python基础语法', description: '变量、数据类型、条件判断、循环结构', objectives: ['掌握基础语法', '能写简单脚本'], task_count: 15, difficulty: 1 },
            { week_start: 3, week_end: 4, phase: '函数与模块', description: '函数定义、参数传递、模块导入', objectives: ['理解函数作用域', '能组织多文件项目'], task_count: 8, difficulty: 2 },
            { week_start: 5, week_end: 6, phase: 'NumPy与Pandas入门', description: '数组操作、DataFrame基础', objectives: ['能处理CSV数据', '能做基础统计分析'], task_count: 8, difficulty: 2 },
            { week_start: 7, week_end: 8, phase: '数据可视化', description: 'Matplotlib、Seaborn基础图表', objectives: ['能绘制常见图表'], task_count: 6, difficulty: 2 },
            { week_start: 9, week_end: 10, phase: '综合实战项目', description: '真实数据集完整分析', objectives: ['能独立完成数据分析项目'], task_count: 4, difficulty: 3 },
            { week_start: 11, week_end: 12, phase: '复习与总结', description: '回顾所有知识点', objectives: ['形成完整的知识体系'], task_count: 4, difficulty: 1 },
          ],
          daily_tasks: [
            { id: 't1_1', day: 1, week: 1, title: '安装Python环境 + Hello World', est_hours: 1.0, description: '安装Python并编写第一个程序',
              resources: [
                { title: 'Python官方教程-入门', url: 'https://docs.python.org/zh-cn/3/tutorial/', type: 'course' },
                { title: '廖雪峰Python教程', url: 'https://www.liaoxuefeng.com/wiki/1016959663602400', type: 'article' },
                { title: '黑马程序员Python入门视频', url: 'https://www.bilibili.com/video/BV1qW4y1a7fU?p=10', type: 'video' },
              ],
              exercises: [
                { title: '基础语法练习题', url: '/learn/kb/python_learning_path/01-基础语法', description: '变量、数据类型、输入输出练习' },
              ]
            },
            { id: 't1_2', day: 1, week: 1, title: '认识变量与数据类型', est_hours: 1.5, description: '学习整数、浮点数、字符串、布尔值',
              resources: [
                { title: '菜鸟教程-Python变量', url: 'https://www.runoob.com/python3/python3-basic-syntax.html', type: 'article' },
                { title: '数据类型详解', url: '/learn/kb/python_learning_path/01-基础语法', type: 'article' },
                { title: '尚硅谷-数据类型视频', url: 'https://www.bilibili.com/video/BV1wD4y1o7AS?p=15', type: 'video' },
              ],
              exercises: [
                { title: '变量与数据类型练习', url: '/learn/kb/exercises/01-变量练习', description: '包含20道基础练习题' },
                { title: '菜鸟在线练习', url: 'https://www.runoob.com/python3/python3-tutorial.html', description: '在线交互式练习' },
              ]
            },
            { id: 't1_3', day: 1, week: 1, title: '基本输入输出', est_hours: 0.5, description: 'print() 和 input() 的使用',
              resources: [
                { title: 'Python输入输出教程', url: 'https://www.runoob.com/python3/python3-inputoutput.html', type: 'article' },
                { title: '廖雪峰-输入输出', url: 'https://www.liaoxuefeng.com/wiki/1016959663602400/1017063413908976', type: 'article' },
                { title: '黑马程序员-输入输出视频', url: 'https://www.bilibili.com/video/BV1qW4y1a7fU?p=17', type: 'video' },
              ],
              exercises: [
                { title: '输入输出练习', url: '/learn/kb/exercises/01-变量练习', description: 'print和input函数练习' },
                { title: '菜鸟在线练习', url: 'https://www.runoob.com/python3/python3-tutorial.html', description: '在线交互式练习' },
              ]
            },
            { id: 't2_1', day: 2, week: 1, title: '变量与数据类型练习', est_hours: 1.5, description: '巩固变量和数据类型知识',
              resources: [
                { title: '菜鸟教程-数据类型', url: 'https://www.runoob.com/python3/python3-variable-types.html', type: 'article' },
                { title: '廖雪峰-数据类型', url: 'https://www.liaoxuefeng.com/wiki/1016959663602400/1017063826246112', type: 'article' },
              ],
              exercises: [
                { title: '数据类型专项练习', url: '/learn/kb/exercises/01-变量练习', description: '类型转换与运算练习' },
              ]
            },
            { id: 't2_2', day: 2, week: 1, title: '字符串操作', est_hours: 1.0, description: '字符串拼接、切片、常用方法',
              resources: [
                { title: '菜鸟教程-字符串', url: 'https://www.runoob.com/python3/python3-string.html', type: 'article' },
                { title: 'Python字符串方法大全', url: 'https://docs.python.org/zh-cn/3/library/stdtypes.html#string-methods', type: 'course' },
                { title: '字符串操作视频', url: 'https://www.bilibili.com/video/BV1qW4y1a7fU?p=20', type: 'video' },
              ],
              exercises: [
                { title: '字符串练习', url: '/learn/kb/exercises/02-流程控制练习', description: '字符串切片与方法练习' },
              ]
            },
            { id: 't2_3', day: 2, week: 1, title: '类型转换', est_hours: 0.5, description: 'int/float/str/bool 之间的转换',
              resources: [
                { title: 'Python类型转换', url: 'https://www.runoob.com/python3/python3-type-conversion.html', type: 'article' },
              ],
              exercises: [
                { title: '类型转换练习', url: '/learn/kb/exercises/01-变量练习', description: '类型转换专项练习' },
              ]
            },
            { id: 't3_1', day: 3, week: 1, title: '条件判断（if/elif/else）', est_hours: 1.0, description: '学习条件判断语句',
              resources: [
                { title: '廖雪峰-条件判断', url: 'https://www.liaoxuefeng.com/wiki/1016959663602400/1017063413908976', type: 'article' },
                { title: '流程控制详解', url: '/learn/kb/python_learning_path/02-流程控制', type: 'article' },
                { title: '黑马程序员-条件判断视频', url: 'https://www.bilibili.com/video/BV1qW4y1a7fU?p=22', type: 'video' },
              ],
              exercises: [
                { title: '条件判断练习', url: '/learn/kb/exercises/02-流程控制练习', description: 'if-else 条件判断练习' },
              ]
            },
            { id: 't3_2', day: 3, week: 1, title: '条件判断练习', est_hours: 1.5, description: '分级成绩判断、猜数字等练习',
              resources: [
                { title: '菜鸟教程-if语句', url: 'https://www.runoob.com/python3/python3-if-statement.html', type: 'article' },
              ],
              exercises: [
                { title: '猜数字游戏', url: '/learn/kb/exercises/02-流程控制练习', description: '综合条件判断练习' },
                { title: 'LeetCode 简单题', url: 'https://leetcode.cn/problemset/all/?difficulty=EASY&page=1', description: '在线编程练习' },
              ]
            },
            { id: 't3_3', day: 3, week: 1, title: '逻辑运算符', est_hours: 0.5, description: 'and、or、not 的使用',
              resources: [
                { title: 'Python逻辑运算符', url: 'https://www.runoob.com/python3/python3-operators.html', type: 'article' },
              ],
              exercises: [
                { title: '逻辑运算练习', url: '/learn/kb/exercises/02-流程控制练习', description: 'and/or/not 练习' },
              ]
            },
            { id: 't4_1', day: 4, week: 1, title: 'for 循环', est_hours: 1.0, description: '学习 for 循环和 range()',
              resources: [
                { title: '菜鸟教程-for循环', url: 'https://www.runoob.com/python3/python3-loop.html', type: 'article' },
                { title: '廖雪峰-for循环', url: 'https://www.liaoxuefeng.com/wiki/1016959663602400/1017070470158080', type: 'article' },
                { title: '尚硅谷-循环视频', url: 'https://www.bilibili.com/video/BV1wD4y1o7AS?p=25', type: 'video' },
              ],
              exercises: [
                { title: '循环练习', url: '/learn/kb/exercises/02-流程控制练习', description: 'for和while循环练习' },
                { title: '循环专题练习', url: 'https://www.runoob.com/python3/python3-examples.html', description: '菜鸟教程实例练习' },
              ]
            },
            { id: 't4_2', day: 4, week: 1, title: 'while 循环', est_hours: 1.0, description: '学习 while 循环',
              resources: [
                { title: 'Python while循环', url: 'https://www.liaoxuefeng.com/wiki/1016959663602400/1017063826246112', type: 'article' },
                { title: '菜鸟教程-while循环', url: 'https://www.runoob.com/python3/python3-while-loop.html', type: 'article' },
                { title: '黑马程序员-while循环视频', url: 'https://www.bilibili.com/video/BV1qW4y1a7fU?p=25', type: 'video' },
              ],
              exercises: [
                { title: 'while循环练习', url: '/learn/kb/exercises/02-流程控制练习', description: 'while循环专项练习' },
              ]
            },
            { id: 't5_1', day: 5, week: 1, title: '循环练习', est_hours: 1.5, description: '九九乘法表、斐波那契数列等',
              resources: [
                { title: 'Python循环实例', url: 'https://www.runoob.com/python3/python3-examples.html', type: 'article' },
              ],
              exercises: [
                { title: '九九乘法表', url: '/learn/kb/exercises/02-流程控制练习', description: '经典循环练习' },
                { title: '斐波那契数列', url: '/learn/kb/exercises/02-流程控制练习', description: '递归与循环练习' },
              ]
            },
            { id: 't5_2', day: 5, week: 1, title: 'break 和 continue', est_hours: 1.0, description: '循环控制语句',
              resources: [
                { title: 'Python break 与 continue', url: 'https://www.liaoxuefeng.com/wiki/1016959663602400/1017071267000640', type: 'article' },
              ],
              exercises: [
                { title: '循环控制练习', url: '/learn/kb/exercises/02-流程控制练习', description: 'break/continue 专项练习' },
              ]
            },
          ],
          prerequisite_check: { status: 'passed', details: [], warnings: [] },
          evaluation: { score: 8, issues: [], suggestions: ['建议增加更多实战项目'] },
        });
        resolve();
      }
    }, 30);
  });
}

export function useLearningChat(userId: string) {
  const {
    messages,
    setMessages,
    currentPlan,
    setCurrentPlan,
    sessionId,
    setSessionId,
    prerequisiteCheck,
    setPrerequisiteCheck,
    evaluation,
    setEvaluation,
    useMock,
  } = useAppStore();

  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (userMsg: string) => {
    if (!userMsg.trim() || loading) return;
    setLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setPrerequisiteCheck(null);
    setEvaluation(null);

    if (useMock) {
      let assistantMsg = '';
      await mockSSE(
        userMsg,
        (t) => {
          assistantMsg += t;
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last?.role === 'assistant') {
              updated[updated.length - 1] = { role: 'assistant', content: assistantMsg };
            } else {
              updated.push({ role: 'assistant', content: assistantMsg });
            }
            return updated;
          });
        },
        (p) => {
          setCurrentPlan(p);
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: `✅ 学习计划已生成！共 **${p.total_weeks} 周**，${p.milestones?.length || 0} 个阶段。\n\n👉 [切换到「计划看板」查看详情](/learn/plan/${p.plan_id})`,
          }]);
        },
        (check) => setPrerequisiteCheck(check),
        (evalRes) => setEvaluation(evalRes),
      );
      setLoading(false);
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    let assistantMsg = '';

    try {
      await apiPostSSE(
        '/v1/learn/chat',
        { user_id: userId, message: userMsg, session_id: sessionId },
        {
          onSessionCreated: (sid) => {
            setSessionId(sid);
          },
          onToken: (token) => {
            assistantMsg += token;
            setMessages(prev => {
              const updated = [...prev];
              const last = updated[updated.length - 1];
              if (last?.role === 'assistant') {
                updated[updated.length - 1] = { role: 'assistant', content: assistantMsg };
              } else {
                updated.push({ role: 'assistant', content: assistantMsg });
              }
              return updated;
            });
          },
          onPrerequisite: (check) => {
            setPrerequisiteCheck(check);
          },
          onEvaluation: (evalRes) => {
            setEvaluation(evalRes);
          },
          onPlan: (p) => {
            setCurrentPlan(p);
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `✅ 学习计划已生成！共 **${p.total_weeks} 周**，${p.milestones?.length || 0} 个阶段。\n\n👉 [切换到「计划看板」查看详情](/learn/plan/${p.plan_id})`,
            }]);
          },
          onError: (err) => {
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: `⚠️ 出错了：${err.message}`,
            }]);
          },
        },
        controller.signal,
      );
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setMessages(prev => [...prev, { role: 'assistant', content: `⚠️ 连接失败：请确保后端服务已启动。` }]);
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  }, [loading, userId, sessionId, useMock, setMessages, setCurrentPlan, setSessionId, setPrerequisiteCheck, setEvaluation]);

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, []);

  const clearMessages = useCallback(async () => {
    stop();
    // 删除后端会话
    if (sessionId) {
      try {
        await apiDeleteSession(sessionId);
      } catch (e) {
        console.error('删除会话失败:', e);
      }
    }
    setMessages([]);
    setCurrentPlan(null);
    setSessionId('');
  }, [stop, sessionId, setMessages, setCurrentPlan, setSessionId]);

  return {
    messages,
    setMessages,
    loading,
    plan: currentPlan,
    sessionId,
    prerequisiteCheck,
    evaluation,
    sendMessage,
    stop,
    clearMessages,
  };
}
