import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const DocumentUpload = ({ onDocumentsProcessed }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      acceptedFiles.forEach(file => {
        formData.append('documents', file);
      });

      const response = await axios.post('/api/documents/process', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      onDocumentsProcessed(response.data);
    } catch (err) {
      setError('Failed to process documents. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  }, [onDocumentsProcessed]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/*': ['.txt', '.doc', '.docx', '.pdf'],
    },
    multiple: true,
  });

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Upload Documents</h2>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <p className="text-gray-600">Processing documents...</p>
        ) : isDragActive ? (
          <p className="text-blue-500">Drop the documents here...</p>
        ) : (
          <p className="text-gray-600">
            Drag and drop documents here, or click to select files
          </p>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
