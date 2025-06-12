import json
import boto3
import urllib.parse
from datetime import datetime
from decimal import Decimal
import logging

# setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# aws clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def convert_float_to_decimal(obj):
   # dynamodb needs decimal instead of float
   if isinstance(obj, float):
       return Decimal(str(obj))
   elif isinstance(obj, dict):
       return {k: convert_float_to_decimal(v) for k, v in obj.items()}
   return obj

def lambda_handler(event, context):
   try:
       # get bucket and file info from s3 event
       bucket = event['Records'][0]['s3']['bucket']['name']
       key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
       
       logger.info(f"Processing file: {key} from bucket: {bucket}")
       
       # read file from s3
       response = s3_client.get_object(Bucket=bucket, Key=key)
       content = response['Body'].read().decode('utf-8')
       data = json.loads(content)
       
       # connect to dynamodb table
       table_name = 'energy-data-analytics-energy-data'
       table = dynamodb.Table(table_name)
       
       processed_count = 0
       anomaly_count = 0
       
       # processes each record in the file
       for record in data:
           # calculate difference between generated and consumed
           net_energy = record['energy_generated_kwh'] - record['energy_consumed_kwh']
           
           # check if this record has problems
           is_anomaly = (record['energy_generated_kwh'] < 0 or 
                        record['energy_consumed_kwh'] < 0 or
                        record['energy_generated_kwh'] > 1000 or
                        record['energy_consumed_kwh'] > 1000)
           
           if is_anomaly:
               anomaly_count += 1
               # log the problem for alerts
               logger.error(f"ANOMALY_DETECTED - Site: {record['site_id']}, Time: {record['timestamp']}, Generated: {record['energy_generated_kwh']}, Consumed: {record['energy_consumed_kwh']}")
           
           # prepared data for database - converting floats to decimal
           item = convert_float_to_decimal({
               'site_id': record['site_id'],
               'timestamp': record['timestamp'],
               'energy_generated_kwh': record['energy_generated_kwh'],
               'energy_consumed_kwh': record['energy_consumed_kwh'],
               'net_energy_kwh': net_energy,
               'anomaly': is_anomaly,
               'processed_at': datetime.utcnow().isoformat()
           })
           
           # save to database
           table.put_item(Item=item)
           processed_count += 1
       
       logger.info(f"Processed {processed_count} records, found {anomaly_count} anomalies")
       

       # return success
       return {
           'statusCode': 200,
           'body': json.dumps({
               'message': f'Successfully processed {processed_count} records',
               'anomalies_found': anomaly_count
           })
       }
       
   except Exception as e:
       # something went wrong
       logger.error(f"Error processing file: {str(e)}")
       return {
           'statusCode': 500,
           'body': json.dumps({'error': str(e)})
       }# testing CI/CD feature 1"