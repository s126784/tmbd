import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ClusterVisualization from './components/ClusterVisualization';
import SearchInterface from './components/SearchInterface';

function App() {
  const [documentData, setDocumentData] = useState(null);
  const [clusterData, setClusterData] = useState(null);

  const handleDocumentsProcessed = (data) => {
    setDocumentData(data);
  };

  const handleClusteringComplete = (clusters) => {
    setClusterData(clusters);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Document Clustering System
          </h1>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 gap-6">
          <DocumentUpload onDocumentsProcessed={handleDocumentsProcessed} />

          {documentData && (
            <ClusterVisualization
              data={documentData}
              onClusteringComplete={handleClusteringComplete}
            />
          )}

          {clusterData && (
            <SearchInterface
              documents={documentData}
              clusters={clusterData}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
