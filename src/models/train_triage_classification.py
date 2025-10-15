import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import pickle
import json
from datetime import datetime
from pathlib import Path
from imblearn.over_sampling import SMOTE




# Modele ML
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

# Metryki

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

#Sciezki
DATA_PATH = Path('/home/dolfik/Projects/Clinic-data/data/processed/')
MODEL_PATH = Path('/home/dolfik/Projects/Clinic-data/models/')
RESULTS_PATH = Path('/home/dolfik/Projects/Clinic-data/results/')

MODEL_PATH.mkdir(parents=True, exist_ok=True)
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

#Parametry treningu
RANDOM_STATE = 42
SAVE_PLOTS = True

#Funkcje pomocnicze

def print_header(text):
    """Wyswietla sformatowany naglowek"""
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)


def plot_confusion_matrix(y_true, y_pred, model_name, save=True):
    """
    Tworzy i wyswietla confusion matrix

    Args:
        y_true: prawdziwe etykiety
        y_pred: predykcje modelu
        model_name: nazwa modelu
        save: czy zapisac wykres
    """

    cm = confusion_matrix(y_true, y_pred)

    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['1','2','3','4','5'], yticklabels=['1','2','3','4','5'])
    plt.title(f'Confusion Matrix - {model_name}', fontsize=14, fontweight='bold')
    plt.ylabel('Prawdziwa kategoria', fontsize=12)
    plt.xlabel('Predykcja modelu', fontsize=12)
    plt.tight_layout()

    if save:
        filename = RESULTS_PATH / f'confusion_matrix_{model_name.lower().replace(" ","_")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
    plt.show()



def plot_feature_importance(model, feature_names, model_name, top_n=20, save=True):
    """
    Wyswietla waznosc cech (feature importance)

    Args:
        model: wytrenowany model
        feature_names: nazwy cech
        model_name: nazwa modelu
        top_n: liczba najwazniejszych cech do wyswietlania
        save: czy zapisac wykres
    """

    if not hasattr(model, 'feature_importances_'):
        print(f"Model {model_name} nie posiada feature_importances_")
        return

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]

    plt.figure(figsize=(12, 8))
    plt.title(f'Top {top_n} najwazniejszych cech - {model_name}',
                fontsize=14, fontweight='bold')
    plt.barh(range(top_n), importances[indices], color='steelblue', edgecolor='black')
    plt.yticks(range(top_n), [feature_names[i] for i in indices])
    plt.xlabel('Ważność cechy', fontsize=12)
    plt.gca().invert_yaxis()
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()

    if save:
        filename = RESULTS_PATH / f'feature_importance_{model_name.lower().replace(" ","_")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')

    plt.show()


def evaluate_model(model, X, y, dataset_name="Test"):
    """
    Ewaluacja modelu i wyswietlanie metryk

    Args:
        model: wytrenowany model
        X: dane wejsciowe
        y: prawdziwe etykiety
        dataset_name: nazwa zbioru danych
    
    Returns:
        dict: slownik z metrykami
    """
    
    y_pred = model.predict(X)

    #oblicz metryki
    accuracy = accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred, average='weighted', zero_division=0)
    recall = recall_score(y, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y, y_pred, average='weighted', zero_division=0)

    print(f"\n--- Metryki na zbiorze {dataset_name} ---")
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    

    #classification raport
    print(f"\n--- Classification report ({dataset_name}) ---")
    print(classification_report(y, y_pred, target_names=[f"Kategoria {i}" for i in range(1,6)]))

    
    return {
        'accuracy' : accuracy,
        'precision' : precision,
        'recall' : recall,
        'f1_score' : f1,
        'predictions' : y_pred
    }

def compare_models(results_dict):
    """
    Porownanie wynikow wszystkich modeli

    Args:
        results_dict: slownik z wynikami modeli
    """
    print_header("Porownanie modeli")

    #przygotowanie danych do porownania
    comparison_data = []
    for model_name, metrics in results_dict.items():
        comparison_data.append({
          'Model': model_name,
          'Accuracy': metrics['test']['accuracy'],
          'Precision': metrics['test']['precision'],
          'Recall': metrics['test']['recall'],
          'F1-Score': metrics['test']['f1_score']
        })
       
    df_comparison = pd.DataFrame(comparison_data)
    print("\n", df_comparison.to_string(index=False))

    #wykres porownawczy
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']

    for idx, metric in enumerate(metrics):
        ax = axes[idx // 2, idx % 2]
        df_comparison.plot(x='Model', y=metric, kind='bar', ax=ax, legend=False, color='skyblue')
        ax.set_title(metric, fontsize=12, fontweight='bold')
        ax.set_ylabel(metric, fontsize=10)
        ax.set_xlabel('')
        ax.set_ylim([0,1])
        ax.grid(axis='y', alpha=0.3)

        for i, v in enumerate(df_comparison[metric]):
            ax.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontsize=9)

    
    plt.suptitle('Porownanie modeli - wszystkie metryki', fontsize=14, fontweight='bold')
    plt.tight_layout()

    if SAVE_PLOTS:
        filename = RESULTS_PATH / 'model_comparison.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')

    plt.show()

    #znajdz najlepszy model
    best_model = df_comparison.loc[df_comparison['F1-Score'].idxmax(), 'Model']
    best_f1 = df_comparison['F1-Score'].max()
    print(f"\nNajlepszy model: {best_model} (F1-Score: {best_f1:.4f})")


    return best_model

