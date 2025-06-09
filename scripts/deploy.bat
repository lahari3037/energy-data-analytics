@echo off
echo Starting Renewable Energy Pipeline Deployment
echo =============================================

set PROJECT_NAME=energy-data-analytics
set AWS_REGION=us-east-1

echo Checking AWS CLI configuration...
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo AWS CLI not configured. Run 'aws configure' first.
    pause
    exit /b 1
)

echo Checking Terraform installation...
terraform version >nul 2>&1
if %errorlevel% neq 0 (
    echo Terraform not found. Please install Terraform first.
    pause
    exit /b 1
)

cd /d "%~dp0.."

echo Packaging Lambda function...
cd lambda
pip install -r requirements.txt -t .
powershell Compress-Archive -Path * -DestinationPath ../infrastructure/lambda_function.zip -Force
cd ..

echo Deploying infrastructure with Terraform...
cd infrastructure

terraform init
terraform plan -var="project_name=%PROJECT_NAME%" -var="aws_region=%AWS_REGION%"
terraform apply -var="project_name=%PROJECT_NAME%" -var="aws_region=%AWS_REGION%" -auto-approve

for /f "tokens=*" %%i in ('terraform output -raw s3_bucket_name') do set BUCKET_NAME=%%i
for /f "tokens=*" %%i in ('terraform output -raw dynamodb_table_name') do set TABLE_NAME=%%i
for /f "tokens=*" %%i in ('terraform output -raw lambda_function_name') do set LAMBDA_NAME=%%i

echo Infrastructure deployed successfully!
echo S3 Bucket: %BUCKET_NAME%
echo DynamoDB Table: %TABLE_NAME%
echo Lambda Function: %LAMBDA_NAME%

cd ..

echo Updating configuration files...
powershell -Command "(gc data_generator/simulate_data.py) -replace 'your-bucket-name-here', '%BUCKET_NAME%' | Out-File -encoding UTF8