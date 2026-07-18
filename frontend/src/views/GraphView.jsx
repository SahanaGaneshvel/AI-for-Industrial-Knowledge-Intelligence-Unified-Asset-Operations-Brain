import { useState, useEffect } from 'react';
import { Network, Loader2, Search, FileText, Users, Wrench, AlertCircle } from 'lucide-react';
import { graphApi } from '../services/api';

function GraphView() {
  const [stats, setStats] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [neighbors, setNeighbors] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await graphApi.getStats();
      setStats(data);
    } catch (err) {
      setError('Failed to load graph statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleNodeSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const data = await graphApi.getNode(searchQuery.trim(), 1);

      // Transform API response to expected format
      // API returns: { node, found, data, edges: [{source, target, type, target_data/source_data}] }
      // We need: { nodes: [{id, node_type, ...}], edges: [...] }
      if (data.found) {
        const nodesMap = new Map();
        const edges = data.edges || [];

        // Extract unique nodes from edges
        edges.forEach(edge => {
          if (edge.target_data) {
            nodesMap.set(edge.target, { id: edge.target, ...edge.target_data });
          }
          if (edge.source_data) {
            nodesMap.set(edge.source, { id: edge.source, ...edge.source_data });
          }
        });

        setNeighbors({
          nodes: Array.from(nodesMap.values()),
          edges: edges
        });
        setSelectedNode(searchQuery.trim());
      } else {
        setError(`Node "${searchQuery}" not found in knowledge graph`);
        setNeighbors(null);
      }
    } catch (err) {
      setError(`Node "${searchQuery}" not found in knowledge graph`);
      setNeighbors(null);
    } finally {
      setLoading(false);
    }
  };

  const getNodeIcon = (nodeType) => {
    const icons = {
      document: FileText,
      equipment: Wrench,
      personnel: Users,
      failure_mode: AlertCircle,
      regulatory: FileText,
    };
    return icons[nodeType] || FileText;
  };

  const getNodeColor = (nodeType) => {
    const colors = {
      document: 'bg-blue-100 text-blue-800',
      equipment: 'bg-green-100 text-green-800',
      personnel: 'bg-purple-100 text-purple-800',
      failure_mode: 'bg-red-100 text-red-800',
      regulatory: 'bg-yellow-100 text-yellow-800',
    };
    return colors[nodeType] || 'bg-gray-100 text-gray-800';
  };

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center">
          <Network className="w-7 h-7 mr-3 text-primary-600" />
          Knowledge Graph Explorer
        </h2>
        <p className="text-gray-600 mb-6">
          Explore the entity relationship graph connecting documents, equipment, personnel, and events
        </p>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-600">Documents</p>
              <p className="text-2xl font-bold text-blue-900">{stats.graph_nodes?.document || 0}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-green-600">Equipment</p>
              <p className="text-2xl font-bold text-green-900">{stats.graph_nodes?.equipment || 0}</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-purple-600">Personnel</p>
              <p className="text-2xl font-bold text-purple-900">{stats.graph_nodes?.personnel || 0}</p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-600">Total Edges</p>
              <p className="text-2xl font-bold text-gray-900">{Object.values(stats.graph_edges || {}).reduce((a, b) => a + b, 0)}</p>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Node Search</h3>
        <form onSubmit={handleNodeSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter node ID (e.g., P-101A, WO-2024-001.txt, PERSON:Priya Sharma)"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button type="submit" className="btn-primary inline-flex items-center">
            <Search className="w-5 h-5 mr-2" />
            Search
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div className="mt-4">
          <p className="text-sm text-gray-600">Popular equipment tags to try:</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {['P-101A', 'V-310', 'E-205', 'C-102', 'H-501'].map((tag) => (
              <button
                key={tag}
                onClick={() => {
                  setSearchQuery(tag);
                  handleNodeSearch({ preventDefault: () => {} });
                }}
                className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1.5 rounded-full transition-colors"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      {neighbors && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Node: {selectedNode}
          </h3>

          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Connected Nodes ({neighbors.nodes?.length || 0})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {neighbors.nodes?.map((node, idx) => {
                  const Icon = getNodeIcon(node.node_type);
                  return (
                    <div
                      key={idx}
                      className="flex items-start p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                      onClick={() => {
                        setSearchQuery(node.id);
                        handleNodeSearch({ preventDefault: () => {} });
                      }}
                    >
                      <div className={`p-2 rounded-lg ${getNodeColor(node.node_type)} mr-3`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{node.id}</p>
                        <p className="text-xs text-gray-600 capitalize">{node.node_type}</p>
                        {node.summary && (
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">{node.summary}</p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">
                Edges ({neighbors.edges?.length || 0})
              </h4>
              <div className="space-y-2">
                {neighbors.edges?.map((edge, idx) => (
                  <div key={idx} className="flex items-center p-3 bg-gray-50 rounded-lg text-sm">
                    <span className="font-medium text-gray-700">{edge.source}</span>
                    <span className="mx-3 px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs font-medium">
                      {edge.type}
                    </span>
                    <span className="font-medium text-gray-700">{edge.target}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {stats && stats.graph_nodes && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Graph Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-3">Nodes by Type</h4>
              <div className="space-y-2">
                {Object.entries(stats.graph_nodes).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700 capitalize">{type.replace('_', ' ')}</span>
                    <span className="text-sm font-medium text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            {stats.graph_edges && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">Edges by Type</h4>
                <div className="space-y-2">
                  {Object.entries(stats.graph_edges).map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm text-gray-700">{type}</span>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default GraphView;
