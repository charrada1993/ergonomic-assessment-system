# reporting/report_generator.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from config import Config

class ReportGenerator:
    @staticmethod
    def generate(csv_path):
        df = pd.read_csv(csv_path)
        report_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        report_path = os.path.join(Config.REPORT_DIR, report_filename)
        doc = SimpleDocTemplate(report_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph("Ergonomic Risk Assessment Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Metadata
        duration = df['timestamp'].max() - df['timestamp'].min()
        story.append(Paragraph(f"Session duration: {duration:.1f} seconds", styles['Normal']))
        story.append(Paragraph(f"Number of samples: {len(df)}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Joint statistics
        joint_cols = ['neck_deg', 'trunk_deg', 'upper_arm_deg', 'elbow_deg', 'wrist_deg']
        stats = df[joint_cols].describe().round(1)
        data = [['Joint', 'Min', 'Max', 'Mean', 'Std']]
        for col in joint_cols:
            data.append([col, stats[col]['min'], stats[col]['max'],
                         stats[col]['mean'], stats[col]['std']])
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(Paragraph("Joint Angle Statistics", styles['Heading2']))
        story.append(table)
        story.append(Spacer(1, 12))

        # RULA/REBA summary
        rula_avg = df['RULA_score'].mean()
        reba_avg = df['REBA_score'].mean()
        story.append(Paragraph(f"Average RULA Score: {rula_avg:.1f}", styles['Normal']))
        story.append(Paragraph(f"Average REBA Score: {reba_avg:.1f}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Plot risk evolution
        plt.figure(figsize=(6,3))
        plt.plot(df['timestamp'], df['RULA_score'], label='RULA')
        plt.plot(df['timestamp'], df['REBA_score'], label='REBA')
        plt.xlabel('Time (s)')
        plt.ylabel('Score')
        plt.legend()
        plot_path = os.path.join(Config.STATIC_DIR, 'temp_plot.png')
        plt.savefig(plot_path)
        plt.close()
        story.append(Image(plot_path, width=400, height=200))
        os.remove(plot_path)

        # Recommendations
        story.append(Paragraph("Clinical Recommendations", styles['Heading2']))
        if rula_avg > 5 or reba_avg > 8:
            rec = "High risk detected. Immediate intervention required: adjust workstation, reduce load, vary tasks."
        else:
            rec = "Moderate risk. Consider ergonomic improvements: arm supports, adjustable chair, frequent breaks."
        story.append(Paragraph(rec, styles['Normal']))

        doc.build(story)
        return report_path