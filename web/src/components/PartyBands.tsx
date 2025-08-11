import React, { useEffect, useState } from 'react';

export interface PartyBandsProps {
  data: Array<{
    date: string;
    value: number;
  }>;
  height: number;
  width: number;
}

interface PoliticalPeriod {
  start: string;
  end: string;
  coalition: string[];
  description: string;
}

interface Party {
  name: string;
  color: string;
}

interface GovernmentData {
  parties: Record<string, Party>;
  periods: PoliticalPeriod[];
}

const PartyBands: React.FC<PartyBandsProps> = ({ data, height, width }) => {
  const [governmentData, setGovernmentData] = useState<GovernmentData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadGovernmentData = async () => {
      try {
        const response = await fetch('/config/governments.json');
        if (response.ok) {
          const data = await response.json();
          setGovernmentData(data);
        }
      } catch (error) {
        console.warn('Failed to load government data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadGovernmentData();
  }, []);

  if (loading || !governmentData || data.length === 0) {
    return null;
  }

  // Calculate date range of the data
  const dates = data.map(item => new Date(item.date));
  const minDate = new Date(Math.min(...dates.map(d => d.getTime())));
  const maxDate = new Date(Math.max(...dates.map(d => d.getTime())));
  const totalRange = maxDate.getTime() - minDate.getTime();

  // Filter periods that overlap with the data
  const relevantPeriods = governmentData.periods.filter(period => {
    const periodStart = new Date(period.start);
    const periodEnd = new Date(period.end === '9999-12-31' ? new Date() : period.end);
    
    return periodStart <= maxDate && periodEnd >= minDate;
  });

  if (relevantPeriods.length === 0) {
    return null;
  }

  return (
    <div 
      className="political-bands"
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        pointerEvents: 'none',
        zIndex: 1
      }}
    >
      {relevantPeriods.map((period, index) => {
        const periodStart = new Date(period.start);
        const periodEnd = new Date(period.end === '9999-12-31' ? new Date() : period.end);
        
        // Calculate position and width
        const startPos = Math.max(0, (periodStart.getTime() - minDate.getTime()) / totalRange);
        const endPos = Math.min(1, (periodEnd.getTime() - minDate.getTime()) / totalRange);
        const bandWidth = (endPos - startPos) * 100;
        const bandLeft = startPos * 100;

        // Get coalition color (use first party's color or default)
        const coalitionColor = period.coalition.length > 0 
          ? governmentData.parties[period.coalition[0]]?.color || '#CCCCCC'
          : '#CCCCCC';

        return (
          <div
            key={`${period.start}-${period.end}-${index}`}
            className="political-band"
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${bandLeft}%`,
              width: `${bandWidth}%`,
              backgroundColor: coalitionColor,
              opacity: 0.1,
              transition: 'opacity 0.25s ease-in-out'
            }}
            title={`${period.description} (${period.coalition.join(', ')})`}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = '0.2';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = '0.1';
            }}
          />
        );
      })}
    </div>
  );
};

export default PartyBands;
