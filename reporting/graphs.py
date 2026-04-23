# reporting/graphs.py
import matplotlib.pyplot as plt
import pandas as pd
import os
from config import Config

class GraphGenerator:
    @staticmethod
    def plot_angles_over_time(df, save_path=None):
        """Generate a line plot of joint angles over time."""
        plt.figure(figsize=(10, 6))
        cols = ['neck_deg', 'trunk_deg', 'upper_arm_left_deg', 'elbow_left_deg', 'wrist_left_deg']
        for col in cols:
            if col in df.columns:
                plt.plot(df['timestamp'], df[col], label=col.replace('_deg', ''))
        plt.xlabel('Time (s)')
        plt.ylabel('Angle (degrees)')
        plt.title('Joint Angles Over Time')
        plt.legend()
        plt.grid(True)
        if save_path:
            plt.savefig(save_path, dpi=100)
            plt.close()
        else:
            plt.show()

    @staticmethod
    def plot_risk_scores(df, save_path=None):
        """Generate a line plot of RULA and REBA scores."""
        plt.figure(figsize=(10, 6))
        plt.plot(df['timestamp'], df['RULA_score'], label='RULA', marker='o')
        plt.plot(df['timestamp'], df['REBA_score'], label='REBA', marker='s')
        plt.xlabel('Time (s)')
        plt.ylabel('Score')
        plt.title('Ergonomic Risk Scores Evolution')
        plt.legend()
        plt.grid(True)
        if save_path:
            plt.savefig(save_path, dpi=100)
            plt.close()
        else:
            plt.show()

    @staticmethod
    def save_all_graphs(csv_path):
        """Read CSV, generate graphs, save as PNG in static folder."""
        df = pd.read_csv(csv_path)
        base_name = os.path.splitext(os.path.basename(csv_path))[0]
        angles_path = os.path.join(Config.STATIC_DIR, f"{base_name}_angles.png")
        risk_path = os.path.join(Config.STATIC_DIR, f"{base_name}_risk.png")
        GraphGenerator.plot_angles_over_time(df, angles_path)
        GraphGenerator.plot_risk_scores(df, risk_path)
        return angles_path, risk_path