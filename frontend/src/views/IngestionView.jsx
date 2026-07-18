import { useState } from 'react';
import { Upload, Database, Loader2, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { ingestApi } from '../services/api';

function IngestionView() {
  const [uploading, setUploading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [ingestResult, setIngestResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const result = await ingestApi.uploadFile(file);
      setUploadResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleFullIngestion = async (force = false) => {
    setIngesting(true);
    setError(null);
    setIngestResult(null);

    try {
      const result = await ingestApi.runFullIngestion(force);
      setIngestResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run ingestion');
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="card">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center">
          <Database className="w-7 h-7 mr-3 text-primary-600" />
          Data Ingestion
        </h2>
        <p className="text-gray-600 mb-6">
          Upload new documents or re-index the entire corpus into the knowledge graph and vector store
        </p>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-gray-400 transition-colors">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Upload className="w-5 h-5 mr-2" />
              Upload Single Document
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Upload a work order, incident report, inspection report, or SOP document
            </p>
            <div className="space-y-4">
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={uploading}
                accept=".txt,.pdf,.csv"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 disabled:opacity-50"
              />
              {uploading && (
                <div className="flex items-center text-sm text-gray-600">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading and processing...
                </div>
              )}
            </div>
          </div>

          <div className="border-2 border-gray-300 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <RefreshCw className="w-5 h-5 mr-2" />
              Full Corpus Ingestion
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Process all documents in the corpus directory. Uses cache for already-processed files.
            </p>
            <div className="space-y-3">
              <button
                onClick={() => handleFullIngestion(false)}
                disabled={ingesting}
                className="btn-primary w-full disabled:opacity-50"
              >
                {ingesting ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin inline" />
                    Ingesting...
                  </>
                ) : (
                  'Run Ingestion (Skip Cached)'
                )}
              </button>
              <button
                onClick={() => handleFullIngestion(true)}
                disabled={ingesting}
                className="btn-secondary w-full disabled:opacity-50"
              >
                Force Re-ingest All
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}
      </div>

      {uploadResult && (
        <div className="card">
          <div className="flex items-start mb-4">
            <CheckCircle className="w-6 h-6 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Upload Successful</h3>
              <p className="text-sm text-gray-600 mb-4">
                Document has been ingested into the knowledge graph and vector store
              </p>

              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Document ID:</span>
                  <span className="font-medium text-gray-900">{uploadResult.doc_id}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Status:</span>
                  <span className="font-medium text-green-600">{uploadResult.status}</span>
                </div>
                {uploadResult.chunks_created && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Chunks Created:</span>
                    <span className="font-medium text-gray-900">{uploadResult.chunks_created}</span>
                  </div>
                )}
              </div>

              {uploadResult.extracted_entities && (
                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Extracted Entities</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="text-xs text-gray-700 overflow-x-auto">
                      {JSON.stringify(uploadResult.extracted_entities, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {ingestResult && (
        <div className="card">
          <div className="flex items-start mb-4">
            <CheckCircle className="w-6 h-6 text-green-600 mr-3 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Ingestion Complete</h3>
              <p className="text-sm text-gray-600 mb-4">
                Corpus has been processed and indexed
              </p>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-sm text-blue-600">Processed</p>
                  <p className="text-2xl font-bold text-blue-900">{ingestResult.documents_processed}</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4">
                  <p className="text-sm text-green-600">From Cache</p>
                  <p className="text-2xl font-bold text-green-900">{ingestResult.documents_cached}</p>
                </div>
                <div className="bg-red-50 rounded-lg p-4">
                  <p className="text-sm text-red-600">Errors</p>
                  <p className="text-2xl font-bold text-red-900">{ingestResult.errors}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="card bg-blue-50 border border-blue-200">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">Ingestion Process</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p><strong>For each document:</strong></p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li>Extract content (text from PDFs, CSVs, images)</li>
            <li>Use Gemini LLM to extract entities, equipment tags, personnel, and failure modes</li>
            <li>Chunk text into ~800 token segments with 100 token overlap</li>
            <li>Store chunks in ChromaDB vector store with metadata</li>
            <li>Update knowledge graph with entities and relationships</li>
            <li>Cache extraction results by file hash for efficiency</li>
          </ul>
          <p className="mt-3">
            <strong>Note:</strong> Cached extractions are reused when file content hasn't changed,
            significantly speeding up re-ingestion.
          </p>
        </div>
      </div>
    </div>
  );
}

export default IngestionView;
