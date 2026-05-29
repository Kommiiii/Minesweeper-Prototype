import os
import json
from src.utilities.constants import get_resource_path, get_save_path

class ScoreManager:
    _instance = None
    SCORE_FILE = "scores.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScoreManager, cls).__new__(cls)
            cls._instance.load()
        return cls._instance

    def load(self):
        self.scores = {
            "Beginner": [],
            "Intermediate": [],
            "Expert": [],
            "Custom": []
        }
        path = get_save_path(self.SCORE_FILE)
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.scores.update(json.load(f))

    def save(self):
        path = get_save_path(self.SCORE_FILE)
        with open(path, 'w') as f:
            json.dump(self.scores, f, indent=4)

    def add_score(self, difficulty, time, bvs):
        if difficulty not in self.scores:
            self.scores[difficulty] = []
        self.scores[difficulty].append({"time": round(time, 3), "bvs": round(bvs, 4)})
        self.scores[difficulty] = sorted(self.scores[difficulty], key=lambda x: x["time"])[:10]
        self.save()