from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime
from typing import Optional
import json

app = FastAPI(title="Renewable Energy Data API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'energy-data-analytics-energy-data'

@app.get("/")
async def root():
    return {"message": "Renewable Energy Data API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/sites/{site_id}/data")
async def get_site_data(
    site_id: str,
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: int = Query(100)
):
    try:
        table = dynamodb.Table(table_name)
        key_condition = Key('site_id').eq(site_id)
        
        if start_time and end_time:
            key_condition = key_condition & Key('timestamp').between(start_time, end_time)
        elif start_time:
            key_condition = key_condition & Key('timestamp').gte(start_time)
        elif end_time:
            key_condition = key_condition & Key('timestamp').lte(end_time)
        
        response = table.query(
            KeyConditionExpression=key_condition,
            Limit=limit,
            ScanIndexForward=False
        )
        
        return {
            "site_id": site_id,
            "record_count": len(response['Items']),
            "data": response['Items']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/sites/{site_id}/anomalies")
async def get_site_anomalies(site_id: str, limit: int = Query(50)):
    try:
        table = dynamodb.Table(table_name)
        
        response = table.query(
            KeyConditionExpression=Key('site_id').eq(site_id),
            FilterExpression='anomaly = :anomaly_value',
            ExpressionAttributeValues={':anomaly_value': True},
            Limit=limit,
            ScanIndexForward=False
        )
        
        return {
            "site_id": site_id,
            "anomaly_count": len(response['Items']),
            "anomalies": response['Items']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/sites")
async def get_all_sites():
    try:
        table = dynamodb.Table(table_name)
        response = table.scan(ProjectionExpression='site_id')
        sites = list(set([item['site_id'] for item in response['Items']]))
        
        return {"sites": sorted(sites), "site_count": len(sites)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/analytics/summary")
async def get_analytics_summary():
    try:
        table = dynamodb.Table(table_name)
        response = table.scan()
        items = response['Items']
        
        total_records = len(items)
        total_anomalies = sum(1 for item in items if item.get('anomaly', False))
        
        site_stats = {}
        for item in items:
            site_id = item['site_id']
            if site_id not in site_stats:
                site_stats[site_id] = {'records': 0, 'anomalies': 0, 'total_generated': 0, 'total_consumed': 0}
            
            site_stats[site_id]['records'] += 1
            if item.get('anomaly', False):
                site_stats[site_id]['anomalies'] += 1
            
            site_stats[site_id]['total_generated'] += item.get('energy_generated_kwh', 0)
            site_stats[site_id]['total_consumed'] += item.get('energy_consumed_kwh', 0)
        
        return {
            "total_records": total_records,
            "total_anomalies": total_anomalies,
            "anomaly_rate": (total_anomalies / total_records * 100) if total_records > 0 else 0,
            "site_count": len(site_stats),
            "site_statistics": site_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)