import { useState } from 'react';
import { confirmAndCreatePatient } from '../services/api';

const TriageResult = ({ result, onClose, onPatientCreated }) => {
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState('');
  
  // Edytowalne wartości (z możliwością zmiany przez użytkownika)
  const [selectedCategory, setSelectedCategory] = useState(
    result?.prediction?.kategoria_triazu || 3
  );
  const [selectedDepartment, setSelectedDepartment] = useState(
    result?.prediction?.przypisany_oddzial || 'SOR'
  );

  if (!result) return null;

  const { formData, prediction } = result;

  // Sprawdź czy użytkownik zmienił wartości
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

  // Lista dostępnych oddziałów (z backendu lub hardcoded)
  const availableDepartments = prediction.dostepne_oddzialy || [
    'SOR',
    'Interna', 
    'Kardiologia',
    'Chirurgia',
    'Ortopedia',
    'Neurologia',
    'Pediatria',
    'Ginekologia'
  ];

  const handleConfirm = async () => {
    setError('');
    setConfirming(true);

    try {
      // Przygotuj dane do potwierdzenia
      const confirmData = {
        ...formData, // Wszystkie oryginalne dane pacjenta
        kategoria_triazu: selectedCategory,
        przypisany_oddzial: selectedDepartment
      };

      // Wywołaj API confirm - tworzy pacjenta w bazie
      const response = await confirmAndCreatePatient(confirmData);
      
      console.log('✅ Pacjent utworzony:', response);

      // Powiadom rodzica (App.jsx) żeby odświeżyć heatmapę
      if (onPatientCreated) {
        onPatientCreated(response);
      }

      // Zamknij modal po sukcesie
      setTimeout(() => {
        onClose();
      }, 1000);

    } catch (err) {
      console.error('❌ Błąd podczas tworzenia pacjenta:', err);
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
        <h2>Wynik Triażu</h2>
        <button onClick={onClose} className="btn-close">✕</button>
      </div>

      <div className="result-content">
        {/* Kategoria triażu - ORYGINALNY WYNIK */}
        <div className="result-section">
          <div 
            className="category-badge"
            style={{ 
              backgroundColor: categoryInfo.color,
              color: 'white'
            }}
          >
            <div className="category-number">
              {prediction.kategoria_triazu}
            </div>
            <div className="category-label">
              {categoryInfo.label}
            </div>
          </div>
        </div>

        {/* Przypisany oddział - ORYGINALNY */}
        <div className="result-section">
          <h3>Przypisany oddział</h3>
          <div className="result-value large">
            {prediction.przypisany_oddzial}
          </div>
        </div>

        {/* Priorytet */}
        <div className="result-section">
          <h3>Priorytet</h3>
          <div className="result-value">
            {categoryInfo.priority}
          </div>
        </div>

        {/* Pewność predykcji */}
        <div className="result-section">
          <h3>Pewność predykcji</h3>
          <div className="result-value">
            {(prediction.confidence_score * 100).toFixed(1)}%
          </div>
        </div>

        {/* Opis kategorii */}
        {prediction.opis_kategorii && (
          <div className="result-section">
            <h3>Opis</h3>
            <div className="result-value" style={{ fontSize: '14px' }}>
              {prediction.opis_kategorii}
            </div>
          </div>
        )}
      </div>

      {/* ============================================
          FORMULARZ POTWIERDZENIA
          ============================================ */}
      <div className="confirmation-form">
        <div className="confirmation-header">
          <h3>Potwierdź i utwórz pacjenta</h3>
          <p className="confirmation-note">
            Możesz zmodyfikować kategorię triażu lub przypisany oddział przed utworzeniem pacjenta w systemie.
          </p>
        </div>

        {error && (
          <div className="error-message" style={{ marginBottom: '16px' }}>
            {error}
          </div>
        )}

        {/* Select kategorii */}
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

        {/* Select oddziału */}
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

        {/* Informacja o modyfikacji */}
        {isModified && (
          <div className="modification-notice">
             Wartości zostały zmodyfikowane ręcznie
          </div>
        )}

        {/* Przycisk potwierdzenia */}
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
