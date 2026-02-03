#!/bin/bash
set -e

echo "🔧 Setting up AgentPulse development environment..."

# Install Python SDK
echo "📦 Installing Python SDK..."
pip install -e ./packages/sdk-python

# Install collector dependencies
echo "📦 Installing collector dependencies..."
cd packages/collector
bun install
cd ../..

# Install dashboard dependencies
echo "📦 Installing dashboard dependencies..."
cd packages/dashboard
bun install
cd ../..

echo "✅ Setup complete!"
