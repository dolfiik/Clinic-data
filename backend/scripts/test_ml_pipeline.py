import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.preprocessor import preprocessor
from app.ml.model_loader import model_loader
from app.ml.predictor import predictor

def test_preprocessor():
    print("TEST 1: PREPROCESSOR")
    print("="*70)
    
    patient_data = {
        "wiek": 67,
        "plec": "M",
        "tetno": 125.0,
        "cisnienie_skurczowe": 95.0,
        "cisnienie_rozkurczowe": 55.0,
        "temperatura": 37.2,
        "saturacja": 88.0,
        "gcs": 14,
        "bol": 9,
        "czestotliwosc_oddechow": 28.0,
        "czas_od_objawow_h": 2.5,
        "szablon_przypadku": "zawał_STEMI"
    }
    
    print("\n Dane wejściowe:")
    for key, value in patient_data.items():
        print(f"  {key}: {value}")
    
    is_valid, error = preprocessor.validate_input(patient_data)
    if is_valid:
        print("\nWalidacja: PASSED")
    else:
        print(f"\nWalidacja: FAILED - {error}")
        return False
    
    try:
        X = preprocessor.transform(patient_data)
        print(f"\n✓ Preprocessing: SUCCESS")
        print(f"  Shape: {X.shape}")
        print(f"  Liczba cech: {X.shape[1]}")
        
        print(f"\n  Przykładowe cechy (pierwsze 10):")
        for i, col in enumerate(X.columns[:10]):
            print(f"    {col}: {X[col].values[0]:.4f}")
        
        return True
    except Exception as e:
        print(f"\nPreprocessing: FAILED - {e}")
        return False

def test_model_loader():
    """Test ładowania modelu"""
    print("TEST 2: MODEL LOADER")
    print("="*70)
    
    try:
        model = model_loader.load_latest_model()
        print("\n✓ Model załadowany pomyślnie")
        
        info = model_loader.get_model_info()
        print("\nInformacje o modelu:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"\n Ładowanie modelu: FAILED - {e}")
        return False

def test_predictor():
    print("TEST 3: PREDICTOR (pełny pipeline)")
    print("="*70)
    
    test_cases = [
        {
            "name": "Zawał STEMI (kategoria 1)",
            "data": {
                "wiek": 67,
                "plec": "M",
                "tetno": 125.0,
                "cisnienie_skurczowe": 95.0,
                "cisnienie_rozkurczowe": 55.0,
                "temperatura": 37.2,
                "saturacja": 88.0,
                "gcs": 14,
                "bol": 9,
                "czestotliwosc_oddechow": 28.0,
                "czas_od_objawow_h": 2.5,
                "szablon_przypadku": "zawał_STEMI"
            },
            "expected_category": 1
        },
        {
            "name": "Złamanie proste (kategoria 3)",
            "data": {
                "wiek": 35,
                "plec": "K",
                "tetno": 80.0,
                "cisnienie_skurczowe": 125.0,
                "cisnienie_rozkurczowe": 78.0,
                "temperatura": 36.8,
                "saturacja": 99.0,
                "gcs": 15,
                "bol": 6,
                "czestotliwosc_oddechow": 16.0,
                "czas_od_objawow_h": 3.0,
                "szablon_przypadku": "złamanie_proste"
            },
            "expected_category": 3
        },
        {
            "name": "Przeziębienie (kategoria 5)",
            "data": {
                "wiek": 25,
                "plec": "M",
                "tetno": 70.0,
                "cisnienie_skurczowe": 120.0,
                "cisnienie_rozkurczowe": 75.0,
                "temperatura": 37.5,
                "saturacja": 99.0,
                "gcs": 15,
                "bol": 2,
                "czestotliwosc_oddechow": 14.0,
                "czas_od_objawow_h": 72.0,
                "szablon_przypadku": "przeziębienie"
            },
            "expected_category": 5
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        
        try:
            result = predictor.predict(test_case['data'])
            
            print(f"✓ Predykcja wykonana")
            print(f"  Kategoria: {result['category']}")
            print(f"  Oczekiwana: {test_case['expected_category']}")
            print(f"  Pewność: {result['confidence']:.2%}")
            print(f"  Model: {result['model_version']}")
            
            print(f"\n  Prawdopodobieństwa:")
            for cat, prob in result['probabilities'].items():
                bar = "█" * int(prob * 50)
                marker = " ← PRZEWIDYWANA" if int(cat) == result['category'] else ""
                print(f"    Kat {cat}: {prob:>6.2%} {bar}{marker}")
            
            if result['category'] == test_case['expected_category']:
                print(f"\n   Kategoria zgodna z oczekiwaną")
                success_count += 1
            else:
                print(f"\n   Kategoria różni się od oczekiwanej")
            
        except Exception as e:
            print(f" Predykcja failed: {e}")
    
    print(f"\n{'='*70}")
    print(f"WYNIKI: {success_count}/{len(test_cases)} testów zakończonych poprawną kategorią")
    
    return success_count == len(test_cases)

def test_feature_importance():
    """Test feature importance"""
    print("TEST 4: FEATURE IMPORTANCE")
    print("="*70)
    
    try:
        importance = predictor.get_feature_importance(top_n=15)
        
        if importance:
            print("\nTop 15 najważniejszych cech:")
            for i, (feature, imp) in enumerate(importance.items(), 1):
                bar = "█" * int(imp * 100)
                print(f"  {i:>2}. {feature:<30} {imp:>6.4f} {bar}")
            return True
        else:
            print("\nFeature importance niedostępne dla tego modelu")
            return True
    except Exception as e:
        print(f"\nFeature importance failed: {e}")
        return False

def test_model_info():
    """Test informacji o modelu"""
    print("TEST 5: MODEL INFO")
    print("="*70)
    
    try:
        info = predictor.get_model_info()
        
        print("\nPełne informacje o modelu:")
        for key, value in info.items():
            if isinstance(value, dict):
                print(f"\n  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"\n Model info failed: {e}")
        return False

def main():
    print("TEST KOMPLETNEGO PIPELINE ML")
    
    tests = [
        ("Preprocessor", test_preprocessor),
        ("Model Loader", test_model_loader),
        ("Predictor", test_predictor),
        ("Feature Importance", test_feature_importance),
        ("Model Info", test_model_info)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\nTest {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print("PODSUMOWANIE TESTÓW")
    print("="*70)
    
    for test_name, result in results:
        status = " PASS" if result else " FAIL"
        print(f"  {test_name:<25} {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n  Wynik: {passed}/{total} testów passed")
    
    if passed == total:
        print("\nWSZYSTKIE TESTY PASSED")
    else:
        print("\n Niektóre testy failed - sprawdź logi powyżej")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
