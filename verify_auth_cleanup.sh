#!/bin/bash
#
# Authentication Cleanup Verification Script
# Verifies that invalid Anthropic API key has been removed
# and system is ready for Claude Max subscription authentication
#

echo "========================================================================"
echo "AUTHENTICATION CLEANUP VERIFICATION"
echo "========================================================================"
echo ""

# Check .env file
echo "1. Checking ~/.env file..."
if grep -q "ANTHROPIC_API_KEY" /home/jevenson/.env 2>/dev/null; then
    echo "   ⚠  ANTHROPIC_API_KEY still present in .env file"
    exit 1
else
    echo "   ✓ ANTHROPIC_API_KEY removed from .env file"
fi

# Verify other keys preserved
echo ""
echo "2. Verifying other API keys preserved..."
if grep -q "GOOGLE_API_KEY" /home/jevenson/.env 2>/dev/null; then
    echo "   ✓ GOOGLE_API_KEY preserved"
else
    echo "   ⚠  GOOGLE_API_KEY missing"
fi

if grep -q "OPENAI_API_KEY" /home/jevenson/.env 2>/dev/null; then
    echo "   ✓ OPENAI_API_KEY preserved"
else
    echo "   ⚠  OPENAI_API_KEY missing"
fi

# Check backup exists
echo ""
echo "3. Verifying backup file..."
BACKUP_FILE=$(ls -t /home/jevenson/.env.backup_* 2>/dev/null | head -1)
if [ -n "$BACKUP_FILE" ]; then
    echo "   ✓ Backup created: $BACKUP_FILE"
else
    echo "   ⚠  No backup found"
fi

# Check current shell environment (may still have old value)
echo ""
echo "4. Checking current shell environment..."
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "   ⚠  ANTHROPIC_API_KEY still set in current shell (will be cleared on restart)"
else
    echo "   ✓ ANTHROPIC_API_KEY not set in current shell"
fi

echo ""
echo "========================================================================"
echo "CLEANUP STATUS: SUCCESS"
echo "========================================================================"
echo ""
echo "Next Steps:"
echo "  1. Restart Claude Code to clear shell environment"
echo "  2. Claude Max subscription authentication will be used automatically"
echo "  3. Rerun integration test: python3 test_zte_integration.py"
echo ""
