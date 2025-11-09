#!/bin/bash
# Install Sync Wrapper Demo Icon

echo "╔═══════════════════════════════════════╗"
echo "║  Sync Wrapper Demo - Icon Installer   ║"
echo "╚═══════════════════════════════════════╝"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to install desktop icon
install_desktop_icon() {
    local src="/home/jevenson/.claude/lib/sync-wrapper-demo.desktop"
    local desktop_dir="$HOME/Desktop"
    local apps_dir="$HOME/.local/share/applications"

    # Check if source exists
    if [ ! -f "$src" ]; then
        echo -e "${RED}✗${NC} Desktop file not found: $src"
        return 1
    fi

    echo "Installing desktop icon..."

    # Install to Desktop if it exists
    if [ -d "$desktop_dir" ]; then
        cp "$src" "$desktop_dir/"
        chmod +x "$desktop_dir/sync-wrapper-demo.desktop"
        echo -e "${GREEN}✓${NC} Icon installed to Desktop"
    else
        echo -e "${YELLOW}⚠${NC} Desktop folder not found, skipping..."
    fi

    # Install to applications menu
    mkdir -p "$apps_dir"
    cp "$src" "$apps_dir/"
    chmod +x "$apps_dir/sync-wrapper-demo.desktop"
    echo -e "${GREEN}✓${NC} Icon installed to Applications menu"

    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$apps_dir" 2>/dev/null
        echo -e "${GREEN}✓${NC} Desktop database updated"
    fi

    return 0
}

# Function to display icon info
show_icon_info() {
    echo
    echo "📦 Available Icon Formats:"
    echo "──────────────────────────────────"

    local icon_dir="/home/jevenson/.claude/lib"

    for icon in sync_wrapper_icon.*; do
        if [ -f "$icon_dir/$icon" ]; then
            local size=$(stat -c%s "$icon_dir/$icon" 2>/dev/null || stat -f%z "$icon_dir/$icon" 2>/dev/null || echo "?")
            local ext="${icon##*.}"

            case "$ext" in
                svg) echo -e "  ${GREEN}•${NC} $icon (Scalable Vector Graphics)";;
                png) echo -e "  ${GREEN}•${NC} $icon (Portable Network Graphics)";;
                xpm) echo -e "  ${GREEN}•${NC} $icon (X PixMap for Linux)";;
                ico) echo -e "  ${GREEN}•${NC} $icon (Windows Icon)";;
                txt) echo -e "  ${GREEN}•${NC} $icon (ASCII Art)";;
                *) echo -e "  ${GREEN}•${NC} $icon";;
            esac
        fi
    done
}

# Function to create symbolic link
create_icon_symlink() {
    local icon_src="/home/jevenson/.claude/lib/sync_wrapper_icon.png"
    local icon_link="/home/jevenson/.local/share/icons/sync_wrapper_icon.png"

    if [ -f "$icon_src" ]; then
        mkdir -p "$(dirname "$icon_link")"
        ln -sf "$icon_src" "$icon_link"
        echo -e "${GREEN}✓${NC} Icon symlink created in ~/.local/share/icons/"
    fi
}

# Main installation
echo "🎯 Installation Options:"
echo "  1. Install desktop icon (recommended)"
echo "  2. View icon files"
echo "  3. Display ASCII icon"
echo "  4. All of the above"
echo
read -p "Select option (1-4): " choice

case $choice in
    1)
        install_desktop_icon
        create_icon_symlink
        ;;
    2)
        show_icon_info
        ;;
    3)
        if [ -f "/home/jevenson/.claude/lib/sync_wrapper_icon.txt" ]; then
            cat "/home/jevenson/.claude/lib/sync_wrapper_icon.txt"
        else
            echo -e "${RED}✗${NC} ASCII icon not found"
        fi
        ;;
    4)
        install_desktop_icon
        create_icon_symlink
        show_icon_info
        echo
        if [ -f "/home/jevenson/.claude/lib/sync_wrapper_icon.txt" ]; then
            cat "/home/jevenson/.claude/lib/sync_wrapper_icon.txt"
        fi
        ;;
    *)
        echo -e "${YELLOW}Invalid option${NC}"
        exit 1
        ;;
esac

echo
echo "╔═══════════════════════════════════════╗"
echo "║  Installation Complete!                ║"
echo "╚═══════════════════════════════════════╝"
echo
echo "Launch methods:"
echo "  • Click icon on Desktop"
echo "  • Search 'Sync Wrapper Demo' in applications"
echo "  • Run: ./demo_sync_wrapper.py"
echo "  • Windows: Double-click launch_demo_with_icon.bat"
echo