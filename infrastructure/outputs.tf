output "s3_bucket_name" {
  value = aws_s3_bucket.energy_data_bucket.bucket
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.energy_data.name
}

output "lambda_function_name" {
  value = aws_lambda_function.data_processor.function_name
}