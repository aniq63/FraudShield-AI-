import { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';

export const useApi = (url, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(url, options);
      setData(response.data);
      return response.data;
    } catch (err) {
      setError(err.message);
      console.error('API Error:', err);
    } finally {
      setLoading(false);
    }
  }, [url, options]);

  useEffect(() => {
    if (options.skip) return;
    fetchData();
    
    // Polling interval
    if (options.pollingInterval) {
      const interval = setInterval(fetchData, options.pollingInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, options]);

  return { data, loading, error, refetch: fetchData };
};
