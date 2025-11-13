import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import pickle
import json
from datetime import datetime
from pathlib import Path

from imblearn.combine import SMOTETomek
from imblearn.over_sampling import BorderlineSMOTE, ADASYN

# Modele ML
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.utils.class_weight import compute_class_weight

# Metryki
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, balanced_accuracy_score
)

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

DATA_PATH = Path('/home/dolfik/Projects/Clinic-data/data/raw/')
MODEL_PATH = Path('/home/dolfik/Projects/Clinic-data/models/')
RESULTS_PATH = Path('/home/dolfik/Projects/Clinic-data/results/')

MODEL_PATH.mkdir(parents=True, exist_ok=True)
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
SAVE_PLOTS = True


def print_header(text):
    """Wyświetla sformatowany nagłówek"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

def analyze_class_distribution(y, dataset_name="Dataset"):
    """Szczegółowa analiza rozkładu klas"""
    print(f"\n--- Rozkład klas: {dataset_name} ---")
    unique, counts = np.unique(y, return_counts=True)
    total = len(y)
    
    for cat, count in zip(unique, counts):
        pct = count / total * 100
        bar = "█" * int(pct / 2)
        print(f"  Kategoria {int(cat)}: {count:>4} ({pct:>5.1f}%) {bar}")
    
    max_count = counts.max()
    min_count = counts.min()
    imbalance_ratio = max_count / min_count
    print(f"\n  Współczynnik nierównowagi: {imbalance_ratio:.2f}x")
    
    if imbalance_ratio > 3:
        print("  UWAGA: Duża nierównowaga klas! Wymagany SMOTE/oversampling")
    
    return dict(zip(unique, counts))

def plot_confusion_matrix(y_true, y_pred, model_name, save=True):
    """Tworzy i wyświetla confusion matrix"""
    cm = confusion_matrix(y_true, y_pred)
    
    cm_pct = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['1','2','3','4','5'], 
                yticklabels=['1','2','3','4','5'], ax=ax1)
    ax1.set_title(f'Confusion Matrix - {model_name} (liczby)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Prawdziwa kategoria', fontsize=10)
    ax1.set_xlabel('Predykcja modelu', fontsize=10)
    
    # Procenty
    sns.heatmap(cm_pct, annot=True, fmt='.1f', cmap='RdYlGn',
                xticklabels=['1','2','3','4','5'], 
                yticklabels=['1','2','3','4','5'], ax=ax2)
    ax2.set_title(f'Confusion Matrix - {model_name} (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Prawdziwa kategoria', fontsize=10)
    ax2.set_xlabel('Predykcja modelu', fontsize=10)
    
    plt.tight_layout()
    
    if save:
        filename = RESULTS_PATH / f'confusion_matrix_{model_name.lower().replace(" ","_")}_improved.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    plt.show()

def plot_feature_importance(model, feature_names, model_name, top_n=20, save=True):
    """Wyświetla ważność cech"""
    if not hasattr(model, 'feature_importances_'):
        print(f"Model {model_name} nie posiada feature_importances_")
        return
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]
    
    plt.figure(figsize=(12, 8))
    plt.title(f'Top {top_n} najważniejszych cech - {model_name}',
              fontsize=14, fontweight='bold')
    plt.barh(range(top_n), importances[indices], color='steelblue', edgecolor='black')
    plt.yticks(range(top_n), [feature_names[i] for i in indices])
    plt.xlabel('Ważność cechy', fontsize=12)
    plt.gca().invert_yaxis()
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    
    if save:
        filename = RESULTS_PATH / f'feature_importance_{model_name.lower().replace(" ","_")}_improved.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    plt.show()

def evaluate_model(model, X, y, dataset_name="Test"):
    """Ewaluacja modelu z rozszerzonymi metrykami"""
    y_pred = model.predict(X)
    
    # Podstawowe metryki
    accuracy = accuracy_score(y, y_pred)
    balanced_acc = balanced_accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y, y_pred, average='weighted', zero_division=0)
    
    print(f"\n--- Metryki na zbiorze {dataset_name} ---")
    print(f"Accuracy:          {accuracy:.4f}")
    print(f"Balanced Accuracy: {balanced_acc:.4f}  ← WAŻNE dla niezbalansowanych klas")
    print(f"Precision:         {precision:.4f}")
    print(f"Recall:            {recall:.4f}")
    print(f"F1-Score:          {f1:.4f}")
    
    # Per-class metrics
    print(f"\n--- Dokładność per kategoria ---")
    for category in sorted(np.unique(y)):
        mask = y == category
        if mask.sum() > 0:
            cat_acc = (y_pred[mask] == category).sum() / mask.sum()
            print(f"  Kategoria {int(category)}: {cat_acc:.1%}")
    
    # Classification report
    print(f"\n--- Classification report ({dataset_name}) ---")
    print(classification_report(y, y_pred, 
                                target_names=[f"Kategoria {i}" for i in range(1,6)],
                                zero_division=0))
    
    return {
        'accuracy': accuracy,
        'balanced_accuracy': balanced_acc,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'predictions': y_pred
    }

def compare_models(results_dict):
    """Porównanie wyników wszystkich modeli"""
    print_header("Porównanie modeli")
    
    comparison_data = []
    for model_name, metrics in results_dict.items():
        comparison_data.append({
            'Model': model_name,
            'Accuracy': metrics['test']['accuracy'],
            'Balanced Acc': metrics['test']['balanced_accuracy'],
            'Precision': metrics['test']['precision'],
            'Recall': metrics['test']['recall'],
            'F1-Score': metrics['test']['f1_score']
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    print("\n", df_comparison.to_string(index=False))
    
    # Wykres porównawczy
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    metrics = ['Accuracy', 'Balanced Acc', 'Precision', 'Recall', 'F1-Score']
    
    for idx, metric in enumerate(metrics):
        ax = axes[idx]
        df_comparison.plot(x='Model', y=metric, kind='bar', ax=ax, legend=False, color='skyblue')
        ax.set_title(metric, fontsize=12, fontweight='bold')
        ax.set_ylabel(metric, fontsize=10)
        ax.set_xlabel('')
        ax.set_ylim([0, 1])
        ax.grid(axis='y', alpha=0.3)
        
        for i, v in enumerate(df_comparison[metric]):
            ax.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontsize=9)
    
    axes[-1].axis('off')  # Ukryj ostatni subplot
    
    plt.suptitle('Porównanie modeli - wszystkie metryki (NO SCALING)', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if SAVE_PLOTS:
        filename = RESULTS_PATH / 'model_comparison_no_scaling.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    plt.show()
    
    # Znajdź najlepszy model (wg Balanced Accuracy dla niezbalansowanych klas)
    best_model = df_comparison.loc[df_comparison['Balanced Acc'].idxmax(), 'Model']
    best_bacc = df_comparison['Balanced Acc'].max()
    
    return best_model

def save_model(model, model_name, metrics):
    """Zapisuje model do pliku"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    model_filename = MODEL_PATH / f'{model_name.lower().replace(" ", "_")}_no_scaling_{timestamp}.pkl'
    with open(model_filename, 'wb') as f:
        pickle.dump(model, f)
    
    print(f"Model zapisany: {model_filename}")
    
    metrics_filename = MODEL_PATH / f'{model_name.lower().replace(" ","_")}_no_scaling_{timestamp}_metrics.json'
    with open(metrics_filename, 'w') as f:
        metrics_to_save = {
            'train': {k: v for k, v in metrics['train'].items() if k != 'predictions'},
            'val': {k: v for k, v in metrics['val'].items() if k != 'predictions'},
            'test': {k: v for k, v in metrics['test'].items() if k != 'predictions'}
        }
        json.dump(metrics_to_save, f, indent=2)
    
    print(f"Metryki zapisane: {metrics_filename}")


