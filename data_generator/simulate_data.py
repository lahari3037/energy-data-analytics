import json
import random
import boto3
import time
from datetime import datetime
import schedule

class EnergyDataSimulator:
   def __init__(self, bucket_name):
       self.bucket_name = bucket_name
       self.s3_client = boto3.client('s3', region_name='us-east-1')
       # list of energy sites to simulate
       self.sites = ['SITE_001', 'SITE_002', 'SITE_003', 'SITE_004', 'SITE_005']
       
   def generate_energy_record(self, site_id):
       # create realistic energy values
       base_generation = random.uniform(50, 200)
       base_consumption = random.uniform(30, 150)
       
       # sometimes generate anomalies (5% chance)
       if random.random() < 0.05:
           energy_generated = random.uniform(-10, 10) 
       else:
           energy_generated = base_generation + random.uniform(-20, 20)
           
       if random.random() < 0.05:
           energy_consumed = random.uniform(-10, 10)  
       else:
           energy_consumed = base_consumption + random.uniform(-15, 15)
       
       return {
           'site_id': site_id,
           'timestamp': datetime.utcnow().isoformat() + 'Z',
           'energy_generated_kwh': round(energy_generated, 2),
           'energy_consumed_kwh': round(energy_consumed, 2)
       }
   
   def generate_batch_data(self):
       # create data for all sites
       records = []
       for site_id in self.sites:
           num_records = random.randint(1, 3)  # each site gets 1-3 records
           for _ in range(num_records):
               records.append(self.generate_energy_record(site_id))
       return records
   
   def upload_to_s3(self, data):
       try:
           # create filename with current time
           timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
           filename = f"energy_data_{timestamp}.json"
           json_data = json.dumps(data, indent=2)
           
           # upload to s3 bucket
           self.s3_client.put_object(
               Bucket=self.bucket_name,
               Key=filename,
               Body=json_data,
               ContentType='application/json'
           )
           
           print(f"Uploaded {len(data)} records to {filename}")
           
       except Exception as e:
           print(f"Error uploading to S3: {str(e)}")
   
   def simulate_continuous_data(self):
       print("Starting energy data simulation...")
       print(f"Generating data for sites: {', '.join(self.sites)}")
       print("Data will be uploaded every 5 minutes")
       
       def upload_data():
           # generate and upload new data
           data = self.generate_batch_data()
           self.upload_to_s3(data)
       
       # schedule uploads every 5 minutes
       schedule.every(5).minutes.do(upload_data)
       upload_data()  # upload first batch immediately
       
       # keep running and check schedule
       while True:
           schedule.run_pending()
           time.sleep(1)

def main():
   # replace with your actual bucket name
   BUCKET_NAME = "energy-data-analytics-energy-data-a1h5jwlw"
   simulator = EnergyDataSimulator(BUCKET_NAME)
   simulator.simulate_continuous_data()

if __name__ == "__main__":
   main()