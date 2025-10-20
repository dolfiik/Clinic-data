DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS department_occupancy CASCADE;
DROP TABLE IF EXISTS triage_predictions CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255), -- NULL dla OAuth
    oauth_provider VARCHAR(50), -- 'google', 'azure', etc.
    oauth_id VARCHAR(255),
    role VARCHAR(50) DEFAULT 'nurse' CHECK (role IN ('admin', 'doctor', 'nurse', 'receptionist')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT unique_oauth UNIQUE(oauth_provider, oauth_id)
);

-- Indeksy dla wydajności
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_id);
CREATE INDEX idx_users_role ON users(role);

COMMENT ON TABLE users IS 'Użytkownicy systemu - personel medyczny';
COMMENT ON COLUMN users.password_hash IS 'Zahashowane hasło (bcrypt) - NULL dla użytkowników OAuth';
COMMENT ON COLUMN users.role IS 'Rola: admin, doctor, nurse, receptionist';

CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    
    wiek INTEGER NOT NULL CHECK (wiek >= 0 AND wiek <= 120),
    plec CHAR(1) NOT NULL CHECK (plec IN ('M', 'K')),
    
    tetno DECIMAL(5,1) CHECK (tetno >= 0 AND tetno <= 300),
    cisnienie_skurczowe DECIMAL(5,1) CHECK (cisnienie_skurczowe >= 0 AND cisnienie_skurczowe <= 300),
    cisnienie_rozkurczowe DECIMAL(5,1) CHECK (cisnienie_rozkurczowe >= 0 AND cisnienie_rozkurczowe <= 200),
    temperatura DECIMAL(4,1) CHECK (temperatura >= 30 AND temperatura <= 45),
    saturacja DECIMAL(4,1) CHECK (saturacja >= 0 AND saturacja <= 100),
    gcs INTEGER CHECK (gcs >= 3 AND gcs <= 15),
    bol INTEGER CHECK (bol >= 0 AND bol <= 10),
    czestotliwosc_oddechow DECIMAL(5,1) CHECK (czestotliwosc_oddechow >= 0 AND czestotliwosc_oddechow <= 100),
    
    czas_od_objawow_h DECIMAL(8,2) CHECK (czas_od_objawow_h >= 0),
    szablon_przypadku VARCHAR(100),
    
    -- Metadane
    data_przyjecia TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    wprowadzony_przez INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'oczekujący' CHECK (status IN ('oczekujący', 'w_leczeniu', 'wypisany', 'przekazany')),
    
    -- Pola pomocnicze
    notatki TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indeksy
CREATE INDEX idx_patients_data_przyjecia ON patients(data_przyjecia DESC);
CREATE INDEX idx_patients_status ON patients(status);
CREATE INDEX idx_patients_wprowadzony ON patients(wprowadzony_przez);
CREATE INDEX idx_patients_szablon ON patients(szablon_przypadku);

CREATE TABLE triage_predictions (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    
    -- Wyniki predykcji
    kategoria_triazu INTEGER NOT NULL CHECK (kategoria_triazu BETWEEN 1 AND 5),
    
    -- Prawdopodobieństwa dla każdej kategorii
    prob_kat_1 DECIMAL(5,4) CHECK (prob_kat_1 BETWEEN 0 AND 1),
    prob_kat_2 DECIMAL(5,4) CHECK (prob_kat_2 BETWEEN 0 AND 1),
    prob_kat_3 DECIMAL(5,4) CHECK (prob_kat_3 BETWEEN 0 AND 1),
    prob_kat_4 DECIMAL(5,4) CHECK (prob_kat_4 BETWEEN 0 AND 1),
    prob_kat_5 DECIMAL(5,4) CHECK (prob_kat_5 BETWEEN 0 AND 1),
    
    -- Przypisanie do oddziału
    przypisany_oddzial VARCHAR(50) NOT NULL,
    oddzial_docelowy VARCHAR(50),
    
    -- Metadane modelu
    model_version VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(5,4) CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- Timestampy
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_patient_prediction UNIQUE(patient_id)
);