def save_model(model, model_name, metrics):
    """
    Zapisuje model do pliku

    Args:
        model: wytrenowany model
        model_name: nazwa modelu
        metrics: metryki modelu
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    model_filename = MODEL_PATH / f'{model_name.lower().replace(" ", "_")}_{timestamp}.pkl'
    with open(model_filename, 'wb') as f:
        pickle.dump(model, f)

    print(f"Model zapisany: {model_filename}")

    metrics_filename = MODEL_PATH / f'{model_name.lower().replace(" ","_")}_{timestamp}_metrics.json'
    with open(metrics_filename, 'w') as f:
        #usuwanie predictions przed zapytaniem (za duze)
        metrics_to_save = {
                'train': {k: v for k, v in metrics['train'].items() if k != 'predictions'},
                'val': {k: v for k, v in metrics['val'].items() if k != 'predictions'},
                'test': {k: v for k, v in metrics['test'].items() if k != 'predictions'}
        }
        json.dump(metrics_to_save, f, indent=2)
    print(f"Metryki zapisane: {metrics_filename}")


def main():
    """
    Glowna funkcja trenujaca model
    """

    print_header("Model klasyfikacji kategorii triaży")
    print(f"Data rozpoczecia: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print_header("Wczytanie danych")

    try:
        X_train = pd.read_csv(DATA_PATH / 'X_train.csv')
        X_val = pd.read_csv(DATA_PATH / 'X_val.csv')
        X_test = pd.read_csv(DATA_PATH / 'X_test.csv')

        y_train = pd.read_csv(DATA_PATH / 'y_train.csv').values.ravel()
        y_val = pd.read_csv(DATA_PATH / 'y_val.csv').values.ravel()
        y_test = pd.read_csv(DATA_PATH / 'y_test.csv').values.ravel()


        text_columns = X_train.select_dtypes(include=['object']).columns.tolist()
        if text_columns:
            print(f"Usuwanie kolumn tekstowych: {text_columns}")
            X_train = X_train.drop(columns=text_columns)
            X_val = X_val.drop(columns=text_columns)
            X_test = X_test.drop(columns=text_columns)
            print(f" Po czyszczeniu: {X_train.shape[1]} cech")
        else:
            print("Brak kolumn tekstowych")

        # Konwersja do float
        X_train = X_train.astype(float)
        X_val = X_val.astype(float)
        X_test = X_test.astype(float)
        print("Dane przekonwertowane na float")

        print(f"Przed SMOTE: {X_train.shape[0]} próbek")
        print(f"Rozkład klas przed SMOTE:")
        unique, counts = np.unique(y_train, return_counts=True)
        for cat, count in zip(unique, counts):
            print(f"  Kategoria {int(cat)}: {count} próbek")

        smote = SMOTE(random_state=RANDOM_STATE)
        X_train, y_train = smote.fit_resample(X_train, y_train)

        print(f"\n✓ Po SMOTE: {X_train.shape[0]} próbek")
        print(f"Rozkład klas po SMOTE:")
        unique, counts = np.unique(y_train, return_counts=True)
        for cat, count in zip(unique, counts):
            print(f"  Kategoria {int(cat)}: {count} próbek")


        print("Dane wczytane pomyslnie")
        print("\nRozmiary zbiorow:")
        print(f" Treningowy: {X_train.shape[0]:>6} probek x {X_train.shape[1]:>3} cech")
        print(f" Walidacyjny: {X_val.shape[0]:>6} probek x {X_val.shape[1]:>3} cech")
        print(f" Testowy: {X_test.shape[0]:>6} probek x {X_test.shape[1]:>3} cech")

        print(f"\nRozklad klas (zbior treningowy):")
        for category in sorted(np.unique(y_train)):
            count = np.sum(y_train == category)
            pct = count / len(y_train) * 100
            print(f" Kategoria {category}: {count:>3} ({pct:>5.2f}%)")

    except FileNotFoundError as e:
        print("\nBlad: nie znaleziono plikow z danymi")
        return


    feature_names = X_train.columns.tolist()


    print_header("Definicja modeli")

    models = {}

    #random forest
    models['Random Forest'] = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        class_weight='balanced',
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=0
    )
    print("Random Forest zdefiniowany")

    #logistic regression
    models['Logistic Regression'] = LogisticRegression(
        max_iter=1000,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        multi_class='multinomial'
    )
    print("Logistic Regression zdefiniowany")

    #Decision Tree (baseline)
    models['Decision Tree'] = DecisionTreeClassifier(
        max_depth=15,
        min_samples_split=5,
        random_state=RANDOM_STATE
    )
    print("Decision Tree zdefiniowany")


    results = {}
    trained_models = {}

    for model_name, model in models.items():
        print_header(f"Trening: {model_name}")

        #trening
        print("Trening w toku...")
        model.fit(X_train, y_train)
        print("Trening zkaonczony")

        trained_models[model_name] = model

        #ewaluacja na wszystkich zbiorach
        results[model_name] = {
            'train': evaluate_model(model, X_train, y_train, "Treningowy"),
            'val': evaluate_model(model, X_val, y_val, "Walidacyjny"),
            'test': evaluate_model(model, X_test, y_test, "Testowy")
        }

        if SAVE_PLOTS:
            plot_confusion_matrix(y_test, results[model_name]['test']['predictions'], model_name, save=True)


        if SAVE_PLOTS and model_name in ['Random Forest', 'Decision Tree']:
            plot_feature_importance(model, feature_names, model_name, top_n=20, save=True)



        
    best_model_name = compare_models(results)
    best_model = trained_models[best_model_name]


    print_header("Zapis modelu")
    save_model(best_model, best_model_name, results[best_model_name])


if __name__ == "__main__":
    main()