def main():
    """Główna funkcja trenująca model"""
    
    print_header("Trening modelu triaży - BEZ SKALOWANIA")
    print(f"Data rozpoczęcia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================================================================
    # 1. WCZYTANIE I PREPROCESSING SUROWYCH DANYCH
    # ========================================================================
    print_header("Wczytanie i preprocessing surowych danych")
    
    try:
        # ✅ Wczytaj surowe dane
        df = pd.read_csv(DATA_PATH / 'triage_data.csv')
        print(f"✓ Wczytano {len(df)} rekordów surowych")
        print(f"  Kolumny: {list(df.columns)}")
        
        # Wydziel target
        y = df['kategoria_triażu'].values
        
        # Usuń kolumny które nie są cechami
        X = df.drop(['kategoria_triażu', 'id_przypadku', 'data_przyjęcia', 'oddział_docelowy'], axis=1)
        print(f"\n✓ Po usunięciu kolumn niebędących cechami: {X.shape[1]} kolumn")
        
        # One-hot encoding dla płci
        X['płeć_M'] = (X['płeć'] == 'M').astype(int)
        X = X.drop('płeć', axis=1)
        
        # One-hot encoding dla szablonu przypadku
        template_dummies = pd.get_dummies(X['szablon_przypadku'], prefix='szablon')
        X = pd.concat([X.drop('szablon_przypadku', axis=1), template_dummies], axis=1)
        
        print(f"✓ Po one-hot encoding: {X.shape[1]} cech")
        print(f"\nPrzykładowe cechy: {list(X.columns[:10])}")
        
        # ✅ SPLIT train/val/test BEZ SKALOWANIA
        print("\n✓ Podział danych na train/val/test...")
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.15, random_state=RANDOM_STATE, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.176, random_state=RANDOM_STATE, stratify=y_temp
        )
        
        print(f"\nRozmiary zbiorów:")
        print(f"  Treningowy:  {X_train.shape[0]:>5} próbek × {X_train.shape[1]:>3} cech")
        print(f"  Walidacyjny: {X_val.shape[0]:>5} próbek × {X_val.shape[1]:>3} cech")
        print(f"  Testowy:     {X_test.shape[0]:>5} próbek × {X_test.shape[1]:>3} cech")
        
        print("\n✅ DANE BEZ NORMALIZACJI (surowe wartości)")
        print("   Model będzie trenowany i używany na tych samych wartościach!")
        
    except FileNotFoundError as e:
        print("\n❌ Błąd: nie znaleziono plików z danymi")
        print(f"   Szczegóły: {e}")
        return
    
    print_header("Analiza rozkładu klas")
    
    train_dist = analyze_class_distribution(y_train, "Treningowy (przed oversampling)")
    test_dist = analyze_class_distribution(y_test, "Testowy")
    
    print_header("Balansowanie klas - SMOTETomek")
    
    print(f"\n  Przed balansowaniem: {X_train.shape[0]} próbek")
    
    resampler = SMOTETomek(random_state=RANDOM_STATE)
    X_train_balanced, y_train_balanced = resampler.fit_resample(X_train, y_train)
    
    print(f"  Po balansowaniu:  {X_train_balanced.shape[0]} próbek")
    analyze_class_distribution(y_train_balanced, "Treningowy (po oversampling)")
    
    print_header("Obliczanie wag klas")
    
    class_weights = compute_class_weight(
        class_weight='balanced',
        classes=np.unique(y_train_balanced),
        y=y_train_balanced
    )
    class_weight_dict = dict(enumerate(class_weights, 1))
    
    print("\nWagi dla każdej kategorii (wyższe = bardziej priorytetowe):")
    for cat, weight in class_weight_dict.items():
        print(f"  Kategoria {cat}: {weight:.3f}")
    
    print_header("Definicja modeli")
    
    feature_names = X_train_balanced.columns.tolist()
    
    print("\n🔍 Hyperparameter tuning dla Random Forest...")
    param_grid = {
        'n_estimators': [200, 300, 400],
        'max_depth': [20, 25, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'class_weight': ['balanced', 'balanced_subsample']
    }
    
    rf_base = RandomForestClassifier(
        random_state=RANDOM_STATE,
        n_jobs=-1,
        max_features='sqrt'
    )
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    
    grid_search = GridSearchCV(
        rf_base, 
        param_grid, 
        cv=cv,
        scoring='balanced_accuracy',  
        n_jobs=-1,
        verbose=2
    )
    
    grid_search.fit(X_train_balanced, y_train_balanced)
    
    print("\n  Najlepsze parametry:")
    for param, value in grid_search.best_params_.items():
        print(f"    {param}: {value}")
    print(f"  Best CV Score: {grid_search.best_score_:.4f}")
    
    best_rf = grid_search.best_estimator_
    
    models = {}
    models['Random Forest'] = best_rf
    
    models['Gradient Boosting'] = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=7,
        random_state=RANDOM_STATE,
        verbose=0
    )
    
    models['Logistic Regression'] = LogisticRegression(
        max_iter=2000,
        random_state=RANDOM_STATE,
        class_weight='balanced',
        solver='saga',
        n_jobs=-1
    )
    
    # Ensemble z wagami
    ensemble = VotingClassifier(
        estimators=[
            ('rf', best_rf),
            ('gb', models['Gradient Boosting']),
            ('lr', models['Logistic Regression'])
        ],
        voting='soft',
        weights=[2, 2, 1],
        n_jobs=-1
    )
    models['Ensemble (Weighted)'] = ensemble
    
    results = {}
    trained_models = {}
    
    for model_name, model in models.items():
        print_header(f"Trening i ewaluacja: {model_name}")
        
        if model_name != 'Random Forest':
            model.fit(X_train_balanced, y_train_balanced)
        
        trained_models[model_name] = model
        
        results[model_name] = {
            'train': evaluate_model(model, X_train_balanced, y_train_balanced, "Treningowy"),
            'val': evaluate_model(model, X_val, y_val, "Walidacyjny"),
            'test': evaluate_model(model, X_test, y_test, "Testowy")
        }
        
        if SAVE_PLOTS:
            plot_confusion_matrix(
                y_test, 
                results[model_name]['test']['predictions'], 
                model_name, 
                save=True
            )
        
        if SAVE_PLOTS and model_name in ['Random Forest', 'Gradient Boosting']:
            plot_feature_importance(model, feature_names, model_name, top_n=20, save=True)
    
    best_model_name = compare_models(results)
    best_model = trained_models[best_model_name]
    
    print_header(f"Szczegółowa analiza najlepszego modelu: {best_model_name}")
    
    best_metrics = results[best_model_name]['test']
    
    print(f"\n  Metryki finalne na zbiorze testowym:")
    print(f"   Accuracy:          {best_metrics['accuracy']:.2%}")
    print(f"   Balanced Accuracy: {best_metrics['balanced_accuracy']:.2%}")
    print(f"   F1-Score:          {best_metrics['f1_score']:.2%}")
    
    print_header("Zapis modelu")
    save_model(best_model, best_model_name, results[best_model_name])
    
    print("\n" + "="*70)
    print("✅ TRENING ZAKOŃCZONY - MODEL BEZ SKALOWANIA")
    print("   Backend używa surowych danych → kompatybilny!")
    print("="*70)
    
if __name__ == "__main__":
    main()
