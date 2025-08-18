#!/bin/bash

# Deploy Enhanced Enrichment to EC2
# This script updates the 4Runr system with comprehensive field population

echo "🚀 Deploying Enhanced Enrichment to EC2..."
echo "=============================================="

# 1. Copy updated enrichment files
echo "📂 Copying enhanced enrichment files..."

# Enhanced enricher integration
cp 4runr-lead-scraper/enricher/enhanced_enricher_integration.py real_4runr_deployment/4runr-lead-scraper/enricher/
cp 4runr-lead-scraper/enricher/enhanced_enricher_integration.py deployment_package/4runr-lead-scraper/enricher/

# Enhanced business trait extractor
cp 4runr-lead-scraper/enricher/business_trait_extractor.py real_4runr_deployment/4runr-lead-scraper/enricher/
cp 4runr-lead-scraper/enricher/business_trait_extractor.py deployment_package/4runr-lead-scraper/enricher/

# Enhanced email enricher
cp 4runr-lead-scraper/enricher/email_enricher.py real_4runr_deployment/4runr-lead-scraper/enricher/
cp 4runr-lead-scraper/enricher/email_enricher.py deployment_package/4runr-lead-scraper/enricher/

# Enhanced engagement defaults
cp 4runr-lead-scraper/sync/engagement_defaults.py real_4runr_deployment/4runr-lead-scraper/sync/
cp 4runr-lead-scraper/sync/engagement_defaults.py deployment_package/4runr-lead-scraper/sync/

# Enhanced autonomous organism (already done above)

echo "✅ Files copied successfully"

# 2. Test the enhanced system locally first
echo ""
echo "🧪 Testing enhanced enrichment locally..."

# Run a quick test
python -c "
import sys
sys.path.append('real_4runr_deployment')
try:
    from real_autonomous_organism import RealAutonomousOrganism
    organism = RealAutonomousOrganism()
    print('✅ Enhanced organism initialized successfully')
    
    # Test comprehensive enrichment
    test_lead = {
        'name': 'John Doe',
        'company': 'Test Tech Corp',
        'title': 'CEO'
    }
    
    enhanced_data = organism._apply_comprehensive_enrichment(test_lead)
    print(f'✅ Comprehensive enrichment test passed - {len(enhanced_data)} fields populated')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Local testing passed"
else
    echo "❌ Local testing failed - aborting deployment"
    exit 1
fi

# 3. Create deployment package
echo ""
echo "📦 Creating deployment package..."

# Create a clean deployment directory
rm -rf enhanced_deployment_package
mkdir enhanced_deployment_package

# Copy the real deployment files
cp -r real_4runr_deployment/* enhanced_deployment_package/

# Add the field enrichment script
cp run_field_enrichment.py enhanced_deployment_package/

echo "✅ Deployment package created"

# 4. Generate deployment instructions
echo ""
echo "📋 Generating deployment instructions..."

cat > enhanced_deployment_package/DEPLOY_ENHANCED_ENRICHMENT.md << 'EOF'
# Enhanced Enrichment Deployment Instructions

## What's New
- ✅ Comprehensive field population during enrichment
- ✅ Automatic LinkedIn URL generation
- ✅ Industry, location, company size inference
- ✅ Business traits and pain points extraction
- ✅ Website URL generation from company names
- ✅ Enhanced email metadata and confidence scoring
- ✅ Engagement readiness flags

## Deployment Steps

### 1. Backup Current System
```bash
# On EC2, backup current files
sudo systemctl stop 4runr-ai-system
cp -r /opt/4runr-system /opt/4runr-system-backup-$(date +%Y%m%d)
```

### 2. Deploy Enhanced Files
```bash
# Copy new files to EC2
scp -r enhanced_deployment_package/* ec2-user@your-ec2-ip:/opt/4runr-system/
```

### 3. Update Permissions
```bash
# On EC2
sudo chown -R ec2-user:ec2-user /opt/4runr-system/
chmod +x /opt/4runr-system/*.py
```

### 4. Test Enhanced System
```bash
# On EC2
cd /opt/4runr-system
python run_field_enrichment.py
```

### 5. Restart System
```bash
# On EC2
sudo systemctl start 4runr-ai-system
sudo systemctl status 4runr-ai-system
```

### 6. Monitor Logs
```bash
# On EC2
sudo journalctl -u 4runr-ai-system -f
```

## Expected Results
- All new leads will automatically have comprehensive field population
- Existing leads can be enriched by running `run_field_enrichment.py`
- Empty fields like LinkedIn URLs, location, industry will be automatically filled
- Better lead quality scoring and engagement readiness

## Rollback Plan
If issues occur:
```bash
sudo systemctl stop 4runr-ai-system
cp -r /opt/4runr-system-backup-[DATE]/* /opt/4runr-system/
sudo systemctl start 4runr-ai-system
```
EOF

echo "✅ Deployment instructions created"

# 5. Final summary
echo ""
echo "🎉 Enhanced Enrichment Deployment Package Ready!"
echo "=============================================="
echo "📂 Package location: enhanced_deployment_package/"
echo "📋 Instructions: enhanced_deployment_package/DEPLOY_ENHANCED_ENRICHMENT.md"
echo ""
echo "🚀 Next Steps:"
echo "1. Review the deployment package"
echo "2. Upload to EC2 using the instructions"
echo "3. Test the enhanced enrichment"
echo "4. Monitor autonomous cycles for comprehensive field population"
echo ""
echo "✨ Your leads will now automatically have ALL fields populated!"
