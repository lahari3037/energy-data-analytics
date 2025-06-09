@echo off
echo Starting cleanup of AWS resources
echo =================================

cd /d "%~dp0.."
cd infrastructure

if not exist "terraform.tfstate" (
    echo No Terraform state found. Resources may not exist.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('terraform output -raw s3_bucket_name 2^>nul') do set BUCKET_NAME=%%i
for /f "tokens=*" %%i in ('terraform output -raw dynamodb_table_name 2^>nul') do set TABLE_NAME=%%i

echo Found resources to clean up:
echo S3 Bucket: %BUCKET_NAME%
echo DynamoDB Table: %TABLE_NAME%

if not "%BUCKET_NAME%"=="" (
    echo Emptying S3 bucket...
    aws s3 rm s3://%BUCKET_NAME% --recursive
)

echo Destroying infrastructure...
terraform destroy -auto-approve

echo Cleanup completed!
echo All AWS resources have been deleted to avoid charges.
pause