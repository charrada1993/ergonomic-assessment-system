# ergonomics/reba.py
class REBACalculator:
    @staticmethod
    def score_trunk(angle, rotated=False, lateral=False):
        if 0 <= angle <= 20: s = 2
        elif angle <= 60: s = 3
        elif angle > 60: s = 4
        else: s = 1 # straight
        if angle < 0: s = 2 # extension
        if rotated: s += 1
        if lateral: s += 1
        return min(max(s, 1), 6)

    @staticmethod
    def score_neck(angle, rotated=False, lateral=False):
        if 0 <= angle <= 20: s = 1
        elif angle > 20: s = 2
        if angle < 0: s = 2 # extension
        if rotated: s += 1
        if lateral: s += 1
        return min(max(s, 1), 4)

    @staticmethod
    def score_legs(posture=1):
        return min(max(posture, 1), 4)

    @staticmethod
    def group_a_table(trunk, neck):
        table = [
            [1, 2, 2, 3, 4], # Neck 1
            [2, 3, 4, 5, 6], # Neck 2
            [3, 4, 5, 6, 7]  # Neck 3
        ]
        n = min(max(neck, 1), 3)
        t = min(max(trunk, 1), 5)
        return table[n-1][t-1]

    @staticmethod
    def score_upper_arm(angle, supported=False, abducted=False):
        if angle <= 20: s = 1
        elif angle <= 45: s = 2
        elif angle <= 90: s = 3
        else: s = 4
        if abducted: s += 1
        if supported: s -= 1
        return min(max(s, 1), 6)

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
        return min(max(s, 1), 3)

    @staticmethod
    def group_b_table(upper_arm, lower_arm):
        table = [
            [1, 2, 3, 4, 5, 6], # Lower arm 1
            [2, 3, 4, 5, 6, 7]  # Lower arm 2
        ]
        la = min(max(lower_arm, 1), 2)
        ua = min(max(upper_arm, 1), 6)
        return table[la-1][ua-1]

    @staticmethod
    def score_load(weight_kg, grip_quality=0):
        if weight_kg < 5: load = 0
        elif weight_kg <= 10: load = 1
        else: load = 2
        return load + grip_quality   # grip: 0=good,1=average,2=poor

    @staticmethod
    def final_table(scoreA, scoreB):
        # 12x12 REBA Table C
        table = [
            [1,1,1,2,3,3,4,5,6,7,7,7],
            [1,2,2,3,4,4,5,6,6,7,7,8],
            [2,3,3,3,4,5,6,7,7,8,8,8],
            [3,4,4,4,5,6,7,8,8,9,9,9],
            [4,4,4,5,6,7,8,8,9,9,9,9],
            [6,6,6,7,8,8,9,9,10,10,10,10],
            [7,7,7,8,9,9,9,10,10,11,11,11],
            [8,8,8,9,10,10,10,10,10,11,11,11],
            [9,9,9,10,10,10,11,11,11,12,12,12],
            [10,10,10,11,11,11,11,12,12,12,12,12],
            [11,11,11,11,12,12,12,12,12,12,12,12],
            [12,12,12,12,12,12,12,12,12,12,12,12]
        ]
        sa = min(max(scoreA, 1), 12)
        sb = min(max(scoreB, 1), 12)
        return table[sa-1][sb-1]

    def compute(self, angles, load_kg=0, grip=0, repetitive=False):
        trunk = self.score_trunk(angles.get('trunk', 0), lateral=(angles.get('trunk_mod', 0) > 0))
        neck = self.score_neck(angles.get('neck', 0), lateral=(angles.get('neck_mod', 0) > 0))
        legs = self.score_legs(1) # Assume stable standing for now
        
        scoreA = self.group_a_table(trunk, neck) + legs
        
        ua = self.score_upper_arm(angles.get('upper_arm_left', 0), abducted=(angles.get('shoulder_mod', 0) > 0))
        la = self.score_lower_arm(angles.get('elbow_left', 90))
        wrist = self.score_wrist(angles.get('wrist_left', 0))
        
        scoreB = self.group_b_table(ua, la) + wrist
        
        final = self.final_table(scoreA, scoreB)
        
        load_score = self.score_load(load_kg, grip)
        activity = 1 if repetitive else 0
        final += load_score + activity
        
        risk = self.interpret(final)
        return {
            "REBA_score": final, "risk_level": risk, 
            "reba_details": {
                "table_a": scoreA - legs, "table_b": scoreB - wrist, "score_c": final - load_score - activity,
                "trunk": trunk, "neck": neck, "legs": legs, "trunk_mod": angles.get('trunk_mod', 0), "neck_mod": angles.get('neck_mod', 0), "knee_mod": 0,
                "upper_arm": ua, "shoulder_mod": angles.get('shoulder_mod', 0), "lower_arm": la, "wrist": wrist, "wrist_twist": 0, "coupling": grip, "load": load_score
            }
        }

    @staticmethod
    def interpret(score):
        if score <= 1: return "Négligeable"
        elif score <= 3: return "Faible"
        elif score <= 7: return "Moyen"
        elif score <= 10: return "Élevé"
        else: return "Très élevé"