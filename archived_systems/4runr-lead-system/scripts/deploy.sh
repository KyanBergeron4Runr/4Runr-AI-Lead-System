#!/bin/bash
# Script to deploy the 4Runr Lead System to an EC2 instance
# Run this script from your local machine

# Exit on error
set -e

# Configuration
EC2_USER="ubuntu"
EC2_HOST="your-ec2-instance-hostname"
EC2_KEY="path/to/your-key.pem"
REMOTE_DIR="/home/ubuntu/4runr-lead-system"

# Check if EC2 host is provided
if [ "$1" != "" ]; then
  EC2_HOST=$1
fi

# Check if EC2 key is provided
if [ "$2" != "" ]; then
  EC2_KEY=$2
fi

echo "Deploying to $EC2_USER@$EC2_HOST using key $EC2_KEY"

# Create a temporary directory for the build
TMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TMP_DIR"

# Copy necessary files to the temporary directory
cp -r ./airtable $TMP_DIR/
cp -r ./config $TMP_DIR/
cp -r ./scraper $TMP_DIR/
cp -r ./utils $TMP_DIR/
cp -r ./scripts $TMP_DIR/
cp ./package.json $TMP_DIR/
cp ./package-lock.json $TMP_DIR/
cp ./Dockerfile $TMP_DIR/
cp ./docker-compose.yml $TMP_DIR/
cp ./docker-entrypoint.sh $TMP_DIR/
cp ./.dockerignore $TMP_DIR/
cp ./README.md $TMP_DIR/
cp ./.env.example $TMP_DIR/

# Create a tarball of the application
TAR_FILE="4runr-lead-system.tar.gz"
tar -czf $TAR_FILE -C $TMP_DIR .
echo "Created tarball: $TAR_FILE"

# Copy the tarball to the EC2 instance
scp -i $EC2_KEY $TAR_FILE $EC2_USER@$EC2_HOST:~
echo "Copied tarball to EC2 instance"

# Extract the tarball on the EC2 instance
ssh -i $EC2_KEY $EC2_USER@$EC2_HOST "mkdir -p $REMOTE_DIR && tar -xzf ~/$TAR_FILE -C $REMOTE_DIR"
echo "Extracted tarball on EC2 instance"

# Build and run the Docker container on the EC2 instance
ssh -i $EC2_KEY $EC2_USER@$EC2_HOST "cd $REMOTE_DIR && docker build -t 4runr-lead-system:prod ."
echo "Built Docker image on EC2 instance"

# Clean up
rm -rf $TMP_DIR
rm $TAR_FILE
ssh -i $EC2_KEY $EC2_USER@$EC2_HOST "rm ~/$TAR_FILE"
echo "Cleaned up temporary files"

echo "Deployment completed successfully!"
echo "Next steps:"
echo "1. SSH into the EC2 instance: ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
echo "2. Create a .env file: cp $REMOTE_DIR/.env.example $REMOTE_DIR/.env"
echo "3. Edit the .env file with your Airtable credentials: nano $REMOTE_DIR/.env"
echo "4. Run the application: cd $REMOTE_DIR && docker run --env-file .env 4runr-lead-system:prod"