import { useState, useEffect } from 'react';
import { getDepartmentOccupancy } from '../services/api';

const HeatMap = () => {
  const [occupancy, setOccupancy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchOccupancy();
    const interval = setInterval(fetchOccupancy, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchOccupancy = async () => {
    try {
      const data = await getDepartmentOccupancy();
      setOccupancy(data);
      setError('');
    } catch (err) {
      console.error('Error fetching occupancy:', err);
      setError('Błąd pobierania danych');
    } finally {
      setLoading(false);
    }
  };

  const getOccupancyColor = (percentage) => {
    if (percentage >= 80) return '#2d5016'; // Ciemny zielony (CRITICAL)
    if (percentage >= 60) return '#6b9c3d'; // Średni zielony (HIGH)
    if (percentage >= 40) return '#a7eb67'; // Główny zielony (MEDIUM)
    return '#d4f5b3'; // Jasny zielony (LOW)
  };

  const getStatusLabel = (percentage) => {
    if (percentage >= 80) return 'KRYTYCZNE';
    if (percentage >= 60) return 'WYSOKIE';
    if (percentage >= 40) return 'ŚREDNIE';
    return 'NISKIE';
  };

  if (loading) {
    return (
      <div className="heatmap">
        <h2>Obłożenie Oddziałów</h2>
        <div className="loading">Ładowanie...</div>
      </div>
    );
  }

  if (error || !occupancy) {
    return (
      <div className="heatmap">
        <h2>Obłożenie Oddziałów</h2>
        <div className="error-message">{error || 'Brak danych'}</div>
      </div>
    );
  }

  return (
    <div className="heatmap">
      <h2>Obłożenie Oddziałów</h2>
      <div className="heatmap-timestamp">
        Aktualizacja: {new Date(occupancy.timestamp).toLocaleString('pl-PL', {
          hour: '2-digit',
          minute: '2-digit'
        })}
      </div>

      <div className="departments-list">
        {occupancy.departments.map((dept) => {
          const percentage = dept.percentage;
          const barColor = getOccupancyColor(percentage);
          const status = getStatusLabel(percentage);

          return (
            <div key={dept.name} className="department-item">
              <div className="department-header">
                <span className="department-name">{dept.name}</span>
                <span className="department-count">
                  {dept.current}/{dept.capacity}
                </span>
              </div>
              
              <div className="occupancy-bar-container">
                <div 
                  className="occupancy-bar"
                  style={{ 
                    width: `${percentage}%`,
                    backgroundColor: barColor
                  }}
                />
              </div>
              
              <div className="department-footer">
                <span className="occupancy-percentage">
                  {percentage.toFixed(0)}%
                </span>
                <span 
                  className="occupancy-status"
                  style={{ color: barColor }}
                >
                  {status}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Podsumowanie */}
      <div className="occupancy-summary">
        <div className="summary-item">
          <span className="summary-label">Całkowite obłożenie:</span>
          <span className="summary-value">
            {occupancy.total_occupancy}/{occupancy.total_capacity}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Procent:</span>
          <span className="summary-value">
            {occupancy.overall_percentage.toFixed(1)}%
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Dostępne łóżka:</span>
          <span className="summary-value">
            {occupancy.total_capacity - occupancy.total_occupancy}
          </span>
        </div>
      </div>

      {/* Legenda */}
      <div className="occupancy-legend">
        <h4>Legenda</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#d4f5b3' }} />
            <span>&lt;40% NISKIE</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#a7eb67' }} />
            <span>40-60% ŚREDNIE</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#6b9c3d' }} />
            <span>60-80% WYSOKIE</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#2d5016' }} />
            <span>&gt;80% KRYTYCZNE</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeatMap;
