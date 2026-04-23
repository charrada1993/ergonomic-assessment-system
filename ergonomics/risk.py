# ergonomics/risk.py
class RiskAnalyzer:
    @staticmethod
    def detect_anomalies(angles, rula_score, reba_score):
        anomalies = []
        if angles.get('trunk', 0) > 60:
            anomalies.append("Trunk flexion > 60°")
        if angles.get('neck', 0) > 20:
            anomalies.append("Neck flexion > 20°")
        if angles.get('upper_arm_left', 0) > 90:
            anomalies.append("Upper arm elevation > 90°")
        if rula_score > 6:
            anomalies.append("RULA high risk")
        if reba_score > 10:
            anomalies.append("REBA high risk")
        return anomalies