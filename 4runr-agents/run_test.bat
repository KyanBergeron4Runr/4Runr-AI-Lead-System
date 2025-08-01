@echo off
echo Running 4Runr lead generation pipeline test...

echo Step 1: Checking Docker containers...
docker ps | findstr "4runr-scraper 4runr-enricher 4runr-engager 4runr-pipeline 4runr-cron"

echo Step 2: Running the pipeline...
docker-compose exec 4runr-pipeline python run_pipeline.py

echo Step 3: Observing logs in real-time...
docker-compose logs -f