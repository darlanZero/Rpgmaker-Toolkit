#!/usr/bin/env python3
"""
Restaura arquivos Live2D do arquivo original (ZIP, RAR ou 7Z)
Suporta múltiplos formatos de compressão automaticamente
"""

import sys
import json
import shutil
from pathlib import Path

class Color:
    """Cores ANSI para terminal"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Color.GREEN}✅ {msg}{Color.ENDC}")

def print_error(msg):
    print(f"{Color.RED}❌ {msg}{Color.ENDC}")

def print_warning(msg):
    print(f"{Color.YELLOW}⚠️  {msg}{Color.ENDC}")

def print_info(msg):
    print(f"{Color.CYAN}ℹ️  {msg}{Color.ENDC}")

def detect_archive_type(archive_path):
    """Detecta o tipo de arquivo compactado"""
    archive_path = Path(archive_path)
    
    # Verifica pela extensão
    ext = archive_path.suffix.lower()
    if ext == '.zip':
        return 'zip'
    elif ext in ['.rar', '.cbr']:
        return 'rar'
    elif ext in ['.7z', '.cb7']:
        return '7z'
    
    # Se não conseguiu pela extensão, tenta pelos bytes mágicos
    try:
        with open(archive_path, 'rb') as f:
            magic = f.read(8)
        
        # ZIP: PK\x03\x04
        if magic[:4] == b'PK\x03\x04':
            return 'zip'
        # RAR: Rar!\x1a\x07
        elif magic[:6] == b'Rar!\x1a\x07':
            return 'rar'
        # 7Z: 7z\xbc\xaf\x27\x1c
        elif magic[:6] == b'7z\xbc\xaf\x27\x1c':
            return '7z'
    except:
        pass
    
    return None

def extract_with_zipfile(archive_path):
    """Extrai usando zipfile (ZIP)"""
    from zipfile import ZipFile
    
    # Mantém o ZipFile aberto retornando uma referência
    zf = ZipFile(archive_path, 'r')
    return zf.namelist(), lambda name: zf.open(name).read(), zf

def extract_with_rarfile(archive_path):
    """Extrai usando rarfile (RAR)"""
    try:
        import rarfile
    except ImportError:
        print_error("Biblioteca 'rarfile' não instalada!")
        print_info("Instale com: pip install rarfile --break-system-packages")
        print_info("Ou: pip3 install rarfile --break-system-packages")
        return None, None, None
    
    try:
        rf = rarfile.RarFile(archive_path, 'r')
        return rf.namelist(), lambda name: rf.open(name).read(), rf
    except rarfile.NeedFirstVolume:
        print_error("Arquivo RAR multi-volume detectado!")
        print_info("Certifique-se de ter TODOS os volumes (.part1.rar, .part2.rar, etc)")
        return None, None, None
    except Exception as e:
        print_error(f"Erro ao abrir RAR: {e}")
        return None, None, None

def extract_with_py7zr(archive_path):
    """Extrai usando py7zr (7Z)"""
    try:
        import py7zr
    except ImportError:
        print_error("Biblioteca 'py7zr' não instalada!")
        print_info("Instale com: pip install py7zr --break-system-packages")
        print_info("Ou: pip3 install py7zr --break-system-packages")
        return None, None, None
    
    try:
        sz = py7zr.SevenZipFile(archive_path, 'r')
        return sz.getnames(), lambda name: sz.read([name])[name].read(), sz
    except Exception as e:
        print_error(f"Erro ao abrir 7Z: {e}")
        return None, None, None

def restore_live2d_universal(archive_path, game_folder, encryption_key=None):
    """Restaura arquivos Live2D de qualquer formato de arquivo"""
    
    archive_path = Path(archive_path)
    game_folder = Path(game_folder)
    
    print("="*70)
    print(f"{Color.BOLD}  RESTAURAR ARQUIVOS LIVE2D - UNIVERSAL{Color.ENDC}")
    print("="*70)
    
    # Validações básicas
    if not archive_path.exists():
        print_error(f"Arquivo não encontrado: {archive_path}")
        return False
    
    if not game_folder.exists():
        print_error(f"Pasta do jogo não encontrada: {game_folder}")
        return False
    
    print(f"\n📦 Arquivo: {archive_path.name}")
    print(f"📁 Destino: {game_folder}")
    
    # Detecta tipo de arquivo
    print_info("Detectando tipo de arquivo...")
    archive_type = detect_archive_type(archive_path)
    
    if not archive_type:
        print_error("Não foi possível detectar o tipo de arquivo!")
        print_info("Extensões suportadas: .zip, .rar, .7z")
        return False
    
    print_success(f"Tipo detectado: {archive_type.upper()}")
    
    # Carrega chave de criptografia se não fornecida
    if not encryption_key:
        system_paths = [
            game_folder / 'data' / 'System.json',
            game_folder / 'www' / 'data' / 'System.json'
        ]
        
        for system_path in system_paths:
            if system_path.exists():
                try:
                    with open(system_path, 'r', encoding='utf-8') as f:
                        system_data = json.load(f)
                    encryption_key = system_data.get('encryptionKey', '')
                    if encryption_key:
                        print_success(f"Chave encontrada: {encryption_key}")
                        break
                except:
                    pass
    
    if not encryption_key:
        print_warning("Chave de criptografia não encontrada!")
        print_info("Arquivos criptografados não serão descriptografados")
    
    # Seleciona método de extração
    print_info(f"Abrindo arquivo {archive_type.upper()}...")
    
    archive_handle = None
    
    if archive_type == 'zip':
        file_list, read_func, archive_handle = extract_with_zipfile(archive_path)
    elif archive_type == 'rar':
        file_list, read_func, archive_handle = extract_with_rarfile(archive_path)
    elif archive_type == '7z':
        file_list, read_func, archive_handle = extract_with_py7zr(archive_path)
    else:
        print_error(f"Formato não suportado: {archive_type}")
        return False
    
    if file_list is None or read_func is None:
        return False
    
    # Filtra arquivos Live2D
    live2d_files = [f for f in file_list if 'live2d' in f.lower() and not f.endswith('/')]
    
    if not live2d_files:
        print_error("Nenhum arquivo Live2D encontrado no arquivo!")
        return False
    
    print_success(f"{len(live2d_files)} arquivos Live2D encontrados")
    
    # Agrupa por tipo
    by_extension = {}
    for f in live2d_files:
        ext = Path(f).suffix.lower()
        if ext not in by_extension:
            by_extension[ext] = []
        by_extension[ext].append(f)
    
    print(f"\n📊 Tipos de arquivo encontrados:")
    for ext, files in sorted(by_extension.items()):
        print(f"   {ext:20s}: {len(files):4d} arquivos")
    
    # Processa arquivos
    print(f"\n📤 Extraindo e processando arquivos...")
    
    extracted = 0
    decrypted = 0
    copied = 0
    errors = []
    
    key_bytes = bytes.fromhex(encryption_key) if encryption_key else None
    
    for i, file_path in enumerate(live2d_files, 1):
        try:
            # Determina caminho de destino
            parts = Path(file_path).parts
            if 'img' in parts:
                idx = parts.index('img')
                relative_path = Path(*parts[idx:])
            elif 'www' in parts and 'img' in parts:
                idx = parts.index('www')
                relative_path = Path(*parts[idx+1:])
            else:
                relative_path = Path(file_path)
            
            output_path = game_folder / relative_path
            
            # Cria diretórios
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Lê arquivo
            data = read_func(file_path)
            extracted += 1
            
            # Verifica se precisa descriptografar
            needs_decrypt = False
            if len(data) > 32 and data[:5] == b'RPGMV':
                needs_decrypt = True
            
            # Descriptografa se necessário
            if needs_decrypt and key_bytes:
                # XOR nos bytes 16-31
                encrypted_header = data[16:32]
                unencrypted_body = data[32:]
                
                decrypted_header = bytes([encrypted_header[i] ^ key_bytes[i] for i in range(16)])
                final_data = decrypted_header + unencrypted_body
                
                # Ajusta extensão
                if output_path.suffix in ['.json_', '.rpgmvj']:
                    output_path = output_path.with_suffix('.json')
                elif output_path.suffix in ['.png_', '.rpgmvp']:
                    output_path = output_path.with_suffix('.png')
                elif output_path.suffix in ['.moc_', '.moc3_']:
                    output_path = output_path.with_suffix('.moc3')
                
                data = final_data
                decrypted += 1
            
            # Salva arquivo
            with open(output_path, 'wb') as f:
                f.write(data)
            
            copied += 1
            
            # Mostra progresso a cada 50 arquivos
            if copied % 50 == 0:
                progress = (i / len(live2d_files)) * 100
                print(f"   ⏳ Progresso: {progress:.1f}% ({copied}/{len(live2d_files)})")
        
        except Exception as e:
            errors.append((file_path, str(e)))
    
    # Fecha o arquivo compactado
    if archive_handle is not None:
        try:
            archive_handle.close()
        except:
            pass
    
    # Resultados
    print(f"\n{'='*70}")
    print(f"{Color.BOLD}📊 RESULTADOS:{Color.ENDC}")
    print_success(f"Extraídos: {extracted}")
    print_success(f"Descriptografados: {decrypted}")
    print_success(f"Copiados: {copied}")
    
    if errors:
        print_error(f"Erros: {len(errors)}")
        print(f"\n📋 Primeiros erros:")
        for file_path, error in errors[:5]:
            print(f"   - {Path(file_path).name}: {error}")
        if len(errors) > 5:
            print(f"   ... e mais {len(errors)-5} erros")
    
    print(f"{'='*70}")
    
    if copied > 0:
        print_success("✨ SUCESSO!")
        print_info("Arquivos Live2D restaurados com sucesso!")
        print(f"\n{Color.CYAN}🎮 Agora teste o jogo no JoiPlay{Color.ENDC}")
        print(f"{Color.CYAN}   As animações Live2D devem funcionar!{Color.ENDC}")
        return True
    else:
        print_error("Nenhum arquivo foi copiado")
        return False

def main():
    print(f"{Color.BOLD}{Color.CYAN}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║           RESTAURAR LIVE2D - UNIVERSAL (ZIP/RAR/7Z)              ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{Color.ENDC}")
    
    if len(sys.argv) < 3:
        print("Uso: python restaurar_live2d_universal.py <arquivo> <pasta_jogo> [chave]")
        print("\nExemplos:")
        print("  python restaurar_live2d_universal.py deathzone.zip /sdcard/joiplay/deathzone")
        print("  python restaurar_live2d_universal.py deathzone.rar ~/deathzone")
        print("  python restaurar_live2d_universal.py deathzone.7z /storage/emulated/0/deathzone")
        print("\nFormatos suportados: ZIP, RAR, 7Z")
        print("A chave é opcional - será lida do System.json se não fornecida")
        sys.exit(1)
    
    archive_path = sys.argv[1]
    game_folder = sys.argv[2]
    encryption_key = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Verifica dependências
    archive_type = detect_archive_type(archive_path)
    
    if archive_type == 'rar':
        try:
            import rarfile
        except ImportError:
            print_error("Biblioteca 'rarfile' necessária para arquivos RAR!")
            print_info("Instale com: pip install rarfile --break-system-packages")
            sys.exit(1)
    
    elif archive_type == '7z':
        try:
            import py7zr
        except ImportError:
            print_error("Biblioteca 'py7zr' necessária para arquivos 7Z!")
            print_info("Instale com: pip install py7zr --break-system-packages")
            sys.exit(1)
    
    success = restore_live2d_universal(archive_path, game_folder, encryption_key)
    
    if success:
        print(f"\n💡 DICA: Se o jogo ainda não funcionar:")
        print(f"   1. Force stop no JoiPlay")
        print(f"   2. Limpe o cache do JoiPlay")
        print(f"   3. Reinicie o JoiPlay")
        print(f"   4. Teste novamente")
    else:
        print(f"\n💡 TROUBLESHOOTING:")
        print(f"   • Verifique se o arquivo não está corrompido")
        print(f"   • Tente extrair manualmente para conferir")
        print(f"   • Para RAR: certifique-se de ter todos os volumes")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
