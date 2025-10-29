import { useState } from 'react';
import { previewTriage } from '../services/api';
import TemplateSelect from './TemplateSelect';

const TriageForm = ({ onPredictionComplete }) => {
  const [formData, setFormData] = useState({
    wiek: '',
    plec: 'M',
    tetno: '',
    cisnienie_skurczowe: '',
    cisnienie_rozkurczowe: '',
    temperatura: '',
    saturacja: '',
    gcs: '',
    bol: '',
    czestotliwosc_oddechow: '',
    czas_od_objawow_h: '',
    szablon_przypadku: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Przygotuj dane
      const patientData = {
        ...formData,
        wiek: parseInt(formData.wiek),
        tetno: parseFloat(formData.tetno),
        cisnienie_skurczowe: parseFloat(formData.cisnienie_skurczowe),
        cisnienie_rozkurczowe: parseFloat(formData.cisnienie_rozkurczowe),
        temperatura: parseFloat(formData.temperatura),
        saturacja: parseFloat(formData.saturacja),
        gcs: parseInt(formData.gcs),
        bol: parseInt(formData.bol),
        czestotliwosc_oddechow: parseFloat(formData.czestotliwosc_oddechow),
        czas_od_objawow_h: parseFloat(formData.czas_od_objawow_h),
        szablon_przypadku: formData.szablon_przypadku || null
      };

      // 🔥 ZMIANA: Używamy preview zamiast tworzyć pacjenta
      const prediction = await previewTriage(patientData);

      // Przekaż ORYGINALNE dane formularza + predykcję do rodzica
      onPredictionComplete({ 
        formData: patientData,  // Oryginalne dane do późniejszego utworzenia pacjenta
        prediction              // Predykcja modelu
      });

      // Wyczyść formularz
      setFormData({
        wiek: '',
        plec: 'M',
        tetno: '',
        cisnienie_skurczowe: '',
        cisnienie_rozkurczowe: '',
        temperatura: '',
        saturacja: '',
        gcs: '',
        bol: '',
        czestotliwosc_oddechow: '',
        czas_od_objawow_h: '',
        szablon_przypadku: ''
      });

    } catch (err) {
      console.error('Error:', err);
      setError(
        err.response?.data?.detail || 
        'Błąd podczas przetwarzania danych. Sprawdź poprawność wprowadzonych wartości.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="triage-form">
      <h2>Formularz Triażu</h2>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Dane podstawowe */}
        <div className="form-section">
          <h3>Dane podstawowe</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="wiek">Wiek (lata)</label>
              <input
                type="number"
                id="wiek"
                name="wiek"
                value={formData.wiek}
                onChange={handleChange}
                required
                min="0"
                max="120"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Płeć</label>
              <div className="radio-group">
                <label>
                  <input
                    type="radio"
                    name="plec"
                    value="M"
                    checked={formData.plec === 'M'}
                    onChange={handleChange}
                    disabled={loading}
                  />
                  Mężczyzna
                </label>
                <label>
                  <input
                    type="radio"
                    name="plec"
                    value="K"
                    checked={formData.plec === 'K'}
                    onChange={handleChange}
                    disabled={loading}
                  />
                  Kobieta
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Parametry vitalne */}
        <div className="form-section">
          <h3>Parametry vitalne</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="tetno">Tętno (uderzeń/min)</label>
              <input
                type="number"
                id="tetno"
                name="tetno"
                value={formData.tetno}
                onChange={handleChange}
                required
                step="0.1"
                min="30"
                max="220"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="temperatura">Temperatura (°C)</label>
              <input
                type="number"
                id="temperatura"
                name="temperatura"
                value={formData.temperatura}
                onChange={handleChange}
                required
                step="0.1"
                min="30"
                max="45"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cisnienie_skurczowe">Ciśnienie skurczowe (mmHg)</label>
              <input
                type="number"
                id="cisnienie_skurczowe"
                name="cisnienie_skurczowe"
                value={formData.cisnienie_skurczowe}
                onChange={handleChange}
                required
                step="0.1"
                min="50"
                max="250"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="cisnienie_rozkurczowe">Ciśnienie rozkurczowe (mmHg)</label>
              <input
                type="number"
                id="cisnienie_rozkurczowe"
                name="cisnienie_rozkurczowe"
                value={formData.cisnienie_rozkurczowe}
                onChange={handleChange}
                required
                step="0.1"
                min="30"
                max="150"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="saturacja">Saturacja (%)</label>
              <input
                type="number"
                id="saturacja"
                name="saturacja"
                value={formData.saturacja}
                onChange={handleChange}
                required
                step="0.1"
                min="50"
                max="100"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="czestotliwosc_oddechow">Częstotliwość oddechów (/min)</label>
              <input
                type="number"
                id="czestotliwosc_oddechow"
                name="czestotliwosc_oddechow"
                value={formData.czestotliwosc_oddechow}
                onChange={handleChange}
                required
                step="0.1"
                min="5"
                max="60"
                disabled={loading}
              />
            </div>
          </div>
        </div>

        {/* Ocena kliniczna */}
        <div className="form-section">
          <h3>Ocena kliniczna</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="gcs">GCS (3-15)</label>
              <input
                type="number"
                id="gcs"
                name="gcs"
                value={formData.gcs}
                onChange={handleChange}
                required
                min="3"
                max="15"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="bol">Ból (0-10)</label>
              <input
                type="number"
                id="bol"
                name="bol"
                value={formData.bol}
                onChange={handleChange}
                required
                min="0"
                max="10"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="czas_od_objawow_h">Czas od objawów (godziny)</label>
            <input
              type="number"
              id="czas_od_objawow_h"
              name="czas_od_objawow_h"
              value={formData.czas_od_objawow_h}
              onChange={handleChange}
              required
              step="0.1"
              min="0"
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="szablon_przypadku">Szablon przypadku (opcjonalnie)</label>
            <TemplateSelect
              value={formData.szablon_przypadku}
              onChange={handleChange}
              disabled={loading}
            />
          </div>
        </div>

        <button 
          type="submit" 
          className="btn-primary btn-large"
          disabled={loading}
        >
          {loading ? 'Przetwarzanie...' : 'Wykonaj Triaz'}
        </button>
      </form>
    </div>
  );
};

export default TriageForm;
