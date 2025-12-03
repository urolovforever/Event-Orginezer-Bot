#!/bin/bash
# Script to clean cache and restart bot properly

echo "🧹 Cleaning Python bytecode cache..."
cd /home/nizomjon/PycharmProjects/university_event_bot

# Remove all .pyc files and __pycache__ directories
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

echo "✅ Cache cleaned"
echo ""
echo "📝 Checking line 623 in your local file..."
sed -n '623p' handlers/events.py

echo ""
echo "👆 If you see 'comment' (without 'event.get'), the file is not updated"
echo "   If you see 'event.get('comment'...)', the file is correct"
echo ""
echo "🔄 Now restart your bot:"
echo "   1. Stop the current bot process (Ctrl+C or kill)"
echo "   2. Run: python bot.py"
