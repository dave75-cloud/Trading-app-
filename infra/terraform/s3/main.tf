resource "aws_s3_bucket" "data_lake" { bucket = "${var.project}-data" }
resource "aws_s3_bucket_public_access_block" "data_block" {
  bucket = aws_s3_bucket.data_lake.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}
output "s3_bucket" { value = aws_s3_bucket.data_lake.bucket }
