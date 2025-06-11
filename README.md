# Renewable Energy Data Pipeline

Real-time data engineering pipeline for processing renewable energy data using AWS services. The system simulates energy generation and consumption data from multiple sites, processes it automatically, detects anomalies, and provides REST APIs and a web dashboard for analytics.

## What this pipeline Does

This pipeline continuously generates renewable energy data from 5 sites, uploads it to S3 every 5 minutes, processes it with Lambda to detect anomalies, stores results in DynamoDB, and provides APIs and a dashboard to view the data. Anomalies are detected when energy values are negative or extremely high.

## Prerequisites

Need an AWS account with permissions for S3, DynamoDB, Lambda, IAM, and CloudWatch.

### Before setup in your command prompt or gitbash

Download and install AWS CLI from https://aws.amazon.com/cli/ 

Download & install Terraform from https://www.terraform.io/downloads 

download and install python 3.9+ from https://www.python.org/downloads/ 

download and install Git from https://git-scm.com/downloads

**Imp :** You need an AWS account with permissions for S3, DynamoDB, Lambda, IAM, and CloudWatch.

## AWS Configuration

Open command prompt/terminal Run: 
```
aws configure
```

Enter your AWS Access Key ID when prompted 

enter your AWS Secret Access Key when prompted 
 
Enter: us-east-1 for region 
 
Enter: json for output format 
 
Test with: 
```
aws sts get-caller-identity
```

## Project Setup

Clone the repository: 
```
git clone [your-repository-url]
```
Navigate to project: 
```
cd renewable-energy-pipeline
```

For Windows users, run the automated deployment:
```
cd scripts
deploy.bat
```

For manual deployment, package the Lambda function first:
```
cd lambda
pip install -r requirements.txt -t .
zip -r ../infrastructure/lambda_function.zip .
cd ../infrastructure
```

### Deploy infrastructure with Terraform
```
terraform init
terraform apply -auto-approve
```

Get the S3 bucket name from Terraform output:
```
terraform output s3_bucket_name
```

Update the bucket name in `data_generator/simulate_data.py` by replacing the BUCKET_NAME variable with your actual bucket name.

### Start the data generator:
```
cd data_generator
pip install -r requirements.txt
python simulate_data.py
```

Launch the API server:
```
cd api
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Start the dashboard:
```
cd visualization
pip install -r requirements.txt
streamlit run dashboard.py
```

## GitHub Setup

After everything worked locally

```
git add .
git commit -m " AWS Energy Data Analytics Pipeline"
git remote add origin https://github.com/lahari3037/energy-data-analytics.git
```

### Create GitHub Personal Access Token
We can go to Settings → Developer settings → Personal access tokens → Generate

Push code
```
git push -u origin master
```
Username: "Username"

Password: token that you pasted

### CI/CD Pipeline Setup

Created .github/workflows/deploy.yml:

Added secrets in GitHub:
• Repository Settings → Secrets → Actions
• Added AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

## How to use the system

The API runs on localhost:8000 and provides several endpoints. 

Get data for a specific site with 
```
curl "http://localhost:8000/sites/SITE_001/data?limit=10"
```

get anomalies with 
```
curl "http://localhost:8000/sites/SITE_001/anomalies"
```

get all sites with 
```
curl "http://localhost:8000/sites"
```

get analytics summary with 
```
curl "http://localhost:8000/analytics/summary"
```

The dashboard runs on localhost:8501 and shows real-time metrics, charts comparing energy generation vs consumption, anomaly tracking, and trend analysis. You can filter by site and date range.

## Project Structure

The infrastructure directory contains Terraform files that define AWS resources. The lambda directory has the data processing function that triggers on S3 uploads. The data_generator directory contains the simulation script that creates and uploads energy data. The api directory has the FastAPI application for REST endpoints. The visualization directory contains the Streamlit dashboard. The scripts directory has deployment and cleanup utilities.

## Configuration

You can customize the deployment by modifying variables in infrastructure/variables.tf or creating a terraform.tfvars file with your preferred aws_region and project_name settings. The default region is us-east-1 and project name is energy-data-analytics.

## Monitoring and Debugging

Check if data is being uploaded to S3:
```
aws s3 ls s3://your-bucket-name --recursive
```

Verify data in DynamoDB:
```
aws dynamodb scan --table-name energy-data-analytics-energy-data --limit 5
```

View Lambda function logs:
```
aws logs tail /aws/lambda/energy-data-analytics-data-processor --follow
```

Test Lambda function:
```
aws lambda invoke --function-name energy-data-analytics-data-processor output.json
```

Check API health:
```
curl http://localhost:8000/health
```

## Problems

If you get AWS credential errors, run aws configure again or set environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_DEFAULT_REGION.

In any of the case if Terraform shows state lock errors, use terraform force-unlock LOCK_ID with the ID from the error message

if Lambda isn't processing files,check CloudWatch logs,verify S3 bucket notifications are configured, & ensure Lambda has proper IAM permissions.

If the dashboard shows no data, verify the DynamoDB table name in dashboard.py matches your actual table, check AWS credentials, and make sure the data pipeline is running.

If you get any of DynamoDB permission errors, then the Lambda IAM role needs DynamoDB permissions. Check the role policy in your Terraform configuration

This project uses AWS Free Tier resources 

## Cleanup

run cleanup.bat in the scripts directory. 

Verify cleanup by checking that resources are gone with 
```
aws s3 ls
aws dynamodb list-tables
aws lambda list-functions
```
