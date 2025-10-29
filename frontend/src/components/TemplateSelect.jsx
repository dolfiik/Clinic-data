import React, { useState, useEffect } from 'react';
import { getAvailableTemplates } from '../services/api';

const TemplateSelect = ({ value, onChange, name = "szablon_przypadku", required = false }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setLoading(true);
        const data = await getAvailableTemplates();
        setTemplates(data);
        setError(null);
      } catch (err) {
        console.error('Błąd pobierania szablonów:', err);
        setError('Nie udało się pobrać listy szablonów');
        // Fallback - statyczna lista
        setTemplates([
          { value: "ból_brzucha_łagodny", label: "Ból brzucha (łagodny)" },
          { value: "infekcja_moczu", label: "Infekcja układu moczowego" },
          { value: "kontrola", label: "Kontrola / Badanie kontrolne" },
          { value: "migrena", label: "Migrena / Ból głowy" },
          { value: "przeziębienie", label: "Przeziębienie" },
          { value: "receptura", label: "Wypisanie recepty" },
          { value: "silne_krwawienie", label: "Silne krwawienie" },
          { value: "skręcenie_lekkie", label: "Skręcenie (lekkie)" },
          { value: "udar_ciężki", label: "Udar mózgu (ciężki)" },
          { value: "uraz_wielonarządowy", label: "Uraz wielonarządowy" },
          { value: "zaostrzenie_astmy", label: "Zaostrzenie astmy" },
          { value: "zapalenie_płuc_ciężkie", label: "Zapalenie płuc (ciężkie)" },
          { value: "zapalenie_wyrostka", label: "Zapalenie wyrostka" },
          { value: "zawał_STEMI", label: "Zawał serca (STEMI)" },
          { value: "złamanie_proste", label: "Złamanie (proste)" }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  if (loading) {
    return (
      <select disabled>
        <option>Ładowanie szablonów...</option>
      </select>
    );
  }

  return (
    <div className="template-select">
      <select
        name={name}
        value={value || ''}
        onChange={onChange}
        required={required}
        className="form-control"
      >
        <option value="">-- Wybierz rodzaj przypadku --</option>
        {templates.map((template) => (
          <option key={template.value} value={template.value}>
            {template.label}
          </option>
        ))}
      </select>
      {error && <small className="text-danger">{error}</small>}
    </div>
  );
};

export default TemplateSelect;