-- Indeksy
CREATE INDEX idx_predictions_patient ON triage_predictions(patient_id);
CREATE INDEX idx_predictions_kategoria ON triage_predictions(kategoria_triazu);
CREATE INDEX idx_predictions_date ON triage_predictions(predicted_at DESC);
CREATE INDEX idx_predictions_oddzial ON triage_predictions(przypisany_oddzial);

COMMENT ON TABLE triage_predictions IS 'Wyniki predykcji modelu ML dla pacjentów';
COMMENT ON COLUMN triage_predictions.kategoria_triazu IS '1=Natychmiastowy, 2=Pilny, 3=Stabilny, 4=Niski priorytet, 5=Bardzo niski';
COMMENT ON COLUMN triage_predictions.confidence_score IS 'Pewność predykcji (max prawdopodobieństwo)';

CREATE TABLE department_occupancy (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    
    -- Obłożenie dla każdego oddziału
    sor INTEGER CHECK (sor >= 0) DEFAULT 0,
    interna INTEGER CHECK (interna >= 0) DEFAULT 0,
    kardiologia INTEGER CHECK (kardiologia >= 0) DEFAULT 0,
    chirurgia INTEGER CHECK (chirurgia >= 0) DEFAULT 0,
    ortopedia INTEGER CHECK (ortopedia >= 0) DEFAULT 0,
    neurologia INTEGER CHECK (neurologia >= 0) DEFAULT 0,
    pediatria INTEGER CHECK (pediatria >= 0) DEFAULT 0,
    ginekologia INTEGER CHECK (ginekologia >= 0) DEFAULT 0,
    
    -- Metadane
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_timestamp UNIQUE(timestamp)
);

CREATE INDEX idx_occupancy_timestamp ON department_occupancy(timestamp DESC);

COMMENT ON TABLE department_occupancy IS 'Historia obłożenia oddziałów (do treningu modelu LSTM)';

CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_action ON audit_log(action, timestamp DESC);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);


-- Funkcja do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger dla tabeli patients
CREATE TRIGGER update_patients_updated_at 
    BEFORE UPDATE ON patients
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();


CREATE VIEW patient_full_data AS
SELECT 
    p.*,
    tp.kategoria_triazu,
    tp.prob_kat_1,
    tp.prob_kat_2,
    tp.prob_kat_3,
    tp.prob_kat_4,
    tp.prob_kat_5,
    tp.przypisany_oddzial,
    tp.confidence_score,
    tp.predicted_at,
    u.username as wprowadzony_przez_username,
    u.email as wprowadzony_przez_email,
    u.role as wprowadzony_przez_role
FROM patients p
LEFT JOIN triage_predictions tp ON p.id = tp.patient_id
LEFT JOIN users u ON p.wprowadzony_przez = u.id;


CREATE VIEW daily_triage_stats AS
SELECT 
    DATE(data_przyjecia) as data,
    COUNT(*) as liczba_pacjentow,
    COUNT(CASE WHEN kategoria_triazu = 1 THEN 1 END) as kat_1_natychmiastowy,
    COUNT(CASE WHEN kategoria_triazu = 2 THEN 1 END) as kat_2_pilny,
    COUNT(CASE WHEN kategoria_triazu = 3 THEN 1 END) as kat_3_stabilny,
    COUNT(CASE WHEN kategoria_triazu = 4 THEN 1 END) as kat_4_niski,
    COUNT(CASE WHEN kategoria_triazu = 5 THEN 1 END) as kat_5_bardzo_niski,
    AVG(EXTRACT(EPOCH FROM (predicted_at - data_przyjecia))/60) as avg_czas_do_triazu_min,
    AVG(confidence_score) as avg_confidence
FROM patient_full_data
WHERE predicted_at IS NOT NULL
GROUP BY DATE(data_przyjecia)
ORDER BY data DESC;

