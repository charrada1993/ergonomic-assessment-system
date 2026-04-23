# ergonomics/reba.py
class REBACalculator:
    @staticmethod
    def score_trunk(angle, rotated=False, lateral=False):
        if angle <= 0: s = 1
        elif angle <= 20: s = 2
        elif angle <= 60: s = 3
        else: s = 4
        if angle < 0: s = 2
        if rotated: s += 1
        if lateral: s += 1
        return min(s, 6)

    @staticmethod
    def score_neck(angle, rotated=False, lateral=False):
        if angle <= 20: s = 1
        else: s = 2
        if angle < 0: s = 2
        if rotated: s += 1
        if lateral: s += 1
        return min(s, 6)

    @staticmethod
    def score_legs(posture=1):
        return posture   # 1=stable, 2=one bent, 3=squat, 4=unstable

    @staticmethod
    def group_a_table(trunk, neck):
        table = [
            [1,2,3,4,5,6],
            [2,2,3,4,5,6],
            [3,3,4,5,6,7],
            [4,4,5,6,7,8],
            [5,5,6,7,8,9],
            [6,6,7,8,9,10]
        ]
        return table[trunk-1][neck-1]

    @staticmethod
    def score_upper_arm(angle, supported=False, load=False):
        if angle <= 20: s = 1
        elif angle <= 45: s = 2
        elif angle <= 90: s = 3
        else: s = 4
        if supported: s += 1
        if load: s += 1
        return min(s, 6)

    @staticmethod
    def score_lower_arm(angle):
        if 60 <= angle <= 100:
            return 1
        return 2

    @staticmethod
    def score_wrist(angle, deviated=False):
        s = 2 if abs(angle) > 15 else 1
        if deviated:
            s += 1
        return min(s, 3)

    @staticmethod
    def group_b_table(upper_arm, lower_arm):
        table = [
            [1,2,3,4],
            [2,2,3,4],
            [3,3,3,5],
            [4,4,5,5]
        ]
        return table[upper_arm-1][lower_arm-1]

    @staticmethod
    def score_load(weight_kg, grip_quality=0):
        if weight_kg < 5: load = 0
        elif weight_kg <= 10: load = 1
        else: load = 2
        return load + grip_quality   # grip: 0=good,1=average,2=poor

    @staticmethod
    def final_table(scoreA, scoreB):
        table = [
            [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
            [2,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
            [3,3,3,4,5,6,7,8,9,10,11,12,13,14,15],
            [4,4,4,4,5,6,7,8,9,10,11,12,13,14,15],
            [5,5,5,5,5,6,7,8,9,10,11,12,13,14,15],
            [6,6,6,6,6,6,7,8,9,10,11,12,13,14,15],
            [7,7,7,7,7,7,7,8,9,10,11,12,13,14,15]
        ]
        return table[scoreA-1][scoreB-1]

    def compute(self, angles, load_kg=0, grip=0, repetitive=False):
        trunk = self.score_trunk(angles.get('trunk', 0))
        neck = self.score_neck(angles.get('neck', 0))
        legs = self.score_legs(1)
        scoreA = self.group_a_table(trunk, neck) + legs
        ua = self.score_upper_arm(angles.get('upper_arm_left', 0))
        la = self.score_lower_arm(angles.get('elbow_left', 90))
        wrist = self.score_wrist(angles.get('wrist_left', 0))
        scoreB = self.group_b_table(ua, la) + wrist
        final = self.final_table(scoreA, scoreB)
        load_score = self.score_load(load_kg, grip)
        activity = 1 if repetitive else 0
        final += load_score + activity
        risk = self.interpret(final)
        return {"REBA_score": final, "risk_level": risk, "scoreA": scoreA, "scoreB": scoreB}

    @staticmethod
    def interpret(score):
        if score <= 1: return "Négligeable"
        elif score <= 3: return "Faible"
        elif score <= 7: return "Moyen"
        elif score <= 10: return "Élevé"
        else: return "Très élevé"