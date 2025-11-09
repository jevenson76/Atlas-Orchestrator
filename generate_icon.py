#!/usr/bin/env python3
"""
Generate icon files for the Sync Wrapper Demo
Creates PNG and XPM formats from scratch
"""

import os
import sys

def create_xpm_icon():
    """Create an XPM icon for Linux desktop"""
    xpm_content = '''/* XPM */
static char *sync_wrapper_icon[] = {
/* columns rows colors chars-per-pixel */
"48 48 10 1 ",
"  c #2B2B2B",
". c #4A9EFF",
"X c #FF6B6B",
"o c #FFA500",
"O c #4ADE80",
"+ c #666666",
"@ c #888888",
"# c #D4D4D4",
"$ c #1E1E1E",
"% c #FFFFFF",
/* pixels */
"                                                ",
"                    ........                    ",
"                 ...........                    ",
"               ..............                   ",
"              ...............                   ",
"             .................                  ",
"            ..................                  ",
"           ...................                  ",
"          ......  ASYNC  ......                 ",
"         .......................                ",
"        .........................               ",
"        XX......................OO              ",
"       XXX......................OOO             ",
"       XXX......................OOO             ",
"      XXXX......................OOOO            ",
"      XXXX......................OOOO            ",
"     XXXXX......................OOOOO           ",
"     XXXXX.......      .........OOOOO           ",
"     ooooo.......  ..  .........OOOOO           ",
"     ooooo....... .... .........OOOOO           ",
"     ooooo........    ..........OOOOO           ",
"     ooooo......................+++++           ",
"     ooooo......................+++++           ",
"     ooooo.......      .........+++++           ",
"     OOOOO.......  ..  .........+++++           ",
"     OOOOO....... .... .........+++++           ",
"     OOOOO........    ..........+++++           ",
"      OOOO......................++++            ",
"      OOOO......................++++            ",
"       OOO......................+++             ",
"       OOO......................+++             ",
"        OO........................+             ",
"        .........................               ",
"         .......................                ",
"          ......  SYNC  .......                 ",
"           ...................                  ",
"            ..................                  ",
"             .................                  ",
"              ................                  ",
"               ..............                   ",
"                 ...........                    ",
"                    ........                    ",
"                                                ",
"            run_async_safely()                  ",
"                                                ",
"             Sync Wrapper Demo                  ",
"                                                ",
"                                                "
};'''

    with open('/home/jevenson/.claude/lib/sync_wrapper_icon.xpm', 'w') as f:
        f.write(xpm_content)
    print("✅ Created sync_wrapper_icon.xpm")

def create_png_icon():
    """Create a PNG icon using PIL if available"""
    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create 256x256 image
        size = 256
        img = Image.new('RGBA', (size, size), (43, 43, 43, 255))
        draw = ImageDraw.Draw(img)

        # Draw main circle
        draw.ellipse([8, 8, size-8, size-8], outline=(74, 158, 255, 255), width=4)

        # Draw async waves (left)
        for i, color in enumerate([(255, 107, 107), (255, 165, 0), (74, 222, 128)]):
            y = 100 + i * 30
            # Draw wavy line
            points = []
            for x in range(40, 90, 5):
                wave_y = y + 10 * ((x - 65) / 25) ** 2 - 10
                points.append((x, wave_y))
            for j in range(len(points) - 1):
                draw.line([points[j], points[j+1]], fill=color + (255,), width=3)

        # Draw center arrow
        draw.rectangle([88, 120, 168, 136], fill=(74, 158, 255, 255))
        draw.polygon([(168, 108), (188, 128), (168, 148)], fill=(74, 158, 255, 255))

        # Draw center circle with 'S'
        draw.ellipse([108, 108, 148, 148], outline=(74, 158, 255, 255), width=3, fill=(43, 43, 43, 255))

        # Draw sync line (right)
        draw.rectangle([176, 126, 216, 130], fill=(74, 222, 128, 255))
        draw.ellipse([212, 124, 220, 132], fill=(74, 222, 128, 255))

        # Add text
        try:
            # Try to use a nice font if available
            from PIL import ImageFont
            font = ImageFont.load_default()
        except:
            font = None

        # Draw labels
        draw.text((65, 70), "ASYNC", fill=(136, 136, 136, 255), font=font)
        draw.text((185, 70), "SYNC", fill=(136, 136, 136, 255), font=font)
        draw.text((128, 20), "run_async_safely()", fill=(74, 158, 255, 255), font=font, anchor="mt")
        draw.text((128, 230), "Sync Wrapper Demo", fill=(102, 102, 102, 255), font=font, anchor="mt")

        # Save PNG
        img.save('/home/jevenson/.claude/lib/sync_wrapper_icon.png')
        print("✅ Created sync_wrapper_icon.png (256x256)")

        # Create smaller versions
        for size in [128, 64, 48, 32, 16]:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(f'/home/jevenson/.claude/lib/sync_wrapper_icon_{size}.png')
            print(f"✅ Created sync_wrapper_icon_{size}.png ({size}x{size})")

        return True

    except ImportError:
        print("⚠️  PIL not installed. Skipping PNG generation.")
        print("   Install with: pip install Pillow")
        return False

