#!/bin/bash
# ZeroTouch Atlas Launcher Script
# Activates virtual environment and starts Streamlit app

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  ZeroTouch Atlas Launcher${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not found!${NC}"
    echo -e "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    echo -e "${GREEN}Virtual environment created.${NC}"
    echo ""

    echo -e "Installing dependencies..."
    "$SCRIPT_DIR/venv/bin/pip" install --upgrade pip
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
    echo -e "${GREEN}Dependencies installed.${NC}"
    echo ""
fi

# Check if atlas_app.py exists
if [ ! -f "$SCRIPT_DIR/atlas_app.py" ]; then
    echo -e "${YELLOW}Error: atlas_app.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Activate virtual environment and run Streamlit
echo -e "${GREEN}Starting ZeroTouch Atlas...${NC}"
echo -e "Access the app at: ${BLUE}http://localhost:8501${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

cd "$SCRIPT_DIR"
source venv/bin/activate
exec streamlit run atlas_app.py --server.port 8501 --server.headless true
