# 🎮 RPG Maker MV/MZ Decryption Toolkit

A comprehensive Python toolkit for decrypting and managing RPG Maker MV/MZ encrypted games, specifically designed for use with JoiPlay on Android devices.

## 📋 Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Scripts Overview](#scripts-overview)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **Full Decryption**: Decrypt `.rpgmvp`, `.rpgmvo`, `.png_`, `.ogg_` and other encrypted files
- **Live2D Support**: Extract and restore Live2D assets from original game archives
- **Multi-Format Archives**: Support for ZIP, RAR, and 7Z archives
- **Automatic Detection**: Smart detection of encryption keys and archive formats
- **Integrity Verification**: Validate decrypted files to ensure correctness
- **Diagnostic Tools**: Advanced analysis of encryption methods and file formats
- **Backup Management**: Safe backup of encrypted files before processing

## 🔧 Requirements

### Core Requirements
- Python 3.7+
- Android device with Termux (for mobile use)

### Python Dependencies
```bash
# Core (included in Python)
- pathlib
- json
- zipfile

# Optional (for additional archive formats)
- rarfile  # For RAR support
- py7zr    # For 7Z support
```

## 📦 Installation

### On Android (Termux)

1. **Install Termux** from F-Droid or Play Store

2. **Install Python and dependencies**:
```bash
pkg update
pkg install python
pip install --upgrade pip
```

3. **Install optional dependencies** (for RAR/7Z support):
```bash
pip install rarfile --break-system-packages
pip install py7zr --break-system-packages
```

4. **Clone or download the scripts**:
```bash
cd ~/storage/downloads
# Place all .py files here
chmod +x *.py
```

### On Desktop (Linux/Mac/Windows)

