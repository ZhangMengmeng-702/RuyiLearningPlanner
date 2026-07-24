import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { apiGet } from '../../services/api';

export default function KbDocPage() {
  const { docId } = useParams<{ docId: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!docId) return;
    setLoading(true);
    apiGet<any>(`/v1/knowledge/doc/${docId}`)
      .then(data => {
        if (data.success) {
          setDoc(data.doc);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [docId]);

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        加载中...
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400">
        <div className="text-4xl mb-3">📄</div>
        <div>文档不存在</div>
        <button
          onClick={() => navigate(-1)}
          className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition-colors"
        >
          返回
        </button>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto bg-gray-950">
      <div className="max-w-4xl mx-auto p-6">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-gray-400 hover:text-indigo-400 transition-colors mb-4 flex items-center gap-1"
        >
          ← 返回
        </button>
        <div className="bg-gray-800/80 rounded-xl p-6 border border-gray-700/50">
          <div className="flex items-start justify-between mb-4">
            <h1 className="text-xl font-bold text-white">{doc.title}</h1>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <span className="px-2 py-1 bg-gray-700 rounded">难度 {doc.difficulty}/3</span>
              <span className="px-2 py-1 bg-gray-700 rounded">{doc.estimated_hours}h</span>
            </div>
          </div>
          {doc.keywords && doc.keywords.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {doc.keywords.map((kw: string, i: number) => (
                <span key={i} className="text-xs px-2 py-1 bg-indigo-900/30 text-indigo-300 rounded-full border border-indigo-700/30">
                  {kw}
                </span>
              ))}
            </div>
          )}
          <div className="prose prose-invert prose-sm max-w-none
            [&_a]:text-indigo-400 [&_code]:bg-gray-700 [&_code]:px-1 [&_code]:rounded
            [&_pre]:bg-gray-900 [&_pre]:p-3 [&_pre]:rounded-lg
            [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4
            [&_h2]:text-white [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:mt-6 [&_h2]:mb-3
            [&_h3]:text-white [&_h3]:text-base [&_h3]:font-medium [&_h3]:mt-4 [&_h3]:mb-2">
            <ReactMarkdown>{doc.content || ''}</ReactMarkdown>
          </div>
          {doc.resources && doc.resources.length > 0 && (
            <div className="mt-6 pt-6 border-t border-gray-700/50">
              <h3 className="text-white font-medium mb-3">📚 相关资源</h3>
              <div className="space-y-2">
                {doc.resources.map((res: any, i: number) => (
                  <a
                    key={i}
                    href={res.url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors border border-gray-600/30"
                    onClick={e => !res.url && e.preventDefault()}
                  >
                    <div className="text-sm text-indigo-300">{res.title}</div>
                    {res.description && (
                      <div className="text-xs text-gray-400 mt-1">{res.description}</div>
                    )}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
