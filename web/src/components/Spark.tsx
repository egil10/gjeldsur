import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts';
import PartyBands from './PartyBands';

export interface SparkProps {
  data: Array<{
    date: string;
    value: number;
  }>;
  showPolitics?: boolean;
  min?: number | null;
  max?: number | null;
  height?: number;
  width?: number;
}

const Spark: React.FC<SparkProps> = ({ 
  data, 
  showPolitics = false, 
  min, 
  max, 
  height = 60,
  width = 300
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (!chartRef.current || !data || data.length === 0) {
      return;
    }

    // Initialize chart
    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, null, {
        renderer: 'canvas',
        useDirtyRect: true
      });
    }

    // Prepare data for ECharts
    const dates = data.map(item => item.date);
    const values = data.map(item => item.value);

    // Calculate y-axis range
    const dataMin = Math.min(...values);
    const dataMax = Math.max(...values);
    const range = dataMax - dataMin;
    const padding = range * 0.1;

    const yMin = min !== null && min !== undefined ? min : dataMin - padding;
    const yMax = max !== null && max !== undefined ? max : dataMax + padding;

    // Chart options
    const option: echarts.EChartsOption = {
      animation: false,
      grid: {
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
        containLabel: false
      },
      xAxis: {
        type: 'category',
        data: dates,
        show: false,
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        show: false,
        min: yMin,
        max: yMax
      },
      series: [
        {
          type: 'line',
          data: values,
          smooth: true,
          symbol: 'none',
          lineStyle: {
            color: '#005AA3',
            width: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: 'rgba(0, 90, 163, 0.3)'
                },
                {
                  offset: 1,
                  color: 'rgba(0, 90, 163, 0.05)'
                }
              ]
            }
          }
        }
      ]
    };

    // Set chart option
    chartInstance.current.setOption(option, true);
    setIsLoaded(true);

    // Cleanup function
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, [data, min, max]);

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (chartInstance.current) {
        chartInstance.current.resize();
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (!data || data.length === 0) {
    return (
      <div 
        ref={chartRef} 
        style={{ 
          height: `${height}px`, 
          width: `${width}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#9E9E9E',
          fontSize: '12px'
        }}
      >
        No data
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', height: `${height}px`, width: `${width}px` }}>
      {showPolitics && isLoaded && (
        <PartyBands 
          data={data}
          height={height}
          width={width}
        />
      )}
      <div 
        ref={chartRef} 
        style={{ 
          height: `${height}px`, 
          width: `${width}px`,
          position: 'relative',
          zIndex: 2
        }}
      />
    </div>
  );
};

export default Spark;