1. **Install Python 3.7+** from [python.org](https://python.org)

2. **Install dependencies**:
```bash
pip install rarfile py7zr
```

3. **Download the scripts** to your working directory

## 📚 Scripts Overview

### 1. `decrypt_all_in_one.py` ⭐ Main Decryption Tool

The all-in-one solution for decrypting RPG Maker games.

**Features**:
- Automatic encryption key detection
- Batch decryption of all encrypted files
- Integrity verification
- System.json configuration update

**Usage**:
```bash
python decrypt_all_in_one.py /path/to/game
```

**What it does**:
1. Scans for `System.json` and extracts encryption key
2. Finds all encrypted files (`.png_`, `.ogg_`, `.rpgmvp`, etc.)
3. Decrypts using XOR cipher on bytes 16-31
4. Verifies file signatures (PNG, OGG, M4A)
5. Disables encryption flags in `System.json`

---

### 2. `restaurar_live2d_universal.py` 🎭 Live2D Restoration

Extracts and restores Live2D assets from original game archives.

**Features**:
- Multi-format support (ZIP/RAR/7Z)
- Automatic format detection
- Handles encrypted Live2D files
- Preserves directory structure

**Usage**:
```bash
python restaurar_live2d_universal.py <archive> <game_folder> [encryption_key]
```

**Examples**:
```bash
# ZIP archive
python restaurar_live2d_universal.py game.zip /sdcard/joiplay/mygame

# RAR archive with explicit key
python restaurar_live2d_universal.py game.rar ~/mygame a5cac2058418585300629

# 7Z archive (auto-detect key from System.json)
python restaurar_live2d_universal.py game.7z /path/to/game
```

---

### 3. `diagnostico_arquivo.py` 🔍 Archive Diagnostics

Analyzes compressed archives to detect their true format.

**Features**:
- Magic byte analysis
- Format detection (ZIP/RAR/7Z/GZIP/TAR)
- File listing
- Multi-volume detection

**Usage**:
```bash
python diagnostico_arquivo.py <archive_file>
```

**Example**:
```bash
python diagnostico_arquivo.py suspicious_file.rar
```

**Output**:
- File size and extension
- Hex dump of magic bytes
- Detected format(s)
- List of contained files

---

### 4. `diagnostico_avancado.py` 🧪 Advanced Diagnostics

Deep analysis of RPG Maker encryption implementation.

**Features**:
- System.json analysis
- Custom encryption detection
- Entropy analysis
- XOR testing at multiple offsets

**Usage**:
```bash
# Analyze entire game
python diagnostico_avancado.py /path/to/game

# Analyze specific file
python diagnostico_avancado.py /path/to/game img/system/Window.png_
```

**Use Cases**:
- Custom encryption detection
- Debugging decryption issues
- Analyzing rpg_core.js modifications

---

### 5. `buscar_live2d.py` 🎨 Live2D File Scanner

Locates all Live2D-related files in a game directory.

**Features**:
- Recursive directory scanning
- Extension-based filtering
- Plugin configuration analysis
- Categorized results

**Usage**:
```bash
python buscar_live2d.py /path/to/game
```

**Searched Extensions**:
- `.model3.json`, `.moc3`, `.motion3.json`
- `.physics3.json`, `.cdi3.json`
- `.exp3.json`, `.userdata3.json`
- Encrypted variants (`.json_`, `.moc3_`, etc.)

---

### 6. `backup_encrypted.py` 💾 Backup Manager

Safely backs up encrypted files before decryption.

**Features**:
- Preserves directory structure
- Move (not copy) for space efficiency
- Rollback capability

**Usage**:
```bash
python backup_encrypted.py /path/to/game
```

**Backup Location**: `<game_folder>/_backup_encrypted/`

**To Restore**:
```bash
cp -r /path/to/game/_backup_encrypted/* /path/to/game/
```

## 📖 Usage Guide

### Complete Workflow

#### Step 1: Backup Original Files
```bash
python backup_encrypted.py /sdcard/joiplay/mygame
```

#### Step 2: Decrypt Game Files
```bash
python decrypt_all_in_one.py /sdcard/joiplay/mygame
```

#### Step 3: Restore Live2D Assets (if needed)
```bash
python restaurar_live2d_universal.py ~/Download/game.zip /sdcard/joiplay/mygame
```

#### Step 4: Test in JoiPlay
1. Open JoiPlay
2. Force stop the app (if previously loaded)
3. Clear cache
4. Load the game

### Common Scenarios

#### Scenario 1: Basic Game Decryption
```bash
cd ~/storage/downloads
python decrypt_all_in_one.py games/mygame
```

#### Scenario 2: Missing Live2D Files
```bash
# First, decrypt the game
python decrypt_all_in_one.py games/mygame

# Then restore Live2D from original archive
python restaurar_live2d_universal.py game_original.zip games/mygame
```

#### Scenario 3: Unknown Archive Format
```bash
# Diagnose first
python diagnostico_arquivo.py mysterious_file.rar

# If detected as ZIP, rename and use
mv mysterious_file.rar mysterious_file.zip
python restaurar_live2d_universal.py mysterious_file.zip games/mygame
```

#### Scenario 4: Custom Encryption
```bash
# Run advanced diagnostics
python diagnostico_avancado.py games/mygame

# Analyze specific file
python diagnostico_avancado.py games/mygame img/system/Window.png_
```

## 🔧 Troubleshooting

### Issue: "Not a RAR file" error
**Solution**: The file might be ZIP with `.rar` extension. Use `diagnostico_arquivo.py` to detect true format.

### Issue: "Attempt to use ZIP archive that was already closed"
**Solution**: Update to latest version of `restaurar_live2d_universal.py` which includes proper file handle management.

### Issue: Live2D animations not working
**Possible causes**:
1. Missing Live2D files - use `buscar_live2d.py` to check
2. Files still encrypted - check for `.json_` or `.moc3_` extensions
3. Incorrect directory structure

**Solution**:
```bash
# Scan for Live2D files
python buscar_live2d.py /path/to/game

# If files are missing, restore from original
python restaurar_live2d_universal.py original.zip /path/to/game
```

### Issue: Decrypted files are corrupted
**Symptoms**: Files have wrong signatures or don't open

**Solution**:
1. Check if custom encryption is used:
```bash
python diagnostico_avancado.py /path/to/game
```

2. Look for modified `rpg_core.js`:
```bash
grep -n "Decrypter" /path/to/game/js/rpg_core.js
```

### Issue: "Command not found" in Termux
**Solution**:
```bash
# Ensure Python is installed
pkg install python

# Make scripts executable
chmod +x *.py

# Use python explicitly
python script_name.py
```

## 🎯 Best Practices

1. **Always backup first**: Use `backup_encrypted.py` before any operations
2. **Test incrementally**: Decrypt a few files first to verify the process works
3. **Keep original archives**: Don't delete the original game archive
4. **Check file integrity**: The decryption script includes automatic verification
5. **Clear JoiPlay cache**: After decryption, force stop JoiPlay and clear cache

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

### Development Setup
```bash
git clone <repository-url>
cd rpgmaker-decryption-toolkit
# Make changes and test
python -m pytest tests/  # If you add tests
```

### Code Style
- Follow PEP 8 guidelines
- Add docstrings to functions
- Include error handling
- Test on both Android (Termux) and desktop

## 📄 License

This project is released under the MIT License. See LICENSE file for details.

## ⚠️ Disclaimer

This toolkit is intended for **personal use only** to enable playing legitimately purchased games on alternative platforms like JoiPlay. Please:

- Only use with games you own legally
- Respect game developers' intellectual property
- Do not distribute decrypted game files
- Support game developers by purchasing their games

## 🙏 Acknowledgments

- RPG Maker community for encryption format documentation
- JoiPlay developers for Android RPG Maker support
- Live2D creators for the animation technology

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Run diagnostic scripts to gather information
3. Open an issue with diagnostic output and error messages

## 🔄 Version History

### v1.0.0 (Initial Release)
- Complete decryption toolkit
- Multi-format archive support
- Live2D restoration
- Diagnostic tools
- Backup management

---

<div align="center">

### 🤖 Created with Claude Sonnet 4.5

**Built to solve real problems** 🎮✨

*Making RPG Maker games playable everywhere*

</div>
