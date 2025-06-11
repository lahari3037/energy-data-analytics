terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  profile = "lahari"

}

resource "aws_s3_bucket" "energy_data_bucket" {
  bucket = "${var.project_name}-energy-data-${random_string.bucket_suffix.result}"
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.energy_data_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.data_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

resource "aws_dynamodb_table" "energy_data" {
  name           = "${var.project_name}-energy-data"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "site_id"
  range_key      = "timestamp"

  attribute {
    name = "site_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name = "EnergyDataTable"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.energy_data_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.energy_data.arn
      }
    ]
  })
}

resource "aws_lambda_function" "data_processor" {
  filename         = "lambda_function.zip"
  function_name    = "${var.project_name}-data-processor"
  role            = aws_iam_role.lambda_role.arn
  handler         = "data_processor.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs, 
  ]
}


resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.data_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.energy_data_bucket.arn
}

resource "aws_cloudwatch_log_metric_filter" "anomaly_filter" {
  name           = "anomaly-detected"
  log_group_name = aws_cloudwatch_log_group.lambda_logs.name
  pattern        = "ANOMALY_DETECTED"
  
  metric_transformation {
    name      = "AnomalyCount"
    namespace = "EnergyPipeline"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-data-processor"
  retention_in_days = 14
}

resource "aws_cloudwatch_metric_alarm" "anomaly_alarm" {
  alarm_name          = "energy-anomaly-detected"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "AnomalyCount"
  namespace           = "EnergyPipeline"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors energy anomalies"
  alarm_actions       = []
  
  treat_missing_data = "notBreaching"
}