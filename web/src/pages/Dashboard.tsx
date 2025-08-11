import React, { useEffect, useState } from 'react';
import Tile, { IndicatorData } from '../components/Tile';
import { fetchIndex, fetchIndicatorData, FetchError } from '../lib/fetch';

interface IndexData {
  indicators: Array<{
    id: string;
    path: string;
    title: string;
    unit: string;
    frequency: string;
    politics_overlay: boolean;
  }>;
  last_updated: string;
}

const Dashboard: React.FC = () => {
  const [indexData, setIndexData] = useState<IndexData | null>(null);
  const [indicatorData, setIndicatorData] = useState<Record<string, IndicatorData>>({});
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [lastUpdated, setLastUpdated] = useState<string>('');

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        
        // Load index data
        const index = await fetchIndex();
        setIndexData(index);
        setLastUpdated(index.last_updated);
        
        // Load all indicator data
        const dataPromises = index.indicators.map(async (indicator: any) => {
          try {
            const data = await fetchIndicatorData(indicator.id);
            return { id: indicator.id, data };
          } catch (error) {
            const errorMessage = error instanceof FetchError 
              ? error.message 
              : 'Failed to load data';
            setErrors(prev => ({ ...prev, [indicator.id]: errorMessage }));
            return { id: indicator.id, data: null };
          }
        });
        
        const results = await Promise.allSettled(dataPromises);
        
        const newIndicatorData: Record<string, IndicatorData> = {};
        results.forEach((result) => {
          if (result.status === 'fulfilled' && result.value.data) {
            newIndicatorData[result.value.id] = result.value.data;
          }
        });
        
        setIndicatorData(newIndicatorData);
      } catch (error) {
        console.error('Failed to load dashboard:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1 className="dashboard-title">Norway Macro Clock</h1>
          <p className="dashboard-subtitle">Key Economic Indicators</p>
          <div className="dashboard-meta">Loading...</div>
        </div>
        <div className="tile-grid">
          {Array.from({ length: 6 }, (_, i) => (
            <div key={i} className="tile loading">
              <div className="tile-header">
                <div className="tile-title">Loading...</div>
              </div>
              <div className="tile-value">—</div>
              <div className="tile-deltas">
                <span className="delta-badge none">MoM —</span>
                <span className="delta-badge none">YoY —</span>
              </div>
              <div className="tile-sparkline" />
              <div className="tile-footer">
                <span>Loading...</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!indexData) {
    return (
      <div className="dashboard">
        <div className="dashboard-header">
          <h1 className="dashboard-title">Norway Macro Clock</h1>
          <p className="dashboard-subtitle">Key Economic Indicators</p>
          <div className="dashboard-meta">Failed to load dashboard data</div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Norway Macro Clock</h1>
        <p className="dashboard-subtitle">Key Economic Indicators</p>
        <div className="dashboard-meta">
          Last updated: {lastUpdated ? new Date(lastUpdated).toLocaleString() : 'Unknown'}
        </div>
      </div>
      
      <div className="tile-grid">
        {indexData.indicators.map((indicator) => {
          const data = indicatorData[indicator.id];
          const error = errors[indicator.id];
          
          if (!data && !error) {
            return (
              <div key={indicator.id} className="tile loading">
                <div className="tile-header">
                  <h3 className="tile-title">{indicator.title}</h3>
                </div>
                <div className="tile-value">—</div>
                <div className="tile-deltas">
                  <span className="delta-badge none">MoM —</span>
                  <span className="delta-badge none">YoY —</span>
                </div>
                <div className="tile-sparkline" />
                <div className="tile-footer">
                  <span>Loading...</span>
                </div>
              </div>
            );
          }
          
          if (error) {
            return (
              <div key={indicator.id} className="tile error">
                <div className="tile-error">
                  <div className="tile-title">{indicator.title}</div>
                  <div>Error loading data</div>
                  <div className="tile-footer">
                    <span>Error: {error}</span>
                  </div>
                </div>
              </div>
            );
          }
          
          return (
            <Tile
              key={indicator.id}
              data={data!}
              loading={false}
            />
          );
        })}
      </div>
    </div>
  );
};

export default Dashboard;
