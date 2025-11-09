# ZeroTouch Atlas - Setup Guide

## Quick Start

### From WSL (Linux)
```bash
cd ~/.claude/lib
./start_atlas.sh
```

### From Windows
```cmd
start_atlas.bat
```

Or double-click `start_atlas.bat` in Windows File Explorer:
`\\wsl$\Ubuntu\home\jevenson\.claude\lib\start_atlas.bat`

## Access the App

Once started, open your browser to:
```
http://localhost:8501
```

## What Was Fixed

### Event Loop Issue (RESOLVED ✅)
**Problem**: `RuntimeError: This event loop is already running`

**Solution Applied**:
1. Added `nest-asyncio` import and `nest_asyncio.apply()` to `atlas_app.py`
2. Created isolated virtual environment with all dependencies
3. Installed `nest-asyncio>=1.6.0` package

### Stable Environment Setup
- **Virtual Environment**: `~/.claude/lib/venv/`
- **Dependencies**: Frozen in `requirements.txt`
- **Python Version**: 3.12.x

## Dependencies Installed

Core packages:
- `streamlit>=1.28.0` - Web UI framework
- `nest-asyncio>=1.6.0` - Event loop fix for Streamlit
- `anthropic>=0.34.0` - Claude API SDK
- `pandas>=2.0.0` - Data processing
- `python-dotenv>=1.0.0` - Environment variable management

All dependencies are locked in `requirements.txt` for reproducibility.

## Troubleshooting

### If the app won't start:

1. **Check virtual environment**:
   ```bash
   ls -la ~/.claude/lib/venv
   ```

2. **Reinstall dependencies**:
   ```bash
   cd ~/.claude/lib
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Check Python version**:
   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

### If you see "module not found" errors:

Activate the virtual environment first:
```bash
cd ~/.claude/lib
source venv/bin/activate
streamlit run atlas_app.py
```

### If port 8501 is already in use:

Kill existing Streamlit processes:
```bash
pkill -f streamlit
```

Or use a different port:
```bash
cd ~/.claude/lib
source venv/bin/activate
streamlit run atlas_app.py --server.port 8502
```

## Manual Setup (Advanced)

If you need to recreate the environment from scratch:

```bash
cd ~/.claude/lib

# Remove old virtual environment
rm -rf venv

# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run atlas_app.py --server.port 8501
```

## API Keys

The app uses Claude API via MCP bridge (Claude Code Max subscription).
No manual API key configuration is needed for basic functionality.

If you want to use additional providers (OpenAI, Google):
1. Create `~/.claude/.env` file
2. Add your API keys:
   ```
   ANTHROPIC_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   ```

## Architecture

```
~/.claude/lib/
├── atlas_app.py           # Main Streamlit application
├── venv/                  # Isolated Python environment
├── requirements.txt       # Dependency specifications
├── start_atlas.sh         # Linux/WSL launcher
├── start_atlas.bat        # Windows launcher
├── ATLAS_SETUP.md         # This file
│
├── security/              # Zero-Trust security module
│   ├── __init__.py
│   └── input_boundary_filter.py
│
├── core/                  # Core constants and models
│   ├── __init__.py
│   └── constants.py
│
└── [other modules]        # RAG, agents, orchestration, etc.
```

## Features

✅ **Event Loop Fixed** - Stable async operation in Streamlit
✅ **Virtual Environment** - Isolated, reproducible setup
✅ **Auto-Launcher** - One-command startup
✅ **Cross-Platform** - Works on WSL & Windows
✅ **Dependency Management** - Locked versions in requirements.txt

## Next Steps

After starting the app, you can:
1. Upload task files via drag-and-drop
2. Submit manual tasks via the form
3. Select RAG topics for optimized routing
4. Monitor real-time agent activity in the dashboard
5. Use multi-perspective dialogue for complex analysis

## Support

**Documentation**: `~/.claude/lib/README.md`
**Event Loop Docs**: `/mnt/d/Dev/EVENT_LOOP_README.md`
**Project Issues**: Check `~/.claude/lib/` for component-specific READMEs

---

**Version**: 1.0.0 (Stable)
**Last Updated**: November 9, 2025
**Status**: ✅ Ready for production use
