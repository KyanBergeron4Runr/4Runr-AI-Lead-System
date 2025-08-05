# AWS EC2 Deployment Guide for 4Runr Lead System

This guide provides step-by-step instructions for deploying the 4Runr Lead System to an AWS EC2 instance running Ubuntu 22.04 LTS.

## Prerequisites

1. An AWS account with permissions to create and manage EC2 instances
2. Basic knowledge of AWS EC2 and SSH
3. The 4Runr Lead System codebase on your local machine

## Step 1: Launch an EC2 Instance

1. Log in to the AWS Management Console
2. Navigate to EC2 and click "Launch Instance"
3. Choose "Ubuntu Server 22.04 LTS" as the Amazon Machine Image (AMI)
4. Select an instance type (t2.micro is sufficient for testing)
5. Configure instance details as needed
6. Add storage (8GB is sufficient for the application)
7. Add tags for better organization (e.g., Name: 4runr-lead-system)
8. Configure security group to allow:
   - SSH (port 22) from your IP address
9. Review and launch the instance
10. Create or select an existing key pair for SSH access
11. Launch the instance

## Step 2: Set Up the EC2 Instance

1. Connect to your EC2 instance via SSH:
   ```bash
   ssh -i path/to/your-key.pem ubuntu@your-ec2-public-dns
   ```

2. Copy the setup script to the EC2 instance:
   ```bash
   scp -i path/to/your-key.pem scripts/setup-ec2.sh ubuntu@your-ec2-public-dns:~
   ```

3. Run the setup script on the EC2 instance:
   ```bash
   ssh -i path/to/your-key.pem ubuntu@your-ec2-public-dns "chmod +x ~/setup-ec2.sh && ~/setup-ec2.sh"
   ```

4. Log out and log back in for the Docker group changes to take effect:
   ```bash
   exit
   ssh -i path/to/your-key.pem ubuntu@your-ec2-public-dns
   ```

## Step 3: Deploy the Application

1. From your local machine, run the deployment script:
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh your-ec2-public-dns path/to/your-key.pem
   ```

2. SSH into the EC2 instance:
   ```bash
   ssh -i path/to/your-key.pem ubuntu@your-ec2-public-dns
   ```

3. Create and configure the .env file:
   ```bash
   cd ~/4runr-lead-system
   cp .env.example .env
   nano .env  # Edit with your Airtable credentials
   ```

4. Test the application:
   ```bash
   docker run --env-file .env 4runr-lead-system:prod
   ```

## Step 4: Set Up Cron Jobs for Scheduled Execution

1. Create a script to run the Docker container:
   ```bash
   cat > ~/run-scraper.sh << 'EOF'
   #!/bin/bash
   cd ~/4runr-lead-system
   docker run --rm --env-file .env 4runr-lead-system:prod >> ~/logs/scraper.log 2>&1
   EOF
   
   chmod +x ~/run-scraper.sh
   ```

2. Edit the crontab to schedule the script:
   ```bash
   crontab -e
   ```

3. Add a cron job to run the scraper daily at 9 AM:
   ```
   0 9 * * * ~/run-scraper.sh
   ```

4. Save and exit the editor

## Step 5: Monitor and Maintain

1. Check the logs:
   ```bash
   tail -f ~/logs/scraper.log
   ```

2. Update the application:
   ```bash
   # Re-run the deployment script from your local machine
   ./scripts/deploy.sh your-ec2-public-dns path/to/your-key.pem
   ```

3. Restart the Docker container:
   ```bash
   docker stop $(docker ps -q --filter ancestor=4runr-lead-system:prod)
   docker run -d --env-file .env 4runr-lead-system:prod
   ```

## Troubleshooting

1. If the Docker container fails to start, check the logs:
   ```bash
   docker logs $(docker ps -a -q --filter ancestor=4runr-lead-system:prod --format="{{.ID}}")
   ```

2. If the cron job is not running, check the cron logs:
   ```bash
   grep CRON /var/log/syslog
   ```

3. If the application is not connecting to Airtable, verify the .env file:
   ```bash
   cat ~/4runr-lead-system/.env
   ```

## Security Considerations

1. Keep your EC2 instance updated:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

2. Regularly rotate your Airtable API key
3. Restrict SSH access to trusted IP addresses in the security group
4. Consider using AWS Secrets Manager for storing sensitive credentials