import { useState } from 'react';
import { login, setAuthToken } from '../services/api';

const LoginForm = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await login(email, password);
      console.log('LOGIN SUCCESS:', data);
      console.log('Token received:', data.access_token);
      setAuthToken(data.access_token);
      console.log('Token saved:', localStorage.getItem('token'));
      localStorage.setItem('user', JSON.stringify({ email }));
      
      onLoginSuccess(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        'Błąd logowania. Sprawdź dane i spróbuj ponownie.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>System Triażu Szpitalnego</h1>
        <p className="subtitle">Zaloguj się do systemu</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              placeholder="twoj.email@szpital.pl"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Hasło</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={loading}
              placeholder="••••••••"
            />
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button 
            type="submit" 
            className="btn-primary"
            disabled={loading}
          >
            {loading ? 'Logowanie...' : 'Zaloguj się'}
          </button>
        </form>

        <div className="login-info">
          <p>Testowe konto:</p>
          <p>Email: dr.kowalski@clinic.local</p>
          <p>Hasło: password123</p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
