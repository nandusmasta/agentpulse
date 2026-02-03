#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "    _                    _   ____       _          "
echo "   / \   __ _  ___ _ __ | |_|  _ \ _   _| |___  ___ "
echo "  / _ \ / _\` |/ _ \ '_ \| __| |_) | | | | / __|/ _ \\"
echo " / ___ \ (_| |  __/ | | | |_|  __/| |_| | \__ \  __/"
echo "/_/   \_\__, |\___|_| |_|\__|_|    \__,_|_|___/\___|"
echo "        |___/                                       "
echo -e "${NC}"
echo "Lightweight observability for AI agents"
echo "========================================"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=mac;;
    MINGW*|CYGWIN*|MSYS*) PLATFORM=windows;;
    *)          PLATFORM=unknown;;
esac

echo -e "${BLUE}[1/6]${NC} Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "  ${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "  ${RED}✗${NC} Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} pip"
else
    echo -e "  ${RED}✗${NC} pip not found. Please install pip"
    exit 1
fi

# Check for Bun or Node
HAS_BUN=false
HAS_NODE=false

if command -v bun &> /dev/null; then
    BUN_VERSION=$(bun --version 2>&1)
    echo -e "  ${GREEN}✓${NC} Bun $BUN_VERSION"
    HAS_BUN=true
elif command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1)
    echo -e "  ${GREEN}✓${NC} Node.js $NODE_VERSION"
    HAS_NODE=true
else
    echo -e "  ${YELLOW}!${NC} Neither Bun nor Node.js found. Installing Bun..."
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
    HAS_BUN=true
    echo -e "  ${GREEN}✓${NC} Bun installed"
fi

# Set install directory
INSTALL_DIR="${AGENTPULSE_DIR:-$HOME/.agentpulse}"

echo ""
echo -e "${BLUE}[2/6]${NC} Creating installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

echo ""
echo -e "${BLUE}[3/6]${NC} Downloading AgentPulse..."

# Download latest release or clone
if command -v git &> /dev/null; then
    if [ -d "$INSTALL_DIR/repo" ]; then
        echo "  Updating existing installation..."
        cd "$INSTALL_DIR/repo"
        git pull --quiet
    else
        git clone --quiet --depth 1 https://github.com/nandusmasta/agentpulse.git "$INSTALL_DIR/repo"
        cd "$INSTALL_DIR/repo"
    fi
    echo -e "  ${GREEN}✓${NC} Downloaded"
else
    echo -e "  ${RED}✗${NC} Git not found. Please install git"
    exit 1
fi

echo ""
echo -e "${BLUE}[4/6]${NC} Installing Python SDK..."
pip3 install --quiet --upgrade agentpulse-ai
echo -e "  ${GREEN}✓${NC} SDK installed (pip install agentpulse-ai)"

echo ""
echo -e "${BLUE}[5/6]${NC} Installing collector dependencies..."
cd "$INSTALL_DIR/repo/packages/collector"
if [ "$HAS_BUN" = true ]; then
    bun install --silent
else
    npm install --silent
fi
echo -e "  ${GREEN}✓${NC} Collector ready"

echo ""
echo -e "${BLUE}[6/6]${NC} Installing dashboard dependencies..."
cd "$INSTALL_DIR/repo/packages/dashboard"
if [ "$HAS_BUN" = true ]; then
    bun install --silent
else
    npm install --silent
fi
echo -e "  ${GREEN}✓${NC} Dashboard ready"

# Create start script
cat > "$INSTALL_DIR/start.sh" << 'STARTSCRIPT'
#!/bin/bash
INSTALL_DIR="${AGENTPULSE_DIR:-$HOME/.agentpulse}"
cd "$INSTALL_DIR/repo/packages/collector"

# Check if already running
if lsof -i :3000 &> /dev/null; then
    echo "Collector already running on port 3000"
else
    if command -v bun &> /dev/null; then
        nohup bun run src/index.ts > "$INSTALL_DIR/collector.log" 2>&1 &
    else
        nohup npx tsx src/index.ts > "$INSTALL_DIR/collector.log" 2>&1 &
    fi
    echo "Collector started on port 3000"
fi

cd "$INSTALL_DIR/repo/packages/dashboard"
if lsof -i :5173 &> /dev/null; then
    echo "Dashboard already running on port 5173"
else
    if command -v bun &> /dev/null; then
        nohup bun run dev > "$INSTALL_DIR/dashboard.log" 2>&1 &
    else
        nohup npm run dev > "$INSTALL_DIR/dashboard.log" 2>&1 &
    fi
    echo "Dashboard started on port 5173"
fi

sleep 2
echo ""
echo "🎉 AgentPulse is running!"
echo "   Dashboard: http://localhost:5173"
echo "   Collector: http://localhost:3000"
STARTSCRIPT
chmod +x "$INSTALL_DIR/start.sh"

# Create stop script
cat > "$INSTALL_DIR/stop.sh" << 'STOPSCRIPT'
#!/bin/bash
echo "Stopping AgentPulse..."
pkill -f "agentpulse.*collector" 2>/dev/null || true
pkill -f "agentpulse.*dashboard" 2>/dev/null || true
lsof -ti :3000 | xargs kill 2>/dev/null || true
lsof -ti :5173 | xargs kill 2>/dev/null || true
echo "Stopped"
STOPSCRIPT
chmod +x "$INSTALL_DIR/stop.sh"

# Start services
echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""

read -p "Start AgentPulse now? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    "$INSTALL_DIR/start.sh"
else
    echo ""
    echo "To start later, run:"
    echo "  ~/.agentpulse/start.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Quick test - add this to your Python code:"
echo ""
echo -e "${YELLOW}from agentpulse import AgentPulse, trace"
echo ""
echo "ap = AgentPulse(endpoint=\"http://localhost:3000\")"
echo ""
echo "@trace(name=\"my-agent\")"
echo "def run():"
echo "    print(\"Hello from AgentPulse!\")"
echo ""
echo "run()"
echo -e "ap.shutdown()${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Commands:"
echo "  ~/.agentpulse/start.sh  - Start services"
echo "  ~/.agentpulse/stop.sh   - Stop services"
echo ""
echo "Docs: https://github.com/nandusmasta/agentpulse"
echo ""
