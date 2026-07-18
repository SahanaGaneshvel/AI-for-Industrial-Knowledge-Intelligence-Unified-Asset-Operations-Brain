import { useState, useEffect } from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, Loader2, Play } from 'lucide-react';
import { complianceApi } from '../services/api';

function ComplianceView() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadReport();
  }, []);

  const loadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await complianceApi.getReport();
      setReport(data);
    } catch (err) {
      if (err.response?.status !== 404) {
        setError('Failed to load compliance report');
      }
    } finally {
      setLoading(false);
    }
  };

  const runScan = async () => {
    setScanning(true);
    setError(null);
    try {
      const data = await complianceApi.runScan();
      setReport(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run compliance scan');
    } finally {
      setScanning(false);
    }
  };

  const getRiskBadge = (risk) => {
    const badges = {
      CRITICAL: 'badge-critical',
      HIGH: 'badge-high',
      MEDIUM: 'badge-medium',
      LOW: 'badge-low',
    };
    return badges[risk] || 'badge';
  };

  const getStatusBadge = (status) => {
    const badges = {
      COMPLIANT: 'badge-compliant',
      NON_COMPLIANT: 'badge-non-compliant',
      PARTIAL: 'badge-medium',
      INSUFFICIENT_EVIDENCE: 'badge bg-gray-100 text-gray-800',
    };
    return badges[status] || 'badge';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Shield className="w-7 h-7 mr-3 text-primary-600" />
              Compliance Gap Detection
            </h2>
            <p className="text-gray-600 mt-1">
              Automated regulatory compliance assessment across all documentation
            </p>
          </div>
          <button
            onClick={runScan}
            disabled={scanning}
            className="btn-primary inline-flex items-center disabled:opacity-50"
          >
            {scanning ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                Scanning...
              </>
            ) : (
              <>
                <Play className="w-5 h-5 mr-2" />
                Run Scan
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start mb-6">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {report && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600">Total Rules</p>
                <p className="text-2xl font-bold text-gray-900">{report.summary.total_rules}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-green-600">Compliant</p>
                <p className="text-2xl font-bold text-green-900">{report.summary.compliant}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4">
                <p className="text-sm text-red-600">Non-Compliant</p>
                <p className="text-2xl font-bold text-red-900">{report.summary.non_compliant}</p>
              </div>
              <div className="bg-red-50 rounded-lg p-4 border-2 border-red-200">
                <p className="text-sm text-red-700 font-medium">Critical Gaps</p>
                <p className="text-2xl font-bold text-red-900">{report.summary.critical_gaps}</p>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <p className="text-sm text-orange-600">High Risk</p>
                <p className="text-2xl font-bold text-orange-900">{report.summary.high_risk_gaps}</p>
              </div>
            </div>

            {report.scan_timestamp && (
              <p className="text-sm text-gray-500 mb-6">
                Last scan: {new Date(report.scan_timestamp).toLocaleString()}
                <span className="ml-2">({report.scan_duration_seconds}s)</span>
              </p>
            )}
          </>
        )}
      </div>

      {report && report.gaps_found && report.gaps_found.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <XCircle className="w-5 h-5 mr-2 text-red-600" />
            Compliance Gaps Found ({report.gaps_found.length})
          </h3>
          <div className="space-y-4">
            {report.gaps_found.map((gap, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-5 hover:border-gray-300 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-base font-semibold text-gray-900">{gap.title}</h4>
                      <span className={getRiskBadge(gap.risk_level)}>{gap.risk_level}</span>
                    </div>
                    <p className="text-sm text-gray-600">
                      {gap.rule_id} | {gap.regulatory_ref}
                    </p>
                  </div>
                  <span className={getStatusBadge(gap.status)}>{gap.status.replace('_', ' ')}</span>
                </div>

                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Requirement:</p>
                    <p className="text-sm text-gray-600">{gap.requirement}</p>
                  </div>

                  <div className="bg-red-50 border border-red-100 rounded-md p-3">
                    <p className="text-sm font-medium text-red-900 mb-1">Gap Identified:</p>
                    <p className="text-sm text-red-800">{gap.gap_description}</p>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-1">Finding:</p>
                    <p className="text-sm text-gray-600">{gap.finding}</p>
                  </div>

                  {gap.evidence && gap.evidence.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-2">Evidence:</p>
                      <ul className="list-disc list-inside space-y-1">
                        {gap.evidence.map((item, i) => (
                          <li key={i} className="text-sm text-gray-600">{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {gap.recommended_action && (
                    <div className="bg-blue-50 border border-blue-100 rounded-md p-3">
                      <p className="text-sm font-medium text-blue-900 mb-1">Recommended Action:</p>
                      <p className="text-sm text-blue-800">{gap.recommended_action}</p>
                    </div>
                  )}

                  <div className="flex items-center gap-2 pt-2">
                    <span className="text-xs text-gray-500">
                      Confidence: {gap.confidence}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {report && report.rules_checked && report.rules_checked.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 mr-2 text-gray-600" />
            All Rules Checked ({report.rules_checked.length})
          </h3>
          <div className="space-y-2">
            {report.rules_checked.map((rule, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{rule.title}</p>
                  <p className="text-xs text-gray-600">{rule.rule_id} | {rule.regulatory_ref}</p>
                </div>
                <span className={getStatusBadge(rule.status)}>{rule.status.replace('_', ' ')}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {!report && !loading && (
        <div className="card text-center py-12">
          <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Compliance Report Available</h3>
          <p className="text-gray-600 mb-6">Run a compliance scan to identify regulatory gaps</p>
          <button onClick={runScan} className="btn-primary inline-flex items-center">
            <Play className="w-5 h-5 mr-2" />
            Run First Scan
          </button>
        </div>
      )}
    </div>
  );
}

export default ComplianceView;
