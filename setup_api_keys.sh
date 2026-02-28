#!/bin/bash
# Setup script for API keys

echo "🔑 API Key Setup for Enhanced Video Generation"
echo "=============================================="
echo ""

echo "Current API key status:"
echo "📺 Pexels API Key: ${PEXELS_API_KEY:+✅ Set}${PEXELS_API_KEY:-❌ Not set}"
echo "📺 Pixabay API Key: ${PIXABAY_API_KEY:+✅ Set}${PIXABAY_API_KEY:-❌ Not set}"
echo "🤖 Claude API Key: ${ANTHROPIC_API_KEY:+✅ Set}${ANTHROPIC_API_KEY:-❌ Not set}"
echo ""

if [[ -z "$PEXELS_API_KEY" ]]; then
    echo "❌ No Pexels API key detected!"
    echo ""
    echo "To get real video footage instead of static colors:"
    echo "1. Go to: https://www.pexels.com/api/"
    echo "2. Create free account and get API key"
    echo "3. Run: export PEXELS_API_KEY=\"your-key-here\""
    echo ""
fi

if [[ -z "$PIXABAY_API_KEY" ]]; then
    echo "💡 Optional: Get Pixabay API key for more video sources"
    echo "1. Go to: https://pixabay.com/api/docs/"
    echo "2. Create account and get API key"
    echo "3. Run: export PIXABAY_API_KEY=\"your-key-here\""
    echo ""
fi

if [[ -z "$ANTHROPIC_API_KEY" ]]; then
    echo "❌ No Claude API key detected!"
    echo "Run: export ANTHROPIC_API_KEY=\"sk-ant-...\""
    echo ""
fi

echo "After setting keys, test with:"
echo "python pipeline_enhanced.py --topic \"ocean waves\" --state calm"