import { useState } from 'react';
import { Send, Loader2, AlertCircle, FileText, TrendingUp } from 'lucide-react';
import { copilotApi } from '../services/api';

function CopilotView() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);

  const exampleQuestions = [
    'What is the recurring failure mode on P-101A and what pattern precedes it?',
    'What is the status of the V-310 CUI inspection finding?',
    'Are there any safety concerns with the current LOTO procedure?',
    'Which equipment has had the most maintenance work in the past year?',
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await copilotApi.query(query, 10);
      setResult(response);
      setQueryHistory([{ query, result: response, timestamp: new Date() }, ...queryHistory]);
      setQuery('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (question) => {
    setQuery(question);
  };

  const getConfidenceBadge = (confidence) => {
    const badges = {
      HIGH: 'badge-compliant',
      MEDIUM: 'badge-medium',
      LOW: 'badge-high',
    };
    return badges[confidence] || 'badge';
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">RAG Copilot</h2>
        <p className="text-gray-600 mb-6">
          Ask questions about equipment, maintenance, incidents, and compliance. The copilot uses
          graph-augmented retrieval to synthesize information across multiple documents.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <div className="flex gap-2">
              <input
                id="query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about equipment, failures, compliance, or patterns..."
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="btn-primary inline-flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    <Send className="w-5 h-5 mr-2" />
                    Ask
                  </>
                )}
              </button>
            </div>
          </div>

          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">Example Questions:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQuestions.map((question, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleExampleClick(question)}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors"
                  disabled={loading}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>

      {result && (
        <div className="card">
          <div className="flex items-start justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Answer</h3>
            <div className="flex items-center gap-2">
              <span className={`badge ${getConfidenceBadge(result.confidence)}`}>
                {result.confidence} Confidence
              </span>
              <span className="text-xs text-gray-500">{result.latency_ms}ms</span>
            </div>
          </div>

          <div className="prose max-w-none mb-6">
            <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{result.answer}</p>
          </div>

          {result.confidence_reason && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-900">
                <strong>Confidence Reason:</strong> {result.confidence_reason}
              </p>
            </div>
          )}

          {result.graph_entities_used && result.graph_entities_used.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2" />
                Graph Entities Used
              </h4>
              <div className="flex flex-wrap gap-2">
                {result.graph_entities_used.map((entity, idx) => (
                  <span key={idx} className="badge bg-purple-100 text-purple-800">
                    {entity}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
              <FileText className="w-4 h-4 mr-2" />
              Sources ({result.citations.length})
            </h4>
            <div className="space-y-2">
              {result.citations.map((citation, idx) => (
                <div
                  key={idx}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-primary-100 text-primary-700 rounded-full text-xs font-medium">
                      {citation.index}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{citation.source}</p>
                      {citation.graph_boosted && (
                        <span className="text-xs text-purple-600">Graph-Linked</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-1 sm:mt-0 ml-9 sm:ml-0">
                    <span className="text-xs text-gray-500">
                      {(citation.relevance_score * 100).toFixed(1)}% relevant
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default CopilotView;
