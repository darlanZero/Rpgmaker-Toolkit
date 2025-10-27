#!/usr/bin/env python3
"""
Diagnostica arquivos compactados - verifica o formato real
"""

import sys
from pathlib import Path

def hex_dump(data, max_bytes=64):
    """Mostra dump hexadecimal dos bytes"""
    result = []
    for i in range(0, min(len(data), max_bytes), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        result.append(f'{i:04x}  {hex_part:<48}  {ascii_part}')
    return '\n'.join(result)

def detect_format(file_path):
    """Detecta o formato real do arquivo"""
    
    file_path = Path(file_path)
    
    print("="*70)
    print(f"  DIAGNÓSTICO DE ARQUIVO COMPACTADO")
    print("="*70)
    
    if not file_path.exists():
        print(f"\n❌ Arquivo não encontrado: {file_path}")
        return
    
    file_size = file_path.stat().st_size
    
    print(f"\n📦 Arquivo: {file_path.name}")
    print(f"📊 Tamanho: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"📁 Extensão: {file_path.suffix}")
    
    # Lê os primeiros bytes
    with open(file_path, 'rb') as f:
        header = f.read(512)
    
    print(f"\n🔍 MAGIC BYTES (primeiros 64 bytes):")
    print(hex_dump(header))
    
    # Análise de formato
    print(f"\n📋 ANÁLISE:")
    
    detected = []
    
    # ZIP: 50 4B 03 04 (PK..)
    if header[:4] == b'\x50\x4B\x03\x04':
        detected.append("ZIP")
        print(f"✅ ZIP detectado (assinatura: 50 4B 03 04)")
    
    # RAR 4.x: 52 61 72 21 1A 07 00 (Rar!...)
    if header[:7] == b'\x52\x61\x72\x21\x1A\x07\x00':
        detected.append("RAR 4.x")
        print(f"✅ RAR 4.x detectado (assinatura: 52 61 72 21 1A 07 00)")
    
    # RAR 5.x: 52 61 72 21 1A 07 01 00 (Rar!....)
    if header[:8] == b'\x52\x61\x72\x21\x1A\x07\x01\x00':
        detected.append("RAR 5.x")
        print(f"✅ RAR 5.x detectado (assinatura: 52 61 72 21 1A 07 01 00)")
    
    # 7Z: 37 7A BC AF 27 1C
    if header[:6] == b'\x37\x7A\xBC\xAF\x27\x1C':
        detected.append("7Z")
        print(f"✅ 7Z detectado (assinatura: 37 7A BC AF 27 1C)")
    
    # GZIP: 1F 8B
    if header[:2] == b'\x1F\x8B':
        detected.append("GZIP")
        print(f"✅ GZIP detectado (assinatura: 1F 8B)")
    
    # TAR (texto "ustar")
    if b'ustar' in header:
        detected.append("TAR")
        print(f"✅ TAR detectado (texto 'ustar' encontrado)")
    
    if not detected:
        print(f"❌ Formato não reconhecido!")
        print(f"\n💡 Assinaturas conhecidas:")
        print(f"   ZIP:     50 4B 03 04")
        print(f"   RAR 4.x: 52 61 72 21 1A 07 00")
        print(f"   RAR 5.x: 52 61 72 21 1A 07 01 00")
        print(f"   7Z:      37 7A BC AF 27 1C")
        print(f"   GZIP:    1F 8B")
    else:
        print(f"\n✨ Formato(s) detectado(s): {', '.join(detected)}")
    
    # Verifica se é multi-volume
    print(f"\n🔍 VERIFICAÇÕES ADICIONAIS:")
    
    if '.part' in file_path.name.lower():
        print(f"⚠️  Arquivo multi-volume detectado!")
        print(f"   Certifique-se de ter todos os volumes (.part1, .part2, etc)")
    
    if file_path.suffix.lower() in ['.001', '.002']:
        print(f"⚠️  Possível arquivo dividido detectado!")
        print(f"   Procure por outros arquivos com extensões .001, .002, etc")
    
    # Tenta listar conteúdo
    print(f"\n📦 TENTANDO LISTAR CONTEÚDO:")
    
    if "ZIP" in detected:
        try:
            from zipfile import ZipFile
            with ZipFile(file_path, 'r') as zf:
                files = zf.namelist()
                print(f"✅ ZIP válido! {len(files)} arquivos encontrados")
                print(f"\n📋 Primeiros 10 arquivos:")
                for f in files[:10]:
                    print(f"   - {f}")
                if len(files) > 10:
                    print(f"   ... e mais {len(files)-10} arquivos")
        except Exception as e:
            print(f"❌ Erro ao abrir como ZIP: {e}")
    
    if "RAR" in ' '.join(detected):
        try:
            import rarfile
            with rarfile.RarFile(file_path, 'r') as rf:
                files = rf.namelist()
                print(f"✅ RAR válido! {len(files)} arquivos encontrados")
                print(f"\n📋 Primeiros 10 arquivos:")
                for f in files[:10]:
                    print(f"   - {f}")
                if len(files) > 10:
                    print(f"   ... e mais {len(files)-10} arquivos")
        except ImportError:
            print(f"⚠️  Biblioteca 'rarfile' não instalada")
            print(f"   Instale com: pip install rarfile --break-system-packages")
        except Exception as e:
            print(f"❌ Erro ao abrir como RAR: {e}")
    
    if "7Z" in detected:
        try:
            import py7zr
            with py7zr.SevenZipFile(file_path, 'r') as sz:
                files = sz.getnames()
                print(f"✅ 7Z válido! {len(files)} arquivos encontrados")
                print(f"\n📋 Primeiros 10 arquivos:")
                for f in files[:10]:
                    print(f"   - {f}")
                if len(files) > 10:
                    print(f"   ... e mais {len(files)-10} arquivos")
        except ImportError:
            print(f"⚠️  Biblioteca 'py7zr' não instalada")
            print(f"   Instale com: pip install py7zr --break-system-packages")
        except Exception as e:
            print(f"❌ Erro ao abrir como 7Z: {e}")
    
    print(f"\n{'='*70}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python diagnostico_arquivo.py <arquivo>")
        print("\nExemplo:")
        print("  python diagnostico_arquivo.py Deathzone_Gunsweeper.rar")
        sys.exit(1)
    
    file_path = sys.argv[1]
    detect_format(file_path)

if __name__ == "__main__":
    main()
