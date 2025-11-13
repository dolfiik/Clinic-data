import { useState, useEffect, useRef } from 'react';
import LoginForm from './components/LoginForm';
import TriageForm from './components/TriageForm';
import TriageResult from './components/TriageResult';
import HeatMap from './components/HeatMap';
import PatientTracker from './components/PatientTracker';
import { logout, getAuthToken } from './services/api';
import './App.css';
import './styles/chart-styles.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [triageResult, setTriageResult] = useState(null);
  const [activeView, setActiveView] = useState('triage'); // 'triage' lub 'tracker'
  const heatMapRef = useRef(null);

  useEffect(() => {
    const token = getAuthToken();
    const savedUser = localStorage.getItem('user');
    
    if (token && savedUser) {
      setIsLoggedIn(true);
      setUser(JSON.parse(savedUser));
    }
  }, []);

  const handleLoginSuccess = (data) => {
    const userEmail = JSON.parse(localStorage.getItem('user'))?.email;
    setUser({ email: userEmail });
    
    setTimeout(() => {
      setIsLoggedIn(true);
    }, 100);
  };

  const handleLogout = async () => {
    await logout();
    setIsLoggedIn(false);
    setUser(null);
    setTriageResult(null);
    setActiveView('triage');
  };

  const handlePredictionComplete = (result) => {
    setTriageResult(result);
  };

  const handleCloseResult = () => {
    setTriageResult(null);
  };

  // Callback po utworzeniu pacjenta
  const handlePatientCreated = (response) => {
    console.log('Pacjent utworzony:', response);
    
    if (heatMapRef.current && heatMapRef.current.refresh) {
      heatMapRef.current.refresh();
    }
  };

  if (!isLoggedIn) {
    return <LoginForm onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1> System Triażu Szpitalnego</h1>
        <div className="header-right">
          <div className="nav-tabs">
            <button 
              className={`nav-tab ${activeView === 'triage' ? 'active' : ''}`}
              onClick={() => setActiveView('triage')}
            >
               Nowy Triaz
            </button>
            <button 
              className={`nav-tab ${activeView === 'tracker' ? 'active' : ''}`}
              onClick={() => setActiveView('tracker')}
            >
               Znajdź Pacjenta
            </button>
          </div>
          <span className="user-email">{user?.email}</span>
          <button onClick={handleLogout} className="btn-logout">
            Wyloguj
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {activeView === 'triage' ? (
          <>
            {/* Lewa strona - Formularz + Wynik */}
            <div className="left-panel">
              <TriageForm onPredictionComplete={handlePredictionComplete} />
              
              {triageResult && (
                <TriageResult 
                  result={triageResult} 
                  onClose={handleCloseResult}
                  onPatientCreated={handlePatientCreated}
                />
              )}
            </div>

            {/* Prawa strona - HeatMap */}
            <div className="right-panel">
              {isLoggedIn && user && (
                <HeatMap 
                  ref={heatMapRef}
                  isLoggedIn={isLoggedIn} 
                />
              )}
            </div>
          </>
        ) : (
          /* Patient Tracker View */
          <div className="tracker-view">
            <PatientTracker />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
