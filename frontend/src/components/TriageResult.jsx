const TriageResult = ({ result, onClose }) => {
  if (!result) return null;

  const { prediction } = result;

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

  return (
    <div className="triage-result">
      <div className="result-header">
        <h2>Wynik Triażu</h2>
        <button onClick={onClose} className="btn-close">✕</button>
      </div>

      <div className="result-content">
        {/* Kategoria triażu */}
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

        {/* Przypisany oddział */}
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
      </div>
    </div>
  );
};

export default TriageResult;
