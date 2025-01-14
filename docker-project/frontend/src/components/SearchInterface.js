import React, { useState } from 'react';
import axios from 'axios';

const SearchInterface = ({ documents, clusters }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    setError(null);

    try {
      const response = await axios.get('/api/search', {
        params: {
          query: searchQuery,
          cluster: clusters ? JSON.stringify(clusters) : undefined
        }
      });

      setSearchResults(response.data.results);
    } catch (err) {
      setError('Failed to perform search. Please try again.');
      console.error('Search error:', err);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Search Documents</h2>

      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={searching}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {searchResults.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Search Results</h3>
          <div className="divide-y">
            {searchResults.map((result, index) => (
              <div key={index} className="py-4">
                <h4 className="font-medium">{result.title}</h4>
                <p className="text-gray-600 mt-1">{result.excerpt}</p>
                <div className="mt-2 flex gap-2">
                  {result.tags?.map((tag, tagIndex) => (
                    <span
                      key={tagIndex}
                      className="px-2 py-1 bg-gray-100 text-gray-600 text-sm rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchInterface;
