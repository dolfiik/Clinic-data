import { useState } from 'react';
import { createPatient, predictTriage } from '../services/api';

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

      const patient = await createPatient(patientData);

      const prediction = await predictTriage(patient.id);

      onPredictionComplete({ patient, prediction });

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

      <form onSubmit={handleSubmit}>
        {/* Podstawowe dane */}
        <div className="form-section">
          <h3>Dane podstawowe</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label>Wiek (lata)</label>
              <input
                type="number"
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
              <label>Tętno (uderzeń/min)</label>
              <input
                type="number"
                name="tetno"
                value={formData.tetno}
                onChange={handleChange}
                required
                min="0"
                max="300"
                step="0.1"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Temperatura (°C)</label>
              <input
                type="number"
                name="temperatura"
                value={formData.temperatura}
                onChange={handleChange}
                required
                min="30"
                max="45"
                step="0.1"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Ciśnienie skurczowe (mmHg)</label>
              <input
                type="number"
                name="cisnienie_skurczowe"
                value={formData.cisnienie_skurczowe}
                onChange={handleChange}
                required
                min="0"
                max="300"
                step="0.1"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Ciśnienie rozkurczowe (mmHg)</label>
              <input
                type="number"
                name="cisnienie_rozkurczowe"
                value={formData.cisnienie_rozkurczowe}
                onChange={handleChange}
                required
                min="0"
                max="200"
                step="0.1"
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Saturacja (%)</label>
              <input
                type="number"
                name="saturacja"
                value={formData.saturacja}
                onChange={handleChange}
                required
                min="0"
                max="100"
                step="0.1"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Częstotliwość oddechów (/min)</label>
              <input
                type="number"
                name="czestotliwosc_oddechow"
                value={formData.czestotliwosc_oddechow}
                onChange={handleChange}
                required
                min="0"
                max="100"
                step="0.1"
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
              <label>GCS (3-15)</label>
              <input
                type="number"
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
              <label>Ból (0-10)</label>
              <input
                type="number"
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

          <div className="form-row">
            <div className="form-group">
              <label>Czas od objawów (godziny)</label>
              <input
                type="number"
                name="czas_od_objawow_h"
                value={formData.czas_od_objawow_h}
                onChange={handleChange}
                required
                min="0"
                step="0.1"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Szablon przypadku (opcjonalnie)</label>
              <input
                type="text"
                name="szablon_przypadku"
                value={formData.szablon_przypadku}
                onChange={handleChange}
                disabled={loading}
                placeholder="np. udar, zawał"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <button 
          type="submit" 
          className="btn-primary btn-large"
          disabled={loading}
        >
          {loading ? 'Przetwarzanie...' : 'Wykonaj Triąż'}
        </button>
      </form>
    </div>
  );
};

export default TriageForm;
