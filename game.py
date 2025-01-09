import pygame
import sys
import random
import json
import time
import pygame.mixer
from datetime import datetime
import csv
import math
from pathlib import Path
import numpy as np

pygame.mixer.pre_init(44100, -16, 2, 1024)  # Pré-configuration audio
pygame.init()
pygame.mixer.init()
# Initialisation de Pygame
pygame.init()
pygame.mixer.init()

# Constantes
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)

# Configuration de l'écran
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Mobile Game - Facteurs Humains")
clock = pygame.time.Clock()


class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=GREEN):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.is_selected = False  # Nouvel attribut pour suivre l'état de sélection
        self.font = pygame.font.Font(None, 36)

    def draw(self, surface):
    # Utiliser une couleur différente si le bouton est sélectionné
        if self.is_selected:
            color = GREEN  # Couleur quand sélectionné
        else:
            color = self.hover_color if self.is_hovered else self.color

        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=12)

        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False


class InputBox:
    def __init__(self, x, y, width, height, text='', type='text'):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
        self.text = text
        self.type = type
        self.font = pygame.font.Font(None, 32)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = RED if self.active else BLACK

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if self.type == 'numeric':
                        if event.unicode.isnumeric():
                            self.text += event.unicode
                    else:
                        self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, self.color)
        return False

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect, 0)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))


class SoundManager:
    def __init__(self):
        """
        Initialise le gestionnaire de son
        """
        try:
            self.sound_manager = SoundManager()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.bip_sound = self.generate_bip_sound()
            print("Audio initialisé avec succès")
        except Exception as e:
            print(f"Erreur d'initialisation audio : {e}")
            self.bip_sound = None

    def generate_bip_sound(self, duration=0.2, frequency=800, volume=0.5):
        """
        Génère un son de bip compatible multiplateforme

        Retourne:
        - Un objet pygame.mixer.Sound représentant le bip
        """
        sample_rate = 44100
        n_samples = int(sample_rate * duration)

        t = np.linspace(0, duration, n_samples, False)
        signal = np.sin(2 * np.pi * frequency * t)

        envelope = np.ones_like(signal)
        envelope[:100] = np.linspace(0, 1, 100)  # Attaque douce
        envelope[-100:] = np.linspace(1, 0, 100)  # Déclin doux

        signal *= envelope

        scaled_signal = np.int16(signal * 32767 * volume)
        stereo_signal = np.column_stack((scaled_signal, scaled_signal))

        try:
            sound = pygame.sndarray.make_sound(stereo_signal)
            return sound
        except Exception as e:
            print(f"Erreur de génération de son : {e}")
            return None

    def play_bip(self, volume=0.5):
        """
        Joue le son de bip avec gestion des erreurs
        """
        try:
            if self.bip_sound is None:
                print("Génération de son de secours")
                self.bip_sound = self.generate_bip_sound()

            self.bip_sound.set_volume(volume)
            self.bip_sound.play()
        except Exception as e:
            print(f"Impossible de jouer le son : {e}")

