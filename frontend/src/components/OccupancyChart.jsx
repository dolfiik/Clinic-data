import { useState, useEffect } from 'react';

const OccupancyChart = ({ 
  department, 
  currentOccupancy, 
  forecast, 
  capacity 
}) => {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    if (!currentOccupancy || !forecast) return;

    const data = [
      {
        label: 'Teraz',
        value: currentOccupancy,
        time: 0
      },
      {
        label: '+1h',
        value: forecast.hour_1 || currentOccupancy,
        time: 1
      },
      {
        label: '+2h',
        value: forecast.hour_2 || currentOccupancy,
        time: 2
      },
      {
        label: '+3h',
        value: forecast.hour_3 || currentOccupancy,
        time: 3
      }
    ];

    setChartData(data);
  }, [currentOccupancy, forecast]);

  if (!chartData.length) {
    return <div className="occupancy-chart-loading">Ładowanie danych...</div>;
  }

  const maxValue = Math.max(capacity, ...chartData.map(d => d.value));
  const yScale = maxValue * 1.1; 

  const width = 400;
  const height = 200;
  const padding = { top: 20, right: 40, bottom: 40, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const getX = (time) => {
    return padding.left + (time / 3) * chartWidth;
  };

  const getY = (value) => {
    return padding.top + chartHeight - (value / yScale) * chartHeight;
  };

  const linePath = chartData.map((point, index) => {
    const x = getX(point.time);
    const y = getY(point.value);
    return index === 0 ? `M ${x} ${y}` : `L ${x} ${y}`;
  }).join(' ');

  const capacityY = getY(capacity);

  const getWarningColor = (value) => {
    const percentage = (value / capacity) * 100;
    if (percentage >= 90) return '#c62828'; 
    if (percentage >= 80) return '#f57c00';
    if (percentage >= 70) return '#fbc02d';
    return '#7cb342'; 
  };

  const warnings = chartData
    .filter(point => (point.value / capacity) * 100 >= 80)
    .map(point => point.label);

  return (
    <div className="occupancy-chart">
      <div className="chart-header">
        <h4> Prognoza obłożenia: {department}</h4>
        {warnings.length > 0 && (
          <div className="chart-warning">
             Wysokie obłożenie: {warnings.join(', ')}
          </div>
        )}
      </div>

      <svg width={width} height={height} className="chart-svg">
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding.top + chartHeight * (1 - ratio);
          const value = Math.round(yScale * ratio);
          return (
            <g key={ratio}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#e0e0e0"
                strokeWidth="1"
              />
              <text
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="12"
                fill="#666"
              >
                {value}
              </text>
            </g>
          );
        })}

        <line
          x1={padding.left}
          y1={capacityY}
          x2={width - padding.right}
          y2={capacityY}
          stroke="#d32f2f"
          strokeWidth="2"
          strokeDasharray="5,5"
        />
        <text
          x={width - padding.right + 5}
          y={capacityY + 4}
          fontSize="12"
          fill="#d32f2f"
          fontWeight="bold"
        >
          Max: {capacity}
        </text>

        <path
          d={linePath}
          fill="none"
          stroke="#1976d2"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {chartData.map((point, index) => {
          const x = getX(point.time);
          const y = getY(point.value);
          const color = getWarningColor(point.value);

          return (
            <g key={index}>
              <circle
                cx={x}
                cy={y}
                r="6"
                fill={color}
                stroke="#fff"
                strokeWidth="2"
              />
              
              <text
                x={x}
                y={y - 15}
                textAnchor="middle"
                fontSize="13"
                fontWeight="bold"
                fill={color}
              >
                {point.value}
              </text>

              <text
                x={x}
                y={height - padding.bottom + 25}
                textAnchor="middle"
                fontSize="12"
                fill="#666"
              >
                {point.label}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#7cb342' }}></span>
          <span>Niskie (&lt;70%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#fbc02d' }}></span>
          <span>Średnie (70-80%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#f57c00' }}></span>
          <span>Wysokie (80-90%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#c62828' }}></span>
          <span>Krytyczne (≥90%)</span>
        </div>
      </div>

      <div className="chart-info">
        {chartData.map((point, index) => {
          const percentage = ((point.value / capacity) * 100).toFixed(0);
          return (
            <div key={index} className="info-item">
              <strong>{point.label}:</strong> {point.value}/{capacity} ({percentage}%)
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default OccupancyChart;
