import React from 'react';
import Spark from './Spark';
import { formatValue, formatDelta, getDeltaClass, formatRelativeTime } from '../lib/format';

export interface IndicatorData {
  id: string;
  title: string;
  unit: string;
  frequency: string;
  source: {
    name: string;
    url: string;
  };
  last_updated_utc: string;
  series: Array<{
    date: string;
    value: number;
  }>;
  snapshot: {
    latest_value: number | null;
    mom_pct: number | null;
    yoy_pct: number | null;
    min: number | null;
    max: number | null;
  };
  politics_overlay: boolean;
}

export interface TileProps {
  data: IndicatorData;
  loading?: boolean;
  error?: string;
}

const Tile: React.FC<TileProps> = ({ data, loading = false, error }) => {
  const { snapshot, source, last_updated_utc, politics_overlay } = data;

  if (error) {
    return (
      <div className="tile error">
        <div className="tile-error">
          <div className="tile-title">{data.title}</div>
          <div>Error loading data</div>
          <div className="tile-footer">
            <span>Source: {source.name}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`tile ${loading ? 'loading' : ''}`}>
      <div className="tile-header">
        <h3 className="tile-title">{data.title}</h3>
        <a 
          href={source.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="tile-source"
          title={`Data source: ${source.name}`}
        >
          {source.name}
        </a>
      </div>

      <div className="tile-value">
        {formatValue(snapshot.latest_value, data.unit)}
        <span className="tile-unit">{data.unit}</span>
      </div>

      <div className="tile-deltas">
        <span 
          className={`delta-badge ${getDeltaClass(snapshot.mom_pct)}`}
          title="Month-over-month change"
        >
          MoM {formatDelta(snapshot.mom_pct)}
        </span>
        <span 
          className={`delta-badge ${getDeltaClass(snapshot.yoy_pct)}`}
          title="Year-over-year change"
        >
          YoY {formatDelta(snapshot.yoy_pct)}
        </span>
      </div>

      <div className="tile-sparkline">
        <Spark 
          data={data.series} 
          showPolitics={politics_overlay}
          min={snapshot.min}
          max={snapshot.max}
        />
      </div>

      <div className="tile-footer">
        <div className="tile-updated">
          <span>Updated {formatRelativeTime(last_updated_utc)}</span>
        </div>
        <div className="tile-frequency">
          {data.frequency}
        </div>
      </div>
    </div>
  );
};

export default Tile;
