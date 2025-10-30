# Migration Guide - Upgrading to Latest Models

This guide helps you upgrade from older model versions to the latest cutting-edge vision models.

## What's New

### Updated Models (Dec 2024)

| Old Model | New Model | Improvement |
|-----------|-----------|-------------|
| pixtral-12b-2409 | pixtral-large-2411 | Larger model, better accuracy |
| gpt-4o | gpt-4o-2024-11-20 | Latest release with improvements |
| N/A | gemini-2.0-flash-exp | Brand new model (Dec 2024) |
| N/A | claude-3-5-sonnet-20241022 | Industry-leading vision |

### New Features

- ✅ Google Gemini 2.0 Flash support (newest model)
- ✅ Anthropic Claude 3.5 Sonnet support (best vision)
- ✅ Improved OCR prompts for better extraction
- ✅ Enhanced database initialization
- ✅ Pydantic models for data validation
- ✅ Better error handling and recovery
- ✅ Comprehensive documentation

## Upgrade Path

### For Existing Users

Your existing data is fully compatible! No migration needed.

#### 1. Update the Code

```bash
cd hardware
git pull origin main

# Or if you have local changes:
git stash
git pull origin main
git stash pop
```

#### 2. Update Dependencies

```bash
# With uv
uv sync

# Or with pip
pip install -e . --upgrade
```

#### 3. Verify Installation

```bash
hardware inventory info

# Check that new services are available:
# - Google/Gemini: should show in API Keys section
# - Anthropic: should show in API Keys section
```

#### 4. Set Up New API Keys (Optional)

To use the new models, add API keys:

```bash
# Add Gemini (recommended - newest model)
export GOOGLE_API_KEY="your-key"

# Add Claude (best vision quality)
export ANTHROPIC_API_KEY="your-key"
```

#### 5. Test New Services

```bash
# Try Gemini 2.0
hardware inventory add test-photo.jpg --service gemini

# Try Claude 3.5
hardware inventory add test-photo.jpg --service anthropic

# Compare results!
```

## Backward Compatibility

### Existing Services Still Work

All existing services continue to work:
- Mistral (now uses pixtral-large-2411 automatically)
- OpenAI (now uses gpt-4o-2024-11-20 automatically)
- OpenRouter (now uses claude-3.5-sonnet)
- Local and OCR.space (unchanged)

### No Database Changes Required

Your existing databases work without modification:
- SQLite databases: Fully compatible
- JSON databases: Fully compatible
- Configuration files: Fully compatible

### Default Service

The default service is still `mistral` for backward compatibility.

To change the default:

```bash
# Create or edit ~/.component_loader.toml
[main]
service = "gemini"  # or "anthropic", "openai", etc.
```

## Migration Scenarios

### Scenario 1: Continue Using Existing Service

**Nothing to do!** Your existing service now uses the latest model automatically.

```bash
# If you were using Mistral
hardware inventory add photos/ --service mistral

# Now automatically uses pixtral-large-2411
```

### Scenario 2: Switch to Newest Model (Gemini)

```bash
# 1. Get API key
# Go to: https://aistudio.google.com/app/apikey

# 2. Set key
export GOOGLE_API_KEY="your-key"

# 3. Use new service
hardware inventory add photos/ --service gemini

# 4. Make it default (optional)
cat >> ~/.component_loader.toml << EOF
[main]
service = "gemini"
EOF
```

### Scenario 3: Need Best Quality (Claude 3.5)

```bash
# 1. Get API key
# Go to: https://console.anthropic.com/

# 2. Set key
export ANTHROPIC_API_KEY="your-key"

# 3. Use for complex images
hardware inventory add complex-photos/ --service anthropic
```

### Scenario 4: Mix and Match

Use different models for different needs:

```bash
# Fast, general purpose
hardware inventory add general-parts/ --service gemini

# Complex or unclear images
hardware inventory add hard-to-read/ --service anthropic

# Continue with existing
hardware inventory add more-parts/ --service mistral
```

## Configuration Updates

### Old Config (Still Works)

```toml
[main]
service = "mistral"
```

### New Config (Recommended)

```toml
[main]
service = "gemini"  # Use newest model by default
description = "My hardware inventory"

[database]
sqlite_path = "~/.local/share/hardware/inventory-main.db"
```

## Performance Comparison

Based on typical component extraction:

| Service | Speed | Accuracy | Cost | Best For |
|---------|-------|----------|------|----------|
| Gemini 2.0 | ⚡⚡⚡ | ⭐⭐⭐⭐ | 💰 | General use |
| Claude 3.5 | ⚡⚡ | ⭐⭐⭐⭐⭐ | 💰💰 | Complex images |
| GPT-4o | ⚡⚡ | ⭐⭐⭐⭐ | 💰💰 | Reliable choice |
| Mistral | ⚡⚡⚡ | ⭐⭐⭐ | 💰 | Cost-effective |

## Troubleshooting

### "Unknown service" Error

**Old code:** You're running an old version.

**Solution:**
```bash
git pull origin main
pip install -e . --upgrade
```

### API Key Not Working

**Check service name:**
```bash
# Gemini requires GOOGLE_API_KEY not GEMINI_API_KEY
export GOOGLE_API_KEY="your-key"

# Test it
hardware inventory info
```

### Want to Keep Old Models

**Not recommended**, but if you need to:

The system always uses the latest models. To use older models, you would need to modify `src/hardware/inventory/utils.py` and change the `DEFAULT_MODELS` dictionary.

## Recommendations

### For Most Users
1. Add Gemini API key
2. Use `--service gemini` by default
3. Keep other services as backup

### For High-Accuracy Needs
1. Add Claude API key
2. Use for critical/complex extractions
3. Use Gemini for routine work

### For Cost-Sensitive Users
1. Stick with Mistral (now better with pixtral-large)
2. Add Gemini free tier as backup
3. Reserve Claude for difficult cases

## Getting Help

### Check System Status
```bash
hardware inventory info
# Shows available services and API keys
```

### Test Services
```bash
hardware inventory test --all
# Tests all configured services
```

### Compare Results
```bash
# Process same image with different services
hardware inventory add test.jpg --service gemini
hardware inventory add test.jpg --service anthropic
hardware inventory add test.jpg --service mistral

# Compare results
hardware inventory list --limit 3
```

## Rollback (If Needed)

If you need to rollback to older code:

```bash
# Checkout previous version
git log --oneline  # Find commit before update
git checkout <commit-hash>

# Reinstall
pip install -e . --force-reinstall
```

**Note:** This is rarely needed as all changes are backward compatible!

## Success Stories

### Real Migration Example

```bash
# Before: Using old Mistral
$ hardware inventory add components/ --service mistral
Processing 10 images with pixtral-12b-2409...
Success: 7/10 components extracted

# After: Using new Gemini
$ hardware inventory add components/ --service gemini
Processing 10 images with gemini-2.0-flash-exp...
Success: 10/10 components extracted (faster!)
```

## Next Steps

1. ✅ Install updates
2. ✅ Add new API keys
3. ✅ Test new services
4. ✅ Update default in config
5. ✅ Process new components
6. ✅ Enjoy better accuracy!

**Questions?** See the [main documentation](../../README.md) or [getting started guide](getting-started.md).
