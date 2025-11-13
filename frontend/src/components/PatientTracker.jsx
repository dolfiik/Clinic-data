import { useState } from 'react';
import { getPatientLocation } from '../services/api';

const PatientTracker = () => {
  const [patientId, setPatientId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [patientData, setPatientData] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!patientId.trim()) {
      setError('Wprowadź ID pacjenta');
      return;
    }

    setError('');
    setLoading(true);
    setPatientData(null);

    try {
      const data = await getPatientLocation(parseInt(patientId));
      setPatientData(data);
    } catch (err) {
      console.error('Błąd wyszukiwania pacjenta:', err);
      
      if (err.response?.status === 404) {
        setError(`Nie znaleziono pacjenta o ID: ${patientId}`);
      } else {
        setError(err.response?.data?.detail || 'Błąd podczas wyszukiwania pacjenta');
      }
    } finally {
      setLoading(false);
    }
  };

  const getCategoryInfo = (category) => {
    const categories = {
      1: { label: 'NATYCHMIASTOWY', color: '#d32f2f', icon: '🔴' },
      2: { label: 'PILNY', color: '#f57c00', icon: '🟠' },
      3: { label: 'STABILNY', color: '#fbc02d', icon: '🟡' },
      4: { label: 'NISKI PRIORYTET', color: '#7cb342', icon: '🟢' },
      5: { label: 'BARDZO NISKI', color: '#66bb6a', icon: '🟢' }
    };
    return categories[category] || categories[3];
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('pl-PL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateTimeOnDepartment = (admissionDate) => {
    const now = new Date();
    const admission = new Date(admissionDate);
    const diffMs = now - admission;
    
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
      return `${hours}h ${minutes}min`;
    }
    return `${minutes}min`;
  };

  return (
    <div className="patient-tracker">
      <h2>🔍 Znajdź Pacjenta</h2>
      
      <form onSubmit={handleSearch}>
        <div className="search-box">
          <input
            type="number"
            className="search-input"
            placeholder="Wprowadź ID pacjenta..."
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            disabled={loading}
            min="1"
          />
          <button 
            type="submit"
            className="btn-search"
            disabled={loading}
          >
            {loading ? 'Szukam...' : 'Szukaj'}
          </button>
        </div>
      </form>

      {error && (
        <div className="tracker-error">
           {error}
        </div>
      )}

      {patientData && (
        <div className="patient-card found">
          <div className="patient-header">
            <span className="status-icon">✓</span>
            <h3>Pacjent #{patientData.patient_id}</h3>
          </div>

          <div className="patient-details">
            <div className="detail-item">
              <div className="detail-label">Wiek</div>
              <div className="detail-value">
                {patientData.wiek} lat ({patientData.plec === 'M' ? 'Mężczyzna' : 'Kobieta'})
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-label">Kategoria triażu</div>
              <div className="detail-value" style={{ color: getCategoryInfo(patientData.kategoria_triazu).color }}>
                {getCategoryInfo(patientData.kategoria_triazu).icon} {patientData.kategoria_triazu} - {getCategoryInfo(patientData.kategoria_triazu).label}
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-label">Data przyjęcia</div>
              <div className="detail-value">
                {formatDate(patientData.data_przyjecia)}
              </div>
            </div>

            <div className="detail-item">
              <div className="detail-label">Czas na oddziale</div>
              <div className="detail-value">
                {calculateTimeOnDepartment(patientData.data_przyjecia)}
              </div>
            </div>

            <div className="current-department">
              <div className="detail-label"> Aktualnie na oddziale</div>
              <div className="detail-value">{patientData.przypisany_oddzial}</div>
            </div>

            {patientData.status && (
              <div className="detail-item" style={{ gridColumn: '1 / -1', marginTop: '8px' }}>
                <div className="detail-label">Status</div>
                <div className="detail-value">
                  {patientData.status === 'oczekujący' && ' Oczekujący'}
                  {patientData.status === 'w_leczeniu' && ' W leczeniu'}
                  {patientData.status === 'wypisany' && ' Wypisany'}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {!patientData && !error && !loading && (
        <div className="patient-card">
          <p style={{ textAlign: 'center', color: '#999', margin: 0 }}>
            Wprowadź ID pacjenta, aby wyszukać jego aktualną lokalizację
          </p>
        </div>
      )}
    </div>
  );
};

export default PatientTracker;
