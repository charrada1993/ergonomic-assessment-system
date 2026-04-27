# ergonomics/rula.py
class RULACalculator:
    @staticmethod
    def score_upper_arm(angle, rotated=False, supported=False, abducted=False):
        if angle <= 20: s = 1
        elif angle <= 45: s = 2
        elif angle <= 90: s = 3
        else: s = 4
        if rotated: s += 1
        if abducted: s += 1
        if supported: s -= 1
        return min(max(s, 1), 6)

    @staticmethod
    def score_lower_arm(elbow_angle):
        if 60 <= elbow_angle <= 100:
            return 1
        return 2

    @staticmethod
    def score_wrist(angle, deviation=0):
        angle = abs(angle)
        if angle <= 15: s = 1
        elif angle <= 30: s = 2
        else: s = 3
        s += deviation
        return min(s, 4)

    @staticmethod
    def score_neck(angle, rotated=False, lateral=False):
        if 0 <= angle <= 10: s = 1
        elif angle <= 20: s = 2
        elif angle > 20: s = 3
        if angle < 0: s = 4  # extension
        if rotated: s += 1
        if lateral: s += 1
        return min(max(s, 1), 6)

    @staticmethod
    def score_trunk(angle, rotated=False, lateral=False):
        if 0 <= angle <= 20: s = 2
        elif angle <= 60: s = 3
        elif angle > 60: s = 4
        else: s = 1 # straight (0)
        if angle < 0: s = 2  # extension
        if rotated: s += 1
        if lateral: s += 1
        return min(max(s, 1), 6)

    @staticmethod
    def score_legs(stable=True):
        return 1 if stable else 2

    @staticmethod
    def score_load(weight_kg, repetitive=False):
        if weight_kg < 1: return 0
        elif weight_kg <= 5: return 1 if repetitive else 0
        else: return 2

    @staticmethod
    def group_a_table(upper_arm, lower_arm, wrist, wrist_twist, load):
        # Maps (upper_arm, lower_arm) -> [col1, col2, col3, col4]
        table = {
            (1,1): [1, 2, 2, 3], (1,2): [2, 2, 3, 3],
            (2,1): [2, 3, 3, 3], (2,2): [3, 3, 4, 4],
            (3,1): [3, 3, 4, 4], (3,2): [4, 4, 5, 5],
            (4,1): [4, 4, 5, 5], (4,2): [5, 5, 6, 6],
            (5,1): [5, 5, 6, 6], (5,2): [6, 6, 7, 7],
            (6,1): [6, 6, 7, 7], (6,2): [7, 7, 8, 8]
        }
        ua = min(max(upper_arm, 1), 6)
        la = min(max(lower_arm, 1), 2)
        row = table.get((ua, la), [1, 2, 2, 3])
        # Column is wrist + wrist_twist - 1 (1 to 4)
        col_idx = min(max(wrist + wrist_twist - 1, 1), 4) - 1
        return row[col_idx] + load

    @staticmethod
    def group_b_table(neck, trunk, legs):
        tbl = [
            [1,2,3,5,6,7],
            [2,2,3,5,6,7],
            [3,3,4,6,7,7],
            [5,5,6,7,7,7],
            [6,6,7,7,7,7],
            [7,7,7,7,7,7]
        ]
        n = min(max(neck, 1), 6)
        t = min(max(trunk, 1), 6)
        return tbl[n-1][t-1] + legs

    @staticmethod
    def final_score(scoreA, scoreB):
        matrix = [
            [1,2,3,3,4,5,5],
            [2,2,3,4,4,5,5],
            [3,3,3,4,4,5,6],
            [3,3,4,4,4,5,6],
            [4,4,4,4,5,6,7],
            [5,5,5,5,6,7,7],
            [5,5,6,6,7,7,7]
        ]
        sa = min(max(scoreA, 1), 7)
        sb = min(max(scoreB, 1), 7)
        return matrix[sa-1][sb-1]

    def compute(self, angles, load_kg=0, repetitive=False):
        ua = self.score_upper_arm(angles.get('upper_arm_left', 0), abducted=(angles.get('shoulder_mod', 0) > 0))
        la = self.score_lower_arm(angles.get('elbow_left', 90))
        wrist = self.score_wrist(angles.get('wrist_left', 0))
        neck = self.score_neck(angles.get('neck', 0), lateral=(angles.get('neck_mod', 0) > 0))
        trunk = self.score_trunk(angles.get('trunk', 0), lateral=(angles.get('trunk_mod', 0) > 0))
        legs = self.score_legs(angles.get('legs_stable', True))
        
        load_score = self.score_load(load_kg, repetitive)
        
        # Assume wrist twist is neutral (1) for now since mediapipe limits hand rotation
        groupA = self.group_a_table(ua, la, wrist, 1, load_score)
        groupB = self.group_b_table(neck, trunk, legs)
        final = self.final_score(groupA, groupB)
        risk = self.interpret(final)
        
        return {
            "RULA_score": final, "risk_level": risk, 
            "rula_details": {
                "score_a": groupA, "score_b": groupB, "score_c": final,
                "upper_arm": ua, "lower_arm": la, "wrist": wrist, "wrist_twist": 1,
                "neck": neck, "trunk": trunk, "legs": legs, "load": load_score,
                "muscle": 1 if repetitive else 0, "activity": 1 if repetitive else 0
            }
        }

    @staticmethod
    def interpret(score):
        if score <= 2: return "Négligeable / Acceptable"
        elif score <= 4: return "Faible / Surveillance"
        elif score <= 6: return "Moyen / Amélioration nécessaire"
        else: return "Élevé / Intervention rapide"