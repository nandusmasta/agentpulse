#!/bin/bash
set -e

echo "🚀 Starting AgentPulse services..."

# Start collector in background
cd packages/collector
nohup bun run src/index.ts > /tmp/collector.log 2>&1 &
COLLECTOR_PID=$!
echo "Collector started (PID: $COLLECTOR_PID)"

# Start dashboard in background
cd ../dashboard
nohup bun run dev --host > /tmp/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard started (PID: $DASHBOARD_PID)"

cd ../..

# Wait for services to be ready
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 AgentPulse is running!"
echo ""
echo "   📊 Dashboard: Click 'Open in Browser' on port 5173"
echo "   🔌 Collector: http://localhost:3000"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Try it out - run this in the terminal:"
echo ""
echo "  python examples/basic.py"
echo ""
echo "Then check the dashboard to see your trace!"
echo ""