def create_ascii_icon():
    """Create an ASCII art icon for terminal display"""
    ascii_art = r"""
    ╔═══════════════════════════════════════╗
    ║      🔄 SYNC WRAPPER DEMO 🔄          ║
    ╠═══════════════════════════════════════╣
    ║                                       ║
    ║    ASYNC ~~~~> [S] =====> SYNC       ║
    ║                                       ║
    ║    async def      run_async_safely()  ║
    ║    ↓              ↓                   ║
    ║    coroutine  →  result               ║
    ║                                       ║
    ║    Complex    →  Simple               ║
    ║    await      →  No await             ║
    ║    asyncio    →  Just works           ║
    ║                                       ║
    ╠═══════════════════════════════════════╣
    ║    Click to launch interactive demo  ║
    ╚═══════════════════════════════════════╝
    """

    with open('/home/jevenson/.claude/lib/sync_wrapper_icon.txt', 'w') as f:
        f.write(ascii_art)

    print("✅ Created sync_wrapper_icon.txt (ASCII art)")
    print("\nASCII Icon Preview:")
    print(ascii_art)

def create_ico_file():
    """Create a Windows ICO file"""
    try:
        from PIL import Image

        # Load or create PNG first
        if os.path.exists('/home/jevenson/.claude/lib/sync_wrapper_icon.png'):
            img = Image.open('/home/jevenson/.claude/lib/sync_wrapper_icon.png')
        else:
            # Create if doesn't exist
            if not create_png_icon():
                return False
            img = Image.open('/home/jevenson/.claude/lib/sync_wrapper_icon.png')

        # Create ICO with multiple sizes
        img.save('/home/jevenson/.claude/lib/sync_wrapper_icon.ico', format='ICO',
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

        print("✅ Created sync_wrapper_icon.ico (Windows icon)")
        return True

    except ImportError:
        print("⚠️  PIL not installed. Skipping ICO generation.")
        return False
    except Exception as e:
        print(f"⚠️  Could not create ICO: {e}")
        return False

def update_desktop_file():
    """Update the desktop file to use the new icon"""
    desktop_file = '/home/jevenson/.claude/lib/sync-wrapper-demo.desktop'
    icon_path = '/home/jevenson/.claude/lib/sync_wrapper_icon'

    try:
        with open(desktop_file, 'r') as f:
            content = f.read()

        # Update icon path
        import re
        content = re.sub(r'Icon=.*', f'Icon={icon_path}', content)

        with open(desktop_file, 'w') as f:
            f.write(content)

        print(f"✅ Updated {desktop_file} with new icon path")
    except Exception as e:
        print(f"⚠️  Could not update desktop file: {e}")

def main():
    print("=" * 50)
    print("Sync Wrapper Demo - Icon Generator")
    print("=" * 50)
    print()

    os.chdir('/home/jevenson/.claude/lib')

    # Create all icon formats
    print("Creating icon files...")
    print()

    # XPM (always works, no dependencies)
    create_xpm_icon()

    # ASCII art
    create_ascii_icon()

    # PNG (requires PIL)
    png_created = create_png_icon()

    # ICO (requires PIL and PNG)
    if png_created:
        create_ico_file()

    # Update desktop file
    update_desktop_file()

    print()
    print("=" * 50)
    print("Icon generation complete!")
    print()
    print("📁 Files created in: /home/jevenson/.claude/lib/")
    print()
    print("Available icons:")
    for ext in ['svg', 'xpm', 'png', 'ico', 'txt']:
        icon_file = f'sync_wrapper_icon.{ext}'
        if os.path.exists(f'/home/jevenson/.claude/lib/{icon_file}'):
            size = os.path.getsize(f'/home/jevenson/.claude/lib/{icon_file}')
            print(f"  • {icon_file:<30} ({size:,} bytes)")

    print()
    print("Usage:")
    print("  • SVG: Scalable, web-friendly")
    print("  • PNG: Desktop applications")
    print("  • XPM: Linux desktop environments")
    print("  • ICO: Windows applications")
    print("  • TXT: Terminal/console display")
    print()

if __name__ == "__main__":
    main()