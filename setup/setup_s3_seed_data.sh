#!/usr/bin/env bash
#
# Create the S3 bucket for workshop seed data and upload CSVs.
#
# Usage:
#   ./setup_s3_seed_data.sh                    # defaults to us-east-1
#   ./setup_s3_seed_data.sh --region us-west-2
#   ./setup_s3_seed_data.sh --cleanup          # delete bucket and contents

set -euo pipefail

BUCKET_NAME="neo4j-aws-workshop-data"
S3_PREFIX="sec-filings"
REGION="us-east-1"
CLEANUP=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED_DATA_DIR="${SCRIPT_DIR}/seed-data"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--region REGION] [--cleanup]"
            exit 1
            ;;
    esac
done

# ── Cleanup mode ──────────────────────────────────────────────────────────────

if [ "$CLEANUP" = true ]; then
    echo "Deleting all objects in s3://${BUCKET_NAME}/${S3_PREFIX}/ ..."
    aws s3 rm "s3://${BUCKET_NAME}/${S3_PREFIX}/" --recursive --region "$REGION" 2>/dev/null || true

    echo "Deleting bucket s3://${BUCKET_NAME} ..."
    aws s3 rb "s3://${BUCKET_NAME}" --region "$REGION" 2>/dev/null || true

    echo "Cleanup complete."
    exit 0
fi

# ── Create bucket ─────────────────────────────────────────────────────────────

echo "Creating S3 bucket: ${BUCKET_NAME} (region: ${REGION}) ..."

if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
    echo "  Bucket already exists."
else
    if [ "$REGION" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION"
    else
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
    echo "  Bucket created."
fi

# ── Set public read policy ────────────────────────────────────────────────────

echo "Disabling Block Public Access ..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
        "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

echo "Applying public-read bucket policy ..."
POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadCSV",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/${S3_PREFIX}/*"
        }
    ]
}
EOF
)
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy "$POLICY"

# ── Upload CSVs ───────────────────────────────────────────────────────────────

echo "Uploading CSVs from ${SEED_DATA_DIR}/ to s3://${BUCKET_NAME}/${S3_PREFIX}/ ..."

csv_count=0
for csv_file in "${SEED_DATA_DIR}"/*.csv; do
    [ -f "$csv_file" ] || continue
    filename="$(basename "$csv_file")"
    aws s3 cp "$csv_file" "s3://${BUCKET_NAME}/${S3_PREFIX}/${filename}" \
        --region "$REGION" \
        --content-type "text/csv" \
        --quiet
    echo "  ${filename}"
    csv_count=$((csv_count + 1))
done

echo ""
echo "Done. Uploaded ${csv_count} CSV files."
echo "Base URL: https://${BUCKET_NAME}.s3.amazonaws.com/${S3_PREFIX}/"
