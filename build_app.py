import PyInstaller.__main__
import os

def build():
    print("🚀 Building TeleDownloadr...")
    
    PyInstaller.__main__.run([
        'teledownloadr/__main__.py',
        '--name=TeleDownloadr',
        '--onefile',
        '--clean',
        '--noconfirm',
        # Add data files or hidden imports if needed via --hidden-import or --add-data
        '--hidden-import=teledownloadr',
        '--hidden-import=rich',
        '--hidden-import=questionary'
    ])
    
    print("\n✅ Build complete! Check 'dist/TeleDownloadr'")

if __name__ == "__main__":
    build()
