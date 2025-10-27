#!/usr/bin/env python3
"""
Teste Rápido - Verifica se o jogo já foi descriptografado
"""

import sys
from pathlib import Path
import json

def check_game_status(game_folder):
    """Verifica status de criptografia do jogo"""
    game_folder = Path(game_folder)
    
    print("="*70)
    print("  VERIFICAÇÃO RÁPIDA DE STATUS")
    print("="*70)
    print(f"\n📁 Jogo: {game_folder}\n")
    
    # Verifica System.json
    system_paths = [
        game_folder / 'data' / 'System.json',
        game_folder / 'www' / 'data' / 'System.json'
    ]
    
    system_data = None
    for system_path in system_paths:
        if system_path.exists():
            try:
                with open(system_path, 'r', encoding='utf-8') as f:
                    system_data = json.load(f)
                print(f"✅ System.json encontrado")
                break
            except:
                pass
    
    if not system_data:
        print("❌ System.json não encontrado!")
        return
    
    # Status de criptografia
    has_encrypted_images = system_data.get('hasEncryptedImages', False)
    has_encrypted_audio = system_data.get('hasEncryptedAudio', False)
    encryption_key = system_data.get('encryptionKey', '')
    
    print(f"\n📊 Status de criptografia:")
    print(f"   hasEncryptedImages: {has_encrypted_images}")
    print(f"   hasEncryptedAudio:  {has_encrypted_audio}")
    
    if encryption_key:
        print(f"   Chave: {encryption_key}")
    
    # Conta arquivos
    encrypted_count = 0
    decrypted_count = 0
    
    encrypted_exts = ['.png_', '.ogg_', '.rpgmvp', '.rpgmvo', '.rpgmvm']
    decrypted_exts = ['.png', '.ogg', '.m4a']
    
    print(f"\n🔍 Contando arquivos...")
    
    for root, dirs, files in game_folder.rglob('*'):
        if root.is_file():
            if any(str(root).endswith(ext) for ext in encrypted_exts):
                encrypted_count += 1
            elif any(str(root).endswith(ext) for ext in decrypted_exts):
                if 'img/' in str(root) or 'audio/' in str(root):
                    decrypted_count += 1
    
    print(f"\n📦 Arquivos encontrados:")
    print(f"   Criptografados: {encrypted_count}")
    print(f"   Descriptografados: {decrypted_count}")
    
    # Determina status
    print(f"\n{'='*70}")
    
    if encrypted_count > 0:
        print("🔒 STATUS: CRIPTOGRAFADO")
        print(f"\n💡 AÇÃO RECOMENDADA:")
        print(f"   python decrypt_all_in_one.py {game_folder}")
    elif decrypted_count > 0:
        if has_encrypted_images or has_encrypted_audio:
            print("⚠️  STATUS: PARCIALMENTE DESCRIPTOGRAFADO")
            print(f"\n💡 AÇÃO RECOMENDADA:")
            print(f"   1. Flags de criptografia ainda ativas!")
            print(f"   2. Execute: python decrypt_all_in_one.py {game_folder}")
            print(f"   3. Ou desative manualmente no System.json")
        else:
            print("✅ STATUS: DESCRIPTOGRAFADO E PRONTO!")
            print(f"\n🎮 Você pode jogar no JoiPlay agora!")
    else:
        print("❓ STATUS: INCERTO")
        print(f"\n💡 Nenhum arquivo de mídia encontrado")
    
    print(f"{'='*70}")


def main():
    if len(sys.argv) < 2:
        print("❌ Uso: python teste_rapido.py /caminho/para/jogo")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    
    if not Path(game_folder).is_dir():
        print(f"❌ Pasta não encontrada: {game_folder}")
        sys.exit(1)
    
    check_game_status(game_folder)


if __name__ == "__main__":
    main()