CREATE OR REPLACE FUNCTION get_current_occupancy()
RETURNS TABLE (
    oddzial VARCHAR(50),
    aktualne_oblozenie INTEGER,
    pojemnosc INTEGER,
    procent_oblozenia DECIMAL(5,2),
    status VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    WITH latest AS (
        SELECT * FROM department_occupancy
        ORDER BY timestamp DESC
        LIMIT 1
    ),
    capacities AS (
        SELECT 'SOR' as dept, 25 as cap UNION ALL
        SELECT 'Interna', 50 UNION ALL
        SELECT 'Kardiologia', 30 UNION ALL
        SELECT 'Chirurgia', 35 UNION ALL
        SELECT 'Ortopedia', 25 UNION ALL
        SELECT 'Neurologia', 20 UNION ALL
        SELECT 'Pediatria', 30 UNION ALL
        SELECT 'Ginekologia', 20
    )
    SELECT 
        c.dept,
        CASE c.dept
            WHEN 'SOR' THEN l.sor
            WHEN 'Interna' THEN l.interna
            WHEN 'Kardiologia' THEN l.kardiologia
            WHEN 'Chirurgia' THEN l.chirurgia
            WHEN 'Ortopedia' THEN l.ortopedia
            WHEN 'Neurologia' THEN l.neurologia
            WHEN 'Pediatria' THEN l.pediatria
            WHEN 'Ginekologia' THEN l.ginekologia
        END as current_occ,
        c.cap,
        ROUND((CASE c.dept
            WHEN 'SOR' THEN l.sor
            WHEN 'Interna' THEN l.interna
            WHEN 'Kardiologia' THEN l.kardiologia
            WHEN 'Chirurgia' THEN l.chirurgia
            WHEN 'Ortopedia' THEN l.ortopedia
            WHEN 'Neurologia' THEN l.neurologia
            WHEN 'Pediatria' THEN l.pediatria
            WHEN 'Ginekologia' THEN l.ginekologia
        END::DECIMAL / c.cap * 100), 2),
        CASE 
            WHEN (CASE c.dept
                WHEN 'SOR' THEN l.sor
                WHEN 'Interna' THEN l.interna
                WHEN 'Kardiologia' THEN l.kardiologia
                WHEN 'Chirurgia' THEN l.chirurgia
                WHEN 'Ortopedia' THEN l.ortopedia
                WHEN 'Neurologia' THEN l.neurologia
                WHEN 'Pediatria' THEN l.pediatria
                WHEN 'Ginekologia' THEN l.ginekologia
            END::DECIMAL / c.cap) >= 0.9 THEN 'CRITICAL'
            WHEN (CASE c.dept
                WHEN 'SOR' THEN l.sor
                WHEN 'Interna' THEN l.interna
                WHEN 'Kardiologia' THEN l.kardiologia
                WHEN 'Chirurgia' THEN l.chirurgia
                WHEN 'Ortopedia' THEN l.ortopedia
                WHEN 'Neurologia' THEN l.neurologia
                WHEN 'Pediatria' THEN l.pediatria
                WHEN 'Ginekologia' THEN l.ginekologia
            END::DECIMAL / c.cap) >= 0.7 THEN 'HIGH'
            WHEN (CASE c.dept
                WHEN 'SOR' THEN l.sor
                WHEN 'Interna' THEN l.interna
                WHEN 'Kardiologia' THEN l.kardiologia
                WHEN 'Chirurgia' THEN l.chirurgia
                WHEN 'Ortopedia' THEN l.ortopedia
                WHEN 'Neurologia' THEN l.neurologia
                WHEN 'Pediatria' THEN l.pediatria
                WHEN 'Ginekologia' THEN l.ginekologia
            END::DECIMAL / c.cap) >= 0.5 THEN 'MEDIUM'
            ELSE 'LOW'
        END::VARCHAR(20)
    FROM capacities c
    CROSS JOIN latest l;
END;
$$ LANGUAGE plpgsql;
