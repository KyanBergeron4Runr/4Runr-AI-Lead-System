# Knowledge Base Testing Guide

## Overview
This guide explains how to test and validate the 4Runr knowledge base to ensure it's properly configured for the engager agent.

## Test Scripts Available

### 1. Quick Fix Verification
**File**: `verify_knowledge_base_fix.py`
**Purpose**: Quick check to verify the knowledge base fix is working
**Usage**: 
```bash
python verify_knowledge_base_fix.py
```
**Expected Output**: 
```
✅ PASS: Knowledge base validation successful
✅ All required sections present
✅ Content length: 7006 characters (good)
🎉 KNOWLEDGE BASE FIX VERIFIED!
```

### 2. Comprehensive Validation Test
**File**: `test_knowledge_base_validation.py`
**Purpose**: Thorough testing of all knowledge base functionality
**Usage**:
```bash
python test_knowledge_base_validation.py
```
**Tests Performed**:
- File existence check
- Content loading verification
- Section validation (all 6 required sections)
- Content quality assessment
- UTF-8 encoding verification
- Caching mechanism test
- Error handling test
- Integration test with knowledge summary

### 3. Engager Agent Test
**Purpose**: Test the actual engager agent with the knowledge base
**Usage**:
```bash
python -m engager.enhanced_engager_agent --dry-run --limit 1
```
**Expected Success Message**:
```
✅ 4Runr knowledge base loaded successfully
```

## Required Sections
The knowledge base must contain these exact sections (case-insensitive):

1. ✅ **4Runr Knowledge Base** - Main title
2. ✅ **Core Philosophy** - 4Runr's foundational beliefs
3. ✅ **Systems Thinking** - Systems approach methodology
4. ✅ **Infrastructure-First** - Infrastructure-first mindset
5. ✅ **AI-as-a-Layer** - AI integration philosophy
6. ✅ **Business Value** - Business value propositions

## Troubleshooting

### If Tests Fail

1. **Missing Sections Error**:
   - Check that all 6 required sections exist in `data/4runr_knowledge.md`
   - Verify section names match exactly (case-insensitive)

2. **File Not Found Error**:
   - Ensure `data/4runr_knowledge.md` exists
   - Check file path is correct relative to project root

3. **Content Too Short Error**:
   - Knowledge base should be >5000 characters
   - Ensure all content sections are properly filled

4. **UTF-8 Encoding Error**:
   - Save the file with UTF-8 encoding
   - Remove any special characters that might cause issues

### Success Indicators

When everything is working correctly, you should see:

1. ✅ All validation tests pass
2. ✅ Engager agent logs: "4Runr knowledge base loaded successfully"
3. ✅ No "missing sections" warnings in logs
4. ✅ System uses full knowledge base (not fallback content)

## File Locations

- **Knowledge Base**: `4runr-outreach-system/data/4runr_knowledge.md`
- **Loader Code**: `4runr-outreach-system/engager/knowledge_base_loader.py`
- **Test Scripts**: `4runr-outreach-system/test_knowledge_base_validation.py`
- **Quick Verify**: `4runr-outreach-system/verify_knowledge_base_fix.py`

## Integration with CI/CD

These tests can be integrated into automated testing pipelines:

```bash
# Quick validation (exit code 0 = success, 1 = failure)
python verify_knowledge_base_fix.py

# Comprehensive testing
python test_knowledge_base_validation.py

# Integration test with actual agent
python -m engager.enhanced_engager_agent --dry-run --limit 1
```

## Maintenance

When updating the knowledge base:

1. Run `python verify_knowledge_base_fix.py` after changes
2. Ensure all 6 required sections remain present
3. Test with the engager agent to verify integration
4. Check that content length remains substantial (>5000 chars)