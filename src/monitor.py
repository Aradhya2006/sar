import pandas as pd
from anonymizer import SARAnonymizer
from generator import SARGenerator
from database import SARDatabase

class FraudMonitor:
    def __init__(self):
        # Initializing our core engines
        self.anon = SARAnonymizer()
        self.gen = SARGenerator()
        self.db = SARDatabase()

    def auto_scan(self, csv_path):
        """
        Reads a CSV, detects structuring, and returns a list of alerts.
        """
        df = pd.read_csv(csv_path)
        
        # AUTOMATIC RULE: Find total deposits >= 10,000 across multiple entries
        summary = df.groupby('customer_name')['amount'].agg(['sum', 'count']).reset_index()
        frauds = summary[(summary['sum'] >= 10000) & (summary['count'] > 1)]
        
        results = []
        for _, row in frauds.iterrows():
            # 1. ALERT: Create the notification details
            alert_details = f"Fraud Detected: {row['customer_name']} deposited ${row['sum']} in {row['count']} transactions."
            
            # 2. REPORT: Process through the AI pipeline
            masked = self.anon.mask_data(alert_details)
            report = self.gen.generate_narrative(masked)
            
            # 3. SAVE: Store in MongoDB
            report_id = self.db.save_report(alert_details, masked, report)
            
            # 4. TRACK: Add to our list for the UI
            results.append({
                "name": row['customer_name'],
                "total": row['sum'],
                "id": report_id,
                "narrative": report
            })
            
        return results