class Game:
    def __init__(self):
        self.reset_game()
        self.setup_ui()
        self.images = {
            "image1": pygame.transform.scale(pygame.image.load("./images/jumpscare.png"), (70, 70)),
            "image2": pygame.transform.scale(pygame.image.load("./images/cute.jpg"), (50, 50)),
            "image3": pygame.transform.scale(pygame.image.load("./images/joke.png"), (50, 50)),
            "image4": pygame.transform.scale(pygame.image.load("./images/kidding.png"), (50, 50)),
        }
        self.image_positions = self.create_image_positions()
        self.image_visible = False  # Indique si les images doivent être affichées
        self.current_image_index = 0  # Index de l'image actuellement affichée
        self.image_last_toggle = 0
        self.sound_manager = SoundManager()
        # Nouvelles variables pour les bips
        self.bip_start_time = None
        self.last_bip_time = 0
        self.bip_duration = 0.2  # Durée d'un bip en secondes

    def manage_bips(self, current_time):
        """Gère les bips selon les conditions expérimentales"""
        if self.bip_start_time is not None:
            if current_time - self.bip_start_time > self.bip_duration:
                self.bip_start_time = None
            return

        if self.participant_data['condition'] == 'sync':
            heart_rate = self.participant_data.get('heart_rate_before', 70)
            interval = 60.0 / heart_rate
            if current_time - self.last_bip_time >= interval:
                self.trigger_bip(current_time)

        elif self.participant_data['condition'] == 'async':
            fixed_bpm = 100
            interval = 60.0 / fixed_bpm
            if current_time - self.last_bip_time >= interval:
                self.trigger_bip(current_time)

        elif self.participant_data['condition'] == 'random':
            heart_rate = self.participant_data.get('heart_rate_before', 70)
            average_interval = 60.0 / heart_rate
            # Vérifier qu'au moins la moitié de l'intervalle moyen s'est écoulé
            if current_time - self.last_bip_time >= (average_interval / 2):
                if random.random() < 0.02:  # 2% de chance par frame
                    self.trigger_bip(current_time)

    def trigger_bip(self, current_time):
        """Déclenche un bip"""
        if self.bip_start_time is None:
            self.sound_manager.play_bip()
            self.bip_start_time = current_time
            self.last_bip_time = current_time
            self.game_data['bip_times'].append(current_time)

    def create_paths(self):
        """Crée les chemins pour chaque niveau"""
        paths = {
            1: [
                (100, 100),  # Départ
                (300, 100),
                (300, 300),
                (500, 300),
                (500, 500),  # Arrivée
            ],
            2: [
                (100, 100),  # Départ
                (300, 100),
                (300, 200),
                (200, 200),
                (200, 400),
                (400, 400),
                (400, 500),  # Arrivée
            ],
            3: [
                (50, 50),  # Départ
                (150, 50),
                (150, 100),
                (100, 100),
                (100, 150),
                (200, 150),
                (200, 200),
                (150, 200),
                (150, 250),
                (250, 250),
                (250, 300),
                (100, 300),
                (100, 400),
                (300, 400),
                (300, 350),
                (200, 350),
                (200, 500),  # Arrivée
            ]
        }
        centered_paths = {level: self.center_path(path) for level, path in paths.items()}

        return centered_paths

    def center_path(self, path):
        """Centre un chemin dans la fenêtre"""
        # Calcul du centre actuel du chemin
        x_coords = [point[0] for point in path]
        y_coords = [point[1] for point in path]
        path_center_x = sum(x_coords) / len(x_coords)
        path_center_y = sum(y_coords) / len(y_coords)

        # Calcul du centre de la fenêtre
        window_center_x = WINDOW_WIDTH / 2
        window_center_y = WINDOW_HEIGHT / 2

        # Translation nécessaire
        x_translation = window_center_x - path_center_x
        y_translation = window_center_y - path_center_y

        # Appliquer la translation à chaque point
        return [(x + x_translation, y + y_translation) for x, y in path]

    def create_image_positions(self):
        """Crée les emplacements fixes des images et leur association pour chaque niveau."""
        return {
            1: [("image1", (200, 200)), ("image2", (400, 200)), ("image3", (200, 400)), ("image4", (400, 400))],
            2: [("image1", (150, 150)), ("image2", (450, 150)), ("image3", (150, 450)), ("image4", (450, 450))],
            3: [("image1", (100, 300)), ("image2", (300, 100)), ("image3", (500, 500)), ("image4", (700, 300))]
        }

    def manage_images(self, current_time):
        """Gère l'affichage d'une seule image à la fois avec rotation toutes les 5 secondes."""
        if self.participant_data['condition'] == 'sync':
            heart_rate = self.participant_data['heart_rate_before']  # Fixed heart rate
            if current_time - self.image_last_toggle > 60 / heart_rate:  # Interval based on BPM
                self.image_visible = not self.image_visible
                if self.image_visible:
                    self.current_image_index = (self.current_image_index + 1) % len(
                        self.image_positions[self.current_level])
                self.image_last_toggle = current_time
        if self.participant_data['condition'] == 'async':
            fixed_bpm = 100  # Fixed value for asynchronous condition
            if current_time - self.image_last_toggle > 60 / fixed_bpm:  # Interval for 100 BPM
                self.image_visible = not self.image_visible
                if self.image_visible:
                    self.current_image_index = (self.current_image_index + 1) % len(
                        self.image_positions[self.current_level])
                self.image_last_toggle = current_time
        if self.participant_data['condition'] == 'random':
            heart_rate = self.participant_data['heart_rate_before']  # Fixed heart rate
            total_blinks = int((heart_rate / 60) * self.time_left)  # Number of blinks in the level
            if len(self.game_data["response_times"]) < total_blinks:
                if current_time - self.image_last_toggle > random.uniform(0.5, 1.5):  # Random intervals
                    self.image_visible = not self.image_visible
                    if self.image_visible:
                        self.current_image_index = (self.current_image_index + 1) % len(
                            self.image_positions[self.current_level])
                    self.image_last_toggle = current_time

    def handle_image_click(self, mouse_pos):
        """Gère le clic sur l'image visible."""
        if self.image_visible:  # Les clics ne sont enregistrés que si une image est visible
            # Récupérer l'image active
            image_key, position = self.image_positions[self.current_level][self.current_image_index]
            x, y = position  # Extraire les coordonnées de la position
            image_rect = pygame.Rect(x, y, 50, 50)  # Zone cliquable (taille de l'image)

            if image_rect.collidepoint(mouse_pos):
                # Temps de réponse pour l'image cliquée
                response_time = time.time() - self.image_last_toggle
                self.game_data["response_times"].append(response_time)
                print(f"Image cliquée avec succès ({image_key}) en {response_time:.2f}s.")
                self.image_visible = False  # Cache l'image après un clic réussi
                return True

        # Si le clic est hors de l'image visible
        self.game_data["missed_bonus"] += 1
        print("Clic manqué ou hors de l'image.")
        return False

    def handle_bonus_click(self, mouse_pos):
        """Gère le clic sur un bonus"""
        if not self.active_bonus:
            return

        bonus_rect = pygame.Rect(
            self.active_bonus["position"][0] - 15,
            self.active_bonus["position"][1] - 15,
            30, 30
        )

        if bonus_rect.collidepoint(mouse_pos):
            response_time = time.time() - self.active_bonus["start_time"]
            self.game_data["response_times"].append(response_time)
            self.active_bonus = None

            # Jouer un son de succès ici si souhaité
            # pygame.mixer.Sound("success.wav").play()

    def handle_movement(self, direction):
        """Gère le mouvement du mobile sur le chemin"""
        current_path = self.level_paths[self.current_level]
        current_point = None

        # Trouver le point le plus proche sur le chemin
        min_dist = float('inf')
        for point in current_path:
            dist = ((self.mobile_pos[0] - point[0]) ** 2 + (self.mobile_pos[1] - point[1]) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                current_point = point

        if not current_point:
            return

        # Trouver les points connectés au point actuel
        connected_points = []
        for i, point in enumerate(current_path):
            if point == current_point:
                if i > 0:
                    connected_points.append(current_path[i - 1])
                if i < len(current_path) - 1:
                    connected_points.append(current_path[i + 1])

        # Déterminer la direction souhaitée
        desired_point = None
        for point in connected_points:
            if direction == "left" and point[0] < current_point[0]:
                desired_point = point
            elif direction == "right" and point[0] > current_point[0]:
                desired_point = point
            elif direction == "up" and point[1] < current_point[1]:
                desired_point = point
            elif direction == "down" and point[1] > current_point[1]:
                desired_point = point

        # Déplacer le mobile si la direction est valide
        if desired_point:
            self.mobile_pos = list(desired_point)
        else:
            self.game_data["command_errors"] += 1

    def schedule_bonus(self):
        """Gère l'apparition des bonus"""
        current_time = time.time()

        # Si aucun bonus n'est actif, on peut en créer un nouveau
        if not self.active_bonus and random.random() < 0.02:  # 2% de chance par frame
            current_path = self.level_paths[self.current_level]

            # Choisir un point aléatoire du chemin
            bonus_point = random.choice(current_path)

            # Vérifier que le point n'est pas trop proche du dernier bonus
            if self.bonus_history:
                last_bonus = self.bonus_history[-1]
                dist = ((bonus_point[0] - last_bonus[0]) ** 2 +
                        (bonus_point[1] - last_bonus[1]) ** 2) ** 0.5
                if dist < 100:  # Distance minimale entre les bonus
                    return

            self.active_bonus = {
                "position": bonus_point,
                "start_time": current_time
            }
            self.bonus_history.append(bonus_point)

            # Limiter l'historique des bonus
            if len(self.bonus_history) > 5:
                self.bonus_history.pop(0)


    def setup_ui(self):
        """Configure les éléments d'interface utilisateur"""
        # Boutons pour l'écran de configuration
        self.start_button = Button(WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT - 100, 200, 50, "Commencer")

        # Champs de saisie
        self.input_boxes = {
            'id': InputBox(WINDOW_WIDTH // 2 - 100, 100, 200, 32, ''),
            'age': InputBox(WINDOW_WIDTH // 2 - 100, 180, 200, 32, '', 'numeric'),
            'heart_rate': InputBox(WINDOW_WIDTH // 2 - 100, 260, 200, 32, '', 'numeric')
        }

        # Boutons de genre
        self.gender_buttons = {
            'homme': Button(WINDOW_WIDTH // 2 - 150, 340, 120, 40, "Homme"),
            'femme': Button(WINDOW_WIDTH // 2 + 30, 340, 120, 40, "Femme")
        }

        # Boutons de condition expérimentale
        self.condition_buttons = {
            'sync': Button(WINDOW_WIDTH // 2 - 250, 420, 150, 40, "Synchrone"),
            'async': Button(WINDOW_WIDTH // 2 - 75, 420, 150, 40, "Asynchrone"),
            'random': Button(WINDOW_WIDTH // 2 + 100, 420, 150, 40, "Aléatoire")
        }

        # Boutons d'évaluation
        self.evaluation_buttons = {
            'performance': [],
            'stress': [],
            'certitude': []
        }

        # Création des boutons d'évaluation
        levels = ["Très bas", "Bas", "Moyen", "Élevé", "Très élevé"]
        certitude_levels = ["Peu sûr", "Moyennement sûr", "Très sûr"]

        for i, level in enumerate(levels):
            self.evaluation_buttons['performance'].append(
                Button(50, 150 + i * 60, 200, 40, level)
            )
            self.evaluation_buttons['stress'].append(
                Button(300, 150 + i * 60, 200, 40, level)
            )

        for i, level in enumerate(certitude_levels):
            self.evaluation_buttons['certitude'].append(
                Button(550, 150 + i * 60, 200, 40, level)
            )

    def reset_game(self):
        """Réinitialise toutes les variables du jeu"""
        self.participant_data = {
            "id": "",
            "age": 0,
            "gender": "",
            "heart_rate_before": 0,
            "heart_rate_after": 0,
            "condition": "",
            "timestamps": []
        }

        self.current_level = 1
        self.game_state = "setup"
        self.level_paths = self.create_paths()
        self.mobile_pos = list(self.level_paths[1][0])  # Position initiale
        self.active_bonus = None
        self.bonus_history = []
        self.time_left = 60
        self.start_time = None
        self.heart_rate = 75
        self.current_evaluation = {}
        self.bip_start_time = None

        # Initialisez game_data AVANT d'ajouter des clés
        self.game_data = {
            "response_times": [],
            "missed_bonus": 0,
            "command_errors": 0,
            "level_evaluations": [],
            "bip_times": []
        }
        # Réinitialisation explicite des variables de bips

        self.image_visible = False
        self.image_last_toggle = 0

        # Réinitialisation des données de bips
        self.game_data['bip_times'] = []
        self.game_data['missed_bips'] = 0


    def handle_setup_input(self, event):
        """Gère les entrées dans l'écran de configuration"""
        # Gestion des champs de saisie
        for key, box in self.input_boxes.items():
            box.handle_event(event)  # Toujours écouter les événements pour chaque champ
            # Mise à jour immédiate des valeurs de participant_data
            if key == 'id':
                self.participant_data['id'] = box.text
            elif key == 'age':
                self.participant_data['age'] = int(box.text) if box.text.isdigit() else 0
            elif key == 'heart_rate':
                self.participant_data['heart_rate_before'] = int(box.text) if box.text.isdigit() else 0

        # Gestion des boutons de genre
        for gender, button in self.gender_buttons.items():
            if button.handle_event(event):
                for btn in self.gender_buttons.values():
                    btn.is_selected = False
                button.is_selected = True
                self.participant_data['gender'] = gender

        # Gestion des boutons de condition
        for condition, button in self.condition_buttons.items():
            if button.handle_event(event):
                for btn in self.condition_buttons.values():
                    btn.is_selected = False
                button.is_selected = True
                self.participant_data['condition'] = condition

        # Gestion du bouton de démarrage
        if self.start_button.handle_event(event):
            print("Données saisies :", self.participant_data)
            if self.validate_setup():
                print("Validation réussie. Début du jeu...")
                self.game_state = "playing"
                self.start_time = time.time()

    def validate_setup(self):
        """Vérifie que toutes les informations nécessaires sont remplies"""


        print(self.participant_data)
        required_fields = ['id', 'age', 'gender', 'heart_rate_before', 'condition']
        if self.participant_data['condition'] == 'async' and self.participant_data['heart_rate_before'] == 100:
            print("La fréquence cardiaque doit être différente de 100 BPM pour cette condition.")
            return False
        return all(self.participant_data.get(field) for field in required_fields)

    def handle_evaluation_input(self, event):
        """Gère les entrées dans l'écran d'évaluation"""
        for category, buttons in self.evaluation_buttons.items():
            for i, button in enumerate(buttons):
                if button.handle_event(event):
                    self.current_evaluation[category] = i + 1

                    if len(self.current_evaluation) == 3:  # Toutes les évaluations sont faites
                        self.game_data['level_evaluations'].append({
                            'level': self.current_level,
                            **self.current_evaluation
                        })
                        self.current_evaluation = {}

                        if self.current_level < 3:
                            self.current_level += 1
                            self.game_state = "playing"
                            self.start_time = time.time()
                            self.mobile_pos = list(self.level_paths[self.current_level][0])
                        else:
                            self.game_state = "finished"
                            self.save_data()

    def draw_setup_screen(self):
        """Dessine l'écran de configuration"""
        # Titre
        font = pygame.font.Font(None, 46)
        title = font.render("Configuration du Participant", True, BLACK)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 30))

        # Labels
        font = pygame.font.Font(None, 30)
        labels = {
            'id': 'Identifiant:',
            'age': 'Âge:',
            'heart_rate': 'Fréquence cardiaque:'
        }

        for i, (key, text) in enumerate(labels.items()):
            label = font.render(text, True, BLACK)
            screen.blit(label, (WINDOW_WIDTH // 2 - 250, 105 + i * 80))
            self.input_boxes[key].draw(screen)

        # Dessin des boutons
        for button in self.gender_buttons.values():
            button.draw(screen)
        for button in self.condition_buttons.values():
            button.draw(screen)
        self.start_button.draw(screen)

    def draw_game_screen(self):
        """Dessine l'écran de jeu"""
        # Fond
        screen.fill(WHITE)

        # Dessine le chemin
        current_path = self.level_paths[self.current_level]
        for i in range(len(current_path) - 1):
            pygame.draw.line(screen, BLACK, current_path[i], current_path[i + 1], 2)

        # Points du chemin
        for point in current_path:
            pygame.draw.circle(screen, BLUE, point, 5)

        # Dessine le mobile
        pygame.draw.circle(screen, RED, self.mobile_pos, 10)

        # Dessine le bonus actif avec animation de clignotement
        if self.active_bonus:
            alpha = int(255 * (0.5 + 0.5 * abs(math.sin(time.time() * 5))))
            bonus_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(bonus_surface, (*YELLOW, alpha), (15, 15), 15)
            screen.blit(bonus_surface,
                        (self.active_bonus["position"][0] - 15,
                         self.active_bonus["position"][1] - 15))

        # Informations
        font = pygame.font.Font(None, 32)
        info_texts = [
            f"Niveau: {self.current_level}",
            f"Temps: {self.time_left}s",
            f"Score: {len(self.game_data['response_times'])}"
        ]

        for i, text in enumerate(info_texts):
            surface = font.render(text, True, BLACK)
            screen.blit(surface, (10, 10 + i * 40))

        # Dessine les images clignotantes
        if self.image_visible:  # Si l'image doit être visible
            image_key, pos = self.image_positions[self.current_level][self.current_image_index]
            screen.blit(self.images[image_key], pos)

    def draw_evaluation_screen(self):
        """Dessine l'écran d'évaluation"""
        # Titre
        font = pygame.font.Font(None, 48)
        title = font.render(f"Évaluation du niveau {self.current_level}", True, BLACK)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 30))

        # Sous-titres
        font = pygame.font.Font(None, 36)
        subtitles = {
            'performance': "Performance",
            'stress': "Niveau de stress",
            'certitude': "Certitude"
        }

        x_positions = [150, 400, 650]
        for i, (key, text) in enumerate(subtitles.items()):
            surface = font.render(text, True, BLACK)
            screen.blit(surface, (x_positions[i] - surface.get_width() // 2, 100))

            # Dessine les boutons d'évaluation
            for button in self.evaluation_buttons[key]:
                button.draw(screen)

    def draw_final_screen(self):
        """Dessine l'écran final"""
        # Titre
        font = pygame.font.Font(None, 48)
        title = font.render("Expérience terminée", True, BLACK)
        screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 30))

        # Statistiques
        font = pygame.font.Font(None, 36)
        stats = [
            f"Temps de réaction moyen: {self.get_average_response_time():.2f}s",
            f"Bonus manqués: {self.game_data['missed_bonus']}",
            f"Erreurs de commande: {self.game_data['command_errors']}"
        ]

        for i, text in enumerate(stats):
            surface = font.render(text, True, BLACK)
            screen.blit(surface, (WINDOW_WIDTH // 2 - surface.get_width() // 2, 150 + i * 50))


        # Message de sauvegarde
        save_text = font.render("Données sauvegardées", True, GREEN)
        screen.blit(save_text, (WINDOW_WIDTH // 2 - save_text.get_width() // 2, 400))

        # Instructions pour quitter
        quit_text = font.render("Appuyez sur ESPACE pour quitter", True, BLACK)
        screen.blit(quit_text, (WINDOW_WIDTH // 2 - quit_text.get_width() // 2, 500))

    def get_average_response_time(self):
        """Calcule le temps de réaction moyen"""
        if not self.game_data['response_times']:
            return 0
        return sum(self.game_data['response_times']) / len(self.game_data['response_times'])

    def save_data(self):
        """Sauvegarde les données de l'expérience"""
        # Création du dossier de données s'il n'existe pas
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # Préparation des données
        data = {
            "participant_info": {
                "id": self.participant_data["id"],
                "age": self.participant_data["age"],
                "gender": self.participant_data["gender"],
                "condition": self.participant_data["condition"],
                "heart_rate_before": self.participant_data["heart_rate_before"],
                "heart_rate_after": self.participant_data["heart_rate_after"]
            },

            "performance_data": {
                "response_times": self.game_data["response_times"],
                "average_response_time": self.get_average_response_time(),
                "missed_bonus": self.game_data["missed_bonus"],
                "command_errors": self.game_data["command_errors"]
            },
            "evaluations": self.game_data["level_evaluations"],
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
            "bip_data": {
                "condition": self.participant_data['condition'],
                "heart_rate": self.participant_data['heart_rate_before'],
                "total_bips": len(self.game_data['bip_times']),
                "missed_bips": self.game_data['missed_bips']
            },
        }

        # Sauvegarde au format JSON
        filename = data_dir / f"participant_{self.participant_data['id']}_{data['timestamp']}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Sauvegarde au format CSV pour analyse facile
        csv_filename = data_dir / f"participant_{self.participant_data['id']}_{data['timestamp']}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Participant ID', 'Age', 'Genre', 'Condition',
                             'FC Avant', 'FC Après', 'Temps Moyen', 'Bonus Manqués',
                             'Erreurs Commande'])
            writer.writerow([
                data['participant_info']['id'],
                data['participant_info']['age'],
                data['participant_info']['gender'],
                data['participant_info']['condition'],
                data['participant_info']['heart_rate_before'],
                data['participant_info']['heart_rate_after'],
                data['performance_data']['average_response_time'],
                data['performance_data']['missed_bonus'],
                data['performance_data']['command_errors']
            ])

    def run(self):
        """Boucle principale du jeu"""
        running = True
        while running:
            current_time = time.time()

            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if self.game_state == "finished":
                        running = False

                # Gestion des événements selon l'état du jeu
                if self.game_state == "setup":
                    self.handle_setup_input(event)  # Appelé à chaque événement
                elif self.game_state == "playing":
                    self.handle_playing_input(event)
                elif self.game_state == "evaluation":
                    self.handle_evaluation_input(event)

            # Mise à jour du jeu
            if self.game_state == "playing":
                self.update_game(current_time)

            # Dessin
            screen.fill(WHITE)
            if self.game_state == "setup":
                self.draw_setup_screen()
            elif self.game_state == "playing":
                self.draw_game_screen()
            elif self.game_state == "evaluation":
                self.draw_evaluation_screen()
            elif self.game_state == "finished":
                self.draw_final_screen()

            pygame.display.flip()
            clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def handle_playing_input(self, event):
        """Gère les entrées pendant le jeu"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.image_visible:  # Vérifier le clic sur l'image visible
                self.handle_image_click(mouse_pos)
            if self.active_bonus:  # Vérifier le clic sur un bonus actif
                self.handle_bonus_click(mouse_pos)

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
                direction = None
                if event.key == pygame.K_LEFT:
                    direction = "left"
                elif event.key == pygame.K_RIGHT:
                    direction = "right"
                elif event.key == pygame.K_UP:
                    direction = "up"
                elif event.key == pygame.K_DOWN:
                    direction = "down"

                if direction:
                    self.handle_movement(direction)

    def update_game(self, current_time):
        """Met à jour l'état du jeu"""
        self.manage_images(current_time)
        self.manage_bips(current_time)

        if self.start_time is None:
            self.start_time = current_time

        # Mise à jour du temps restant
        elapsed_time = int(current_time - self.start_time)
        self.time_left = max(0, 60 - elapsed_time)

        # Vérification de fin de niveau
        if self.time_left <= 0:
            self.game_state = "evaluation"
            return

        # Gestion des bonus
        self.schedule_bonus()

        # Vérification des bonus expirés
        if self.active_bonus:
            if current_time - self.active_bonus["start_time"] > 5:
                self.game_data["missed_bonus"] += 1
                self.active_bonus = None


if __name__ == "__main__":
    game = Game()
    game.run()