INSERT INTO users (email, username, password_hash, role, is_active) VALUES
    ('admin@clinic.local', 'admin', '$2b$12$3OWOF8bIlDXICfj6JQMs1.avQwawC.sTXOScrpl2dYU9oT5WWfZ6C', 'admin', true),
    ('dr.kowalski@clinic.local', 'dr_kowalski', '$2b$12$3OWOF8bIlDXICfj6JQMs1.avQwawC.sTXOScrpl2dYU9oT5WWfZ6C', 'doctor', true),
    ('nurse.anna@clinic.local', 'nurse_anna', '$2b$12$3OWOF8bIlDXICfj6JQMs1.avQwawC.sTXOScrpl2dYU9oT5WWfZ6C', 'nurse', true),
    ('reception@clinic.local', 'reception', '$2b$12$3OWOF8bIlDXICfj6JQMs1.avQwawC.sTXOScrpl2dYU9oT5WWfZ6C', 'receptionist', true);
-- password123

INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia, notatki
) VALUES (
    67, 'M', 125, 95, 55, 37.2, 88, 14, 9, 28,
    2.5, 'zawał_STEMI', 'oczekujący', 3,
    NOW() - INTERVAL '10 minutes',
    'Pacjent z bólem w klatce piersiowej, promieniującym do lewej ręki. Pilna interwencja'
);

-- Przypadek 2: Udar ciężki (kategoria 1)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    72, 'K', 85, 180, 110, 37.8, 92, 10, 3, 20,
    1.0, 'udar_ciężki', 'oczekujący', 3,
    NOW() - INTERVAL '5 minutes'
);

-- Przypadek 3: Zapalenie płuc ciężkie (kategoria 2 - pilny)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    45, 'M', 105, 125, 75, 39.5, 89, 15, 6, 30,
    24, 'zapalenie_płuc_ciężkie', 'oczekujący', 3,
    NOW() - INTERVAL '30 minutes'
);

-- Przypadek 4: Zapalenie wyrostka (kategoria 2)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    28, 'M', 95, 130, 80, 38.5, 98, 15, 8, 18,
    12, 'zapalenie_wyrostka', 'oczekujący', 3,
    NOW() - INTERVAL '1 hour'
);

-- Przypadek 5: Złamanie proste (kategoria 3 - stabilny)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    35, 'K', 80, 125, 78, 36.8, 99, 15, 6, 16,
    3, 'złamanie_proste', 'oczekujący', 3,
    NOW() - INTERVAL '2 hours'
);

-- Przypadek 6: Infekcja moczu (kategoria 3)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    52, 'K', 88, 135, 82, 38.2, 98, 15, 5, 16,
    48, 'infekcja_moczu', 'oczekujący', 3,
    NOW() - INTERVAL '3 hours'
);

-- Przypadek 7: Migrena (kategoria 4 - niski priorytet)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    38, 'K', 75, 125, 80, 36.9, 99, 15, 8, 14,
    6, 'migrena', 'oczekujący', 4,
    NOW() - INTERVAL '4 hours'
);

-- Przypadek 8: Przeziębienie (kategoria 5 - bardzo niski)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    25, 'M', 70, 120, 75, 37.5, 99, 15, 2, 14,
    72, 'przeziębienie', 'oczekujący', 4,
    NOW() - INTERVAL '5 hours'
);

-- Przypadek 9: Kontrola (kategoria 5)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia, notatki
) VALUES (
    55, 'M', 68, 128, 78, 36.6, 99, 15, 0, 14,
    168, 'kontrola', 'oczekujący', 4,
    NOW() - INTERVAL '6 hours',
    'Kontrola po przebytym zapaleniu płuc - pacjent czuje się dobrze'
);

-- Przypadek 10: Receptura (kategoria 5)
INSERT INTO patients (
    wiek, plec, tetno, cisnienie_skurczowe, cisnienie_rozkurczowe,
    temperatura, saturacja, gcs, bol, czestotliwosc_oddechow,
    czas_od_objawow_h, szablon_przypadku, status, wprowadzony_przez,
    data_przyjecia
) VALUES (
    62, 'K', 72, 130, 80, 36.7, 99, 15, 1, 15,
    240, 'receptura', 'oczekujący', 4,
    NOW() - INTERVAL '7 hours'
);

RAISE NOTICE '✓ Utworzono 10 pacjentów testowych';


-- Pacjent 1: Zawał STEMI -> kategoria 1
INSERT INTO triage_predictions (
    patient_id, kategoria_triazu,
    prob_kat_1, prob_kat_2, prob_kat_3, prob_kat_4, prob_kat_5,
    przypisany_oddzial, oddzial_docelowy,
    model_version, confidence_score, predicted_at
) VALUES (
    1, 1,
    0.92, 0.06, 0.02, 0.0, 0.0,
    'Kardiologia', 'Kardiologia',
    'rf_improved_20251017', 0.92,
    NOW() - INTERVAL '9 minutes'
);

-- Pacjent 2: Udar ciężki -> kategoria 1
INSERT INTO triage_predictions (
    patient_id, kategoria_triazu,
    prob_kat_1, prob_kat_2, prob_kat_3, prob_kat_4, prob_kat_5,
    przypisany_oddzial, oddzial_docelowy,
    model_version, confidence_score, predicted_at
) VALUES (
    2, 1,
    0.88, 0.10, 0.02, 0.0, 0.0,
    'Neurologia', 'Neurologia',
    'rf_improved_20251017', 0.88,
    NOW() - INTERVAL '4 minutes'
);

