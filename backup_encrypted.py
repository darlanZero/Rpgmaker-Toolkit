#!/usr/bin/env python3
"""
Move arquivos .png_ e .ogg_ para pasta de backup
"""

import os
import sys
import shutil
from pathlib import Path

def backup_encrypted_files(game_folder):
    game_folder = Path(game_folder)
    backup_folder = game_folder / '_backup_encrypted'
    
    print("="*60)
    print("  Backup de Arquivos Criptografados")
    print("="*60)
    print(f"\n📁 Jogo: {game_folder}")
    print(f"💾 Backup: {backup_folder}\n")
    
    # Cria pasta de backup
    backup_folder.mkdir(exist_ok=True)
    
    moved_count = 0
    
    # Procura arquivos criptografados
    extensions = ['.png_', '.ogg_', '.rpgmvp', '.rpgmvo', '.rpgmvm']
    
    for ext in extensions:
        print(f"\n🔍 Procurando arquivos {ext}...")
        
        for root, dirs, files in os.walk(game_folder):
            root_path = Path(root)
            
            # Não procurar na pasta de backup
            if '_backup_encrypted' in root_path.parts:
                continue
            
            for file in files:
                if file.endswith(ext):
                    source = root_path / file
                    
                    # Mantém estrutura de pastas no backup
                    relative = source.relative_to(game_folder)
                    destination = backup_folder / relative
                    
                    # Cria subpastas se necessário
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move o arquivo
                    try:
                        shutil.move(str(source), str(destination))
                        print(f"  ✅ {relative}")
                        moved_count += 1
                    except Exception as e:
                        print(f"  ❌ {relative} - Erro: {e}")
    
    print(f"\n{'='*60}")
    print(f"📦 Total de arquivos movidos: {moved_count}")
    print(f"💾 Backup salvo em: {backup_folder}")
    print(f"{'='*60}")
    
    if moved_count > 0:
        print(f"\n✅ Backup concluído!")
        print(f"🎮 Agora você pode testar o jogo no JoiPlay")
        print(f"\n💡 Se precisar restaurar os arquivos originais:")
        print(f"   cp -r '{backup_folder}'/* '{game_folder}'/")
    else:
        print(f"\n⚠️  Nenhum arquivo criptografado encontrado")

def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python backup_encrypted.py /caminho/jogo")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    
    if not os.path.isdir(game_folder):
        print(f"❌ Pasta não encontrada: {game_folder}")
        sys.exit(1)
    
    backup_encrypted_files(game_folder)

if __name__ == "__main__":
    main()
