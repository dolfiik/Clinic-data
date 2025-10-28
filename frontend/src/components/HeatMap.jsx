import { useState, useEffect } from 'react';
import { getDepartmentOccupancy } from '../services/api';

const HeatMap = ({ isLoggedIn }) => {
  const [occupancy, setOccupancy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    
    if (!isLoggedIn) {
      setLoading(false);
      return;
    }

    // Małe opóźnienie dla pewności że token jest zapisany
    const timer = setTimeout(() => {
      fetchOccupancy();
    }, 150);

    const interval = setInterval(fetchOccupancy, 30000);
    
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [isLoggedIn]);

  const fetchOccupancy = async () => {
    const token = localStorage.getItem('token');
    
    try {
      const data = await getDepartmentOccupancy();
      setOccupancy(data);
      setError('');
    } catch (err) {
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
      <div className="heatmap-container">
        <div className="loading">Ładowanie danych...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="heatmap-container">
        <div className="error">{error}</div>
      </div>
    );
  }

  if (!occupancy) {
    return (
      <div className="heatmap-container">
        <div className="no-data">Brak danych</div>
      </div>
    );
  }

  return (
    <div className="heatmap-container">
      <div className="heatmap-header">
        <h2>Obłożenie Oddziałów</h2>
        <span className="last-update">
          Ostatnia aktualizacja: {new Date(occupancy.timestamp).toLocaleString('pl-PL')}
        </span>
      </div>

      <div className="heatmap-summary">
        <div className="summary-item">
          <span className="summary-label">Całkowite obłożenie:</span>
          <span className="summary-value">
            {occupancy.total_occupancy}/{occupancy.total_capacity}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Procent obłożenia:</span>
          <span className="summary-value">
            {occupancy.overall_percentage.toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="heatmap-grid">
        {Object.values(occupancy.departments).map((dept) => (
          <div 
            key={dept.name}
            className="department-card"
            style={{ backgroundColor: getOccupancyColor(dept.occupancy_percentage) }}
          >
            <h3>{dept.name}</h3>
            <div className="occupancy-info">
              <div className="occupancy-numbers">
                <span className="occupancy-current">{dept.current_occupancy}</span>
                <span className="occupancy-separator">/</span>
                <span className="occupancy-capacity">{dept.capacity}</span>
              </div>
              <div className="occupancy-percentage">
                {dept.occupancy_percentage.toFixed(1)}%
              </div>
              <div className={`status-badge status-${dept.status.toLowerCase()}`}>
                {getStatusLabel(dept.occupancy_percentage)}
              </div>
              <div className="available-beds">
                Dostępne łóżka: {dept.available_beds}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="heatmap-legend">
        <h4>Legenda:</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#d4f5b3' }}></div>
            <span>Niskie (&lt;40%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#a7eb67' }}></div>
            <span>Średnie (40-60%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#6b9c3d' }}></div>
            <span>Wysokie (60-80%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#2d5016' }}></div>
            <span>Krytyczne (≥80%)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeatMap;
