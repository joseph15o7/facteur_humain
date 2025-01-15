import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from typing import List, Dict, Any, Tuple
import logging


class ExperimentAnalyzer:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.df = None
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='analysis.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def load_data(self) -> pd.DataFrame:
        data_list = []

        try:
            for file_path in self.data_dir.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Extraire les informations de base du participant
                    participant_info = data['participant_info']
                    performance_data = data['performance_data']

                    # Pour chaque évaluation (niveau)
                    for evaluation in data.get('evaluations', []):
                        try:
                            # Création d'une nouvelle entrée pour ce niveau
                            level_data = {
                                'participant_id': participant_info['id'],
                                'age': participant_info['age'],
                                'gender': participant_info['gender'],
                                'condition': participant_info['condition'],
                                'heart_rate_before': participant_info['heart_rate_before'],
                                'heart_rate_after': participant_info['heart_rate_after'],
                                'level': evaluation['level'],
                                'avg_response_time': evaluation['avg_response_time'],
                                'missed_bonus': performance_data['missed_bonus'],
                                'command_errors': performance_data['command_errors'],
                                'performance_eval': evaluation['performance'],
                                'stress_eval': evaluation['stress'],
                                'certitude_eval': evaluation['certitude']
                            }
                            data_list.append(level_data)
                        except KeyError as e:
                            logging.error(f"Données manquantes dans l'évaluation du fichier {file_path}: {str(e)}")
                            continue

            self.df = pd.DataFrame(data_list)
            logging.info(f"Données chargées avec succès: {len(self.df)} entrées")
            return self.df

        except Exception as e:
            logging.error(f"Erreur lors du chargement des données: {str(e)}")
            raise

    def validate_data(self) -> Tuple[bool, List[str]]:
        issues = []

        if self.df is None:
            return False, ["Aucune donnée chargée"]

        # Vérification du nombre minimum de participants par condition
        participants_per_condition = self.df.groupby('condition')['participant_id'].nunique()
        for condition, count in participants_per_condition.items():
            if count < 20:
                issues.append(f"Condition {condition}: seulement {count}/20 participants requis")

        # Vérification de la validité des évaluations
        if not self.df['performance_eval'].between(1, 5).all():
            issues.append("Certaines évaluations de performance sont hors limites")
        if not self.df['stress_eval'].between(1, 5).all():
            issues.append("Certaines évaluations de stress sont hors limites")
        if not self.df['certitude_eval'].between(1, 3).all():
            issues.append("Certaines évaluations de certitude sont hors limites")

        return len(issues) == 0, issues

    def analyze_response_times(self) -> Dict[str, Any]:
        results = {}

        try:
            # Statistiques descriptives
            results['descriptive'] = self.df.groupby(['condition', 'level'])['avg_response_time'].agg([
                'count', 'mean', 'std', 'min', 'max'
            ]).round(3)

            # ANOVA à deux facteurs (condition x niveau)
            conditions = self.df['condition'].unique()
            levels = self.df['level'].unique()

            # Préparation des données pour ANOVA
            response_times = [
                [self.df[(self.df['condition'] == c) & (self.df['level'] == l)]['avg_response_time'].values
                 for l in levels]
                for c in conditions
            ]

            f_stat, p_value = stats.f_oneway(*[group for sublist in response_times for group in sublist])
            results['anova'] = {
                'f_statistic': round(f_stat, 3),
                'p_value': round(p_value, 4)
            }

        except Exception as e:
            logging.error(f"Erreur lors de l'analyse des temps de réponse: {str(e)}")
            results['error'] = str(e)

        return results

    def analyze_performance_ratings(self) -> Dict[str, Any]:
        results = {}

        try:
            # Statistiques descriptives par condition et niveau
            results['ratings'] = self.df.groupby(['condition', 'level'])[
                ['performance_eval', 'stress_eval', 'certitude_eval']
            ].agg(['mean', 'std']).round(2)

            # Test de Kruskal-Wallis pour les différences entre conditions
            for metric in ['performance_eval', 'stress_eval']:
                try:
                    h_stat, p_value = stats.kruskal(*[
                        self.df[self.df['condition'] == c][metric].values
                        for c in self.df['condition'].unique()
                    ])
                    results[f'kruskal_{metric}'] = {
                        'h_statistic': round(h_stat, 3),
                        'p_value': round(p_value, 4)
                    }
                except Exception as e:
                    logging.error(f"Erreur lors du test Kruskal-Wallis pour {metric}: {str(e)}")
                    results[f'kruskal_{metric}'] = {'error': str(e)}

        except Exception as e:
            logging.error(f"Erreur lors de l'analyse des évaluations: {str(e)}")
            results['error'] = str(e)

        return results

    def analyze_heart_rate_impact(self) -> Dict[str, Any]:
        results = {}

        try:
            # Calcul de la variation de FC
            self.df['heart_rate_change'] = self.df['heart_rate_after'] - self.df['heart_rate_before']

            # Statistiques descriptives par condition
            results['hr_changes'] = self.df.groupby('condition')['heart_rate_change'].agg([
                'count', 'mean', 'std'
            ]).round(2)

            # T-test apparié pour chaque condition
            for condition in self.df['condition'].unique():
                condition_data = self.df[self.df['condition'] == condition]
                t_stat, p_value = stats.ttest_rel(
                    condition_data['heart_rate_before'],
                    condition_data['heart_rate_after']
                )
                results[f'ttest_{condition}'] = {
                    't_statistic': round(t_stat, 3),
                    'p_value': round(p_value, 4)
                }

        except Exception as e:
            logging.error(f"Erreur lors de l'analyse de la fréquence cardiaque: {str(e)}")
            results['error'] = str(e)

        return results

    def generate_visualizations(self, output_dir: str = "figures"):
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)

            # Configuration du style
            plt.style.use('default')

            # 1. Temps de réponse par condition et niveau
            plt.figure(figsize=(12, 6))
            sns.boxplot(x='level', y='avg_response_time', hue='condition', data=self.df)
            plt.title('Temps de réponse par niveau et condition')
            plt.savefig(output_path / 'response_times.png')
            plt.close()

            # 2. Évaluations de performance
            fig, axes = plt.subplots(1, 2, figsize=(15, 6))

            sns.violinplot(x='condition', y='performance_eval', data=self.df, ax=axes[0])
            axes[0].set_title('Distribution des évaluations de performance')

            sns.violinplot(x='condition', y='stress_eval', data=self.df, ax=axes[1])
            axes[1].set_title('Distribution des évaluations de stress')

            plt.tight_layout()
            plt.savefig(output_path / 'performance_ratings.png')
            plt.close()

            # 3. Changement de fréquence cardiaque
            plt.figure(figsize=(10, 6))
            sns.barplot(x='condition', y='heart_rate_change', data=self.df)
            plt.title('Variation moyenne de la fréquence cardiaque par condition')
            plt.savefig(output_path / 'heart_rate_changes.png')
            plt.close()

        except Exception as e:
            logging.error(f"Erreur lors de la génération des visualisations: {str(e)}")
            raise

    def generate_report(self) -> str:
        if self.df is None:
            return "Aucune donnée à analyser"

        report = []
        report.append("RAPPORT D'ANALYSE STATISTIQUE\n")
        report.append("=" * 50 + "\n")

        try:
            # Informations générales
            report.append("1. INFORMATIONS GÉNÉRALES\n")
            report.append(f"Nombre total de participants: {self.df['participant_id'].nunique()}")
            report.append("Participants par condition:")
            for condition, count in self.df.groupby('condition')['participant_id'].nunique().items():
                report.append(f"  - {condition}: {count}")
            report.append("")

            # Résultats des analyses
            response_results = self.analyze_response_times()
            performance_results = self.analyze_performance_ratings()
            heart_rate_results = self.analyze_heart_rate_impact()

            report.append("2. ANALYSE DES TEMPS DE RÉPONSE\n")
            report.append(str(response_results['descriptive']))
            report.append(
                f"\nANOVA: F={response_results['anova']['f_statistic']}, p={response_results['anova']['p_value']}")
            report.append("")

            report.append("3. ANALYSE DES ÉVALUATIONS\n")
            report.append(str(performance_results['ratings']))
            report.append("")

            report.append("4. ANALYSE DE LA FRÉQUENCE CARDIAQUE\n")
            report.append(str(heart_rate_results['hr_changes']))
            report.append("")

        except Exception as e:
            logging.error(f"Erreur lors de la génération du rapport: {str(e)}")
            report.append(f"Erreur lors de la génération du rapport: {str(e)}")

        return "\n".join(report)


def main():
    analyzer = ExperimentAnalyzer()

    try:
        # Chargement et validation des données
        analyzer.load_data()
        is_valid, issues = analyzer.validate_data()

        if not is_valid:
            print("Problèmes détectés dans les données:")
            for issue in issues:
                print(f"- {issue}")
            return

        # Exécution des analyses
        analyzer.analyze_response_times()
        analyzer.analyze_performance_ratings()
        analyzer.analyze_heart_rate_impact()

        # Génération des visualisations
        analyzer.generate_visualizations()

        # Génération du rapport
        report = analyzer.generate_report()

        # Sauvegarde du rapport
        with open('rapport_analyse.txt', 'w', encoding='utf-8') as f:
            f.write(report)

        print("Analyse terminée avec succès. Consultez rapport_analyse.txt pour les résultats.")

    except Exception as e:
        logging.error(f"Erreur lors de l'analyse: {str(e)}")
        print(f"Une erreur est survenue: {str(e)}")


if __name__ == "__main__":
    main()