-- Pacjent 3: Zapalenie płuc -> kategoria 2
INSERT INTO triage_predictions (
    patient_id, kategoria_triazu,
    prob_kat_1, prob_kat_2, prob_kat_3, prob_kat_4, prob_kat_5,
    przypisany_oddzial, oddzial_docelowy,
    model_version, confidence_score, predicted_at
) VALUES (
    3, 2,
    0.08, 0.82, 0.08, 0.02, 0.0,
    'Interna', 'Interna',
    'rf_improved_20251017', 0.82,
    NOW() - INTERVAL '28 minutes'
);

-- Pacjent 4: Zapalenie wyrostka -> kategoria 2
INSERT INTO triage_predictions (
    patient_id, kategoria_triazu,
    prob_kat_1, prob_kat_2, prob_kat_3, prob_kat_4, prob_kat_5,
    przypisany_oddzial, oddzial_docelowy,
    model_version, confidence_score, predicted_at
) VALUES (
    4, 2,
    0.05, 0.85, 0.08, 0.02, 0.0,
    'Chirurgia', 'Chirurgia',
    'rf_improved_20251017', 0.85,
    NOW() - INTERVAL '58 minutes'
);

-- Pacjent 5: Złamanie proste -> kategoria 3
INSERT INTO triage_predictions (
    patient_id, kategoria_triazu,
    prob_kat_1, prob_kat_2, prob_kat_3, prob_kat_4, prob_kat_5,
    przypisany_oddzial, oddzial_docelowy,
    model_version, confidence_score, predicted_at
) VALUES (
    5, 3,
    0.0, 0.10, 0.78, 0.10, 0.02,
    'Ortopedia', 'Ortopedia',
    'rf_improved_20251017', 0.78,
    NOW() - INTERVAL '1 hour 58 minutes'
);

-- Obecne obłożenie
INSERT INTO department_occupancy (
    timestamp, sor, interna, kardiologia, chirurgia, 
    ortopedia, neurologia, pediatria, ginekologia
) VALUES (
    NOW(),
    18, 35, 22, 28, 15, 12, 20, 10
);

-- 1 godzine temu
INSERT INTO department_occupancy (
    timestamp, sor, interna, kardiologia, chirurgia, 
    ortopedia, neurologia, pediatria, ginekologia
) VALUES (
    NOW() - INTERVAL '1 hour',
    15, 32, 20, 25, 14, 10, 18, 9
);

-- 2 godziny temu
INSERT INTO department_occupancy (
    timestamp, sor, interna, kardiologia, chirurgia, 
    ortopedia, neurologia, pediatria, ginekologia
) VALUES (
    NOW() - INTERVAL '2 hours',
    20, 38, 25, 30, 18, 15, 22, 12
);

-- 3 godziny temu
INSERT INTO department_occupancy (
    timestamp, sor, interna, kardiologia, chirurgia, 
    ortopedia, neurologia, pediatria, ginekologia
) VALUES (
    NOW() - INTERVAL '3 hours',
    22, 42, 27, 32, 20, 16, 25, 14
);

-- 6 godzin temu (szczyt)
INSERT INTO department_occupancy (
    timestamp, sor, interna, kardiologia, chirurgia, 
    ortopedia, neurologia, pediatria, ginekologia
) VALUES (
    NOW() - INTERVAL '6 hours',
    24, 48, 29, 34, 23, 18, 28, 16
);

-- 12 godzin temu (noc)
INSERT INTO department_occupancy (
    timestamp, sor, interna, kardiologia, chirurgia, 
    ortopedia, neurologia, pediatria, ginekologia
) VALUES (
    NOW() - INTERVAL '12 hours',
    10, 25, 15, 18, 10, 8, 12, 5
);

-- 24 godziny temu
INSERT INTO department_occupancy (
    timestamp, sor, interna, kardiologia, chirurgia, 
    ortopedia, neurologia, pediatria, ginekologia
) VALUES (
    NOW() - INTERVAL '24 hours',
    19, 36, 23, 27, 16, 13, 21, 11
);

RAISE NOTICE '✓ Utworzono 7 wpisów obłożenia oddziałów';

-- Login admina
INSERT INTO audit_log (
    user_id, action, table_name, record_id, 
    ip_address, user_agent, timestamp
) VALUES (
    1, 'LOGIN', NULL, NULL,
    '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    NOW() - INTERVAL '2 hours'
);

-- Utworzenie pacjenta przez pielęgniarkę
INSERT INTO audit_log (
    user_id, action, table_name, record_id,
    new_values, ip_address, timestamp
) VALUES (
    3, 'CREATE_PATIENT', 'patients', 1,
    '{"wiek": 67, "plec": "M", "szablon_przypadku": "zawał_STEMI"}',
    '192.168.1.105',
    NOW() - INTERVAL '10 minutes'
);

-- Wykonanie predykcji
INSERT INTO audit_log (
    user_id, action, table_name, record_id,
    new_values, timestamp
) VALUES (
    3, 'PREDICT_TRIAGE', 'triage_predictions', 1,
    '{"kategoria_triazu": 1, "confidence": 0.92}',
    NOW() - INTERVAL '9 minutes'
);
