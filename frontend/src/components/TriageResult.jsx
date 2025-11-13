import { useState, useEffect } from 'react';
import { confirmAndCreatePatient, getOccupancyForecast } from '../services/api';
import OccupancyChart from './OccupancyChart';

const TriageResult = ({ result, onClose, onPatientCreated }) => {
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState('');
  const [occupancyData, setOccupancyData] = useState(null);
  const [loadingForecast, setLoadingForecast] = useState(true);
  
  const [selectedCategory, setSelectedCategory] = useState(
    result?.prediction?.kategoria_triazu || 3
  );
  const [selectedDepartment, setSelectedDepartment] = useState(
    result?.prediction?.przypisany_oddzial || 'SOR'
  );

  useEffect(() => {
    const fetchForecast = async () => {
      try {
        setLoadingForecast(true);
        const forecast = await getOccupancyForecast();
        setOccupancyData(forecast);
      } catch (err) {
        console.error('Błąd pobierania prognoz:', err);
      } finally {
        setLoadingForecast(false);
      }
    };

    fetchForecast();
  }, []);

  if (!result) return null;

  const { formData, prediction } = result;

  const isModified = 
    selectedCategory !== prediction.kategoria_triazu ||
    selectedDepartment !== prediction.przypisany_oddzial;

  const getCategoryInfo = (category) => {
    const categories = {
      1: { label: 'NATYCHMIASTOWY', color: '#d32f2f', priority: 'RESUSCYTACJA' },
      2: { label: 'PILNY', color: '#f57c00', priority: 'CIĘŻKI STAN' },
      3: { label: 'STABILNY', color: '#fbc02d', priority: 'STABILNY' },
      4: { label: 'NISKI PRIORYTET', color: '#7cb342', priority: 'NISKI' },
      5: { label: 'BARDZO NISKI', color: '#66bb6a', priority: 'BARDZO NISKI' }
    };
    return categories[category] || categories[3];
  };

  const categoryInfo = getCategoryInfo(prediction.kategoria_triazu);

  const availableDepartments = prediction.dostepne_oddzialy || [
    'SOR',
    'Interna', 
    'Kardiologia',
    'Chirurgia',
    'Ortopedia',
    'Neurologia'
  ];

  const departmentCapacity = {
    'SOR': 25,
    'Interna': 50,
    'Kardiologia': 30,
    'Chirurgia': 35,
    'Ortopedia': 25,
    'Neurologia': 20,
    'Pediatria': 30,
    'Ginekologia': 20
  };

  const getCurrentOccupancy = (dept) => {
    if (!occupancyData || !occupancyData.current) return 0;
    return occupancyData.current[dept] || 0;
  };

  const getForecast = (dept) => {
    if (!occupancyData || !occupancyData.forecast) return {};
    const deptForecast = occupancyData.forecast[dept] || {};
    return {
      hour_1: deptForecast.hour_1 || getCurrentOccupancy(dept),
      hour_2: deptForecast.hour_2 || getCurrentOccupancy(dept),
      hour_3: deptForecast.hour_3 || getCurrentOccupancy(dept)
    };
  };

  const getAlternatives = () => {
    // TODO: To powinno przyjść z Model 3 (Department Allocation)
    const alternatives = [];
    const assignedDept = prediction.przypisany_oddzial;
    
    availableDepartments.forEach(dept => {
      if (dept !== assignedDept) {
        const currentOcc = getCurrentOccupancy(dept);
        const capacity = departmentCapacity[dept] || 30;
        const percentage = ((currentOcc / capacity) * 100).toFixed(0);
        
        alternatives.push({
          name: dept,
          confidence: Math.random() * 0.5 + 0.3, 
          current_occupancy: currentOcc,
          capacity: capacity,
          percentage: percentage
        });
      }
    });

    return alternatives.sort((a, b) => b.confidence - a.confidence).slice(0, 3);
  };

  const handleConfirm = async () => {
    setError('');
    setConfirming(true);

    try {
      const confirmData = {
        ...formData, 
        kategoria_triazu: selectedCategory,
        przypisany_oddzial: selectedDepartment
      };

      const response = await confirmAndCreatePatient(confirmData);
      
      console.log(' Pacjent utworzony:', response);

      if (onPatientCreated) {
        onPatientCreated(response);
      }

      setTimeout(() => {
        onClose();
      }, 1000);

    } catch (err) {
      console.error(' Błąd podczas tworzenia pacjenta:', err);
      setError(
        err.response?.data?.detail || 
        'Błąd podczas dodawania pacjenta do systemu.'
      );
    } finally {
      setConfirming(false);
    }
  };

  return (
    <div className="triage-result">
      <div className="result-header">
        <h2> Wynik Predykcji</h2>
        <button className="btn-close" onClick={onClose}>✕</button>
      </div>

      <div className="result-content">
        <div className="result-section">
          <h3>Kategoria Triażu</h3>
          <div className="category-badge" style={{ borderColor: categoryInfo.color }}>
            <span className="category-icon" style={{ backgroundColor: categoryInfo.color }}>
              {prediction.kategoria_triazu}
            </span>
            <div className="category-details">
              <div className="category-label" style={{ color: categoryInfo.color }}>
                {categoryInfo.label}
              </div>
              <div className="category-priority">
                {categoryInfo.priority}
              </div>
              <div className="category-confidence">
                Pewność: {(prediction.confidence_score * 100).toFixed(0)}%
              </div>
            </div>
          </div>

          <div className="probabilities">
            <p><strong>Prawdopodobieństwa:</strong></p>
            {Object.entries(prediction.probabilities).map(([cat, prob]) => (
              <div key={cat} className="prob-item">
                <span>Kategoria {cat}:</span>
                <div className="prob-bar">
                  <div 
                    className="prob-fill" 
                    style={{ width: `${prob * 100}%` }}
                  />
                </div>
                <span className="prob-value">{(prob * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="result-section">
          <h3>Przypisany Oddział</h3>
          <div className="department-badge">
             {prediction.przypisany_oddzial}
          </div>
          <p className="department-description">
            {prediction.opis_kategorii}
          </p>

          {!loadingForecast && occupancyData && (
            <OccupancyChart
              department={selectedDepartment}
              currentOccupancy={getCurrentOccupancy(selectedDepartment)}
              forecast={getForecast(selectedDepartment)}
              capacity={departmentCapacity[selectedDepartment] || 30}
            />
          )}

          {loadingForecast && (
            <div className="loading-forecast">
              Ładowanie prognoz obłożenia...
            </div>
          )}

          {getAlternatives().length > 0 && (
            <div className="alternatives-section">
              <h4>Alternatywne oddziały:</h4>
              {getAlternatives().map(alt => (
                <div key={alt.name} className="alternative-item">
                  <div>
                    <span className="alternative-name">{alt.name}</span>
                    <span className="alternative-confidence">
                      {' '}({(alt.confidence * 100).toFixed(0)}%)
                    </span>
                  </div>
                  <span className="alternative-occupancy">
                    Obłożenie: {alt.current_occupancy}/{alt.capacity} ({alt.percentage}%)
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {error && (
          <div className="error-message" style={{ marginBottom: '16px' }}>
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="category-select">Kategoria triażu</label>
          <select
            id="category-select"
            className="category-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(parseInt(e.target.value))}
            disabled={confirming}
          >
            <option value={1}>1 - NATYCHMIASTOWY (Resuscytacja)</option>
            <option value={2}>2 - PILNY (Ciężki stan)</option>
            <option value={3}>3 - STABILNY (Pilny)</option>
            <option value={4}>4 - NISKI PRIORYTET</option>
            <option value={5}>5 - BARDZO NISKI</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="department-select">Przypisany oddział</label>
          <select
            id="department-select"
            className="department-select"
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            disabled={confirming}
          >
            {availableDepartments.map(dept => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
        </div>

        {isModified && (
          <div className="modification-notice">
             Wartości zostały zmodyfikowane ręcznie
          </div>
        )}

        <button
          className="btn-confirm"
          onClick={handleConfirm}
          disabled={confirming}
        >
          {confirming ? 'Tworzenie pacjenta...' : 'Potwierdź i dodaj pacjenta'}
        </button>
      </div>
    </div>
  );
};

export default TriageResult;
