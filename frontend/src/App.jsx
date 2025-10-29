import { useState, useEffect, useRef } from 'react';
import LoginForm from './components/LoginForm';
import TriageForm from './components/TriageForm';
import TriageResult from './components/TriageResult';
import HeatMap from './components/HeatMap';
import { logout, getAuthToken } from './services/api';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [triageResult, setTriageResult] = useState(null);
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
  };

  const handlePredictionComplete = (result) => {
    setTriageResult(result);
  };

  const handleCloseResult = () => {
    setTriageResult(null);
  };

  // NOWE: Callback po utworzeniu pacjenta
  const handlePatientCreated = (response) => {
    console.log('Pacjent utworzony:', response);
    
    // Odśwież heatmapę
    if (heatMapRef.current && heatMapRef.current.refresh) {
      heatMapRef.current.refresh();
    }
    
    // Można dodać toast notification
    // toast.success(`Pacjent #${response.patient_id} dodany do systemu!`);
  };

  if (!isLoggedIn) {
    return <LoginForm onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>System Triażu Szpitalnego</h1>
        <div className="header-right">
          <span className="user-email">{user?.email}</span>
          <button onClick={handleLogout} className="btn-logout">
            Wyloguj
          </button>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
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
      </div>
    </div>
  );
}

export default App;
