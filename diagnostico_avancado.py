#!/usr/bin/env python3
"""
Diagnóstico Avançado de Criptografia RPG Maker
Identifica o tipo exato de criptografia e problemas
"""

import sys
from pathlib import Path

def analyze_file_deep(file_path, encryption_key=None):
    """Análise profunda de arquivo criptografado"""
    
    print(f"\n{'='*70}")
    print(f"📄 Arquivo: {file_path.name}")
    print(f"{'='*70}")
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"\n📊 Informações básicas:")
    print(f"   Tamanho: {len(data)} bytes")
    print(f"   Extensão: {file_path.suffix}")
    
    # Mostra primeiros 64 bytes
    print(f"\n🔍 Primeiros 64 bytes (hex):")
    for i in range(0, min(64, len(data)), 16):
        hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
        print(f"   {i:04x}  {hex_str:48s}  {ascii_str}")
    
    # Verifica header RPGMV
    print(f"\n🔍 Análise do header:")
    standard_header = bytes.fromhex("5250474d56000000000301000000000000")
    
    if data[:5] == b'RPGMV':
        print(f"   ✅ Header RPGMV detectado")
        
        actual_header = data[:16]
        print(f"   Header completo: {actual_header.hex()}")
        
        if actual_header == standard_header:
            print(f"   ✅ Header PADRÃO (comum)")
        else:
            print(f"   ⚠️  Header CUSTOMIZADO")
            print(f"   Padrão:  {standard_header.hex()}")
            print(f"   Atual:   {actual_header.hex()}")
            print(f"   AÇÃO: Verifique rpg_core.js para valores customizados")
    else:
        print(f"   ❌ Header RPGMV NÃO encontrado")
        print(f"   Primeiros 16 bytes: {data[:16].hex()}")
        print(f"   Este arquivo pode:")
        print(f"      - Já estar descriptografado")
        print(f"      - Usar criptografia customizada")
        print(f"      - Estar corrompido")
    
    # Procura assinaturas de arquivo
    print(f"\n🔍 Procurando assinaturas de arquivo:")
    
    signatures = {
        'PNG': b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
        'OGG': b'OggS',
        'M4A': b'\x00\x00\x00\x20\x66\x74\x79\x70',
        'JPEG': b'\xFF\xD8\xFF',
        'WebP': b'RIFF',
    }
    
    for name, sig in signatures.items():
        pos = data.find(sig)
        if pos >= 0:
            print(f"   ✅ {name} encontrado na posição {pos}")
            if pos == 0:
                print(f"      → Arquivo JÁ descriptografado!")
            elif pos == 16:
                print(f"      → Assinatura após header RPGMV (provável)")
            else:
                print(f"      → Posição incomum")
    
    # Se tem chave, testa XOR
    if encryption_key:
        print(f"\n🧪 Testando descriptografia com chave fornecida:")
        print(f"   Chave: {encryption_key}")
        
        try:
            key_bytes = bytes.fromhex(encryption_key)
            
            # Testa XOR em diferentes posições
            test_positions = [0, 16]
            
            for start_pos in test_positions:
                if start_pos + 16 > len(data):
                    continue
                
                encrypted_chunk = data[start_pos:start_pos+16]
                decrypted_chunk = bytes([encrypted_chunk[i] ^ key_bytes[i] for i in range(16)])
                
                print(f"\n   Posição {start_pos}:")
                print(f"      Criptografado: {encrypted_chunk.hex()}")
                print(f"      Descriptografado: {decrypted_chunk.hex()}")
                
                # Verifica se resultou em assinatura válida
                for name, sig in signatures.items():
                    if decrypted_chunk.startswith(sig[:min(len(sig), 16)]):
                        print(f"      ✅ SUCESSO! Assinatura {name} encontrada!")
                        print(f"      RESULTADO: XOR deve começar no byte {start_pos}")
                        
                        # Mostra próximos bytes
                        if start_pos + 32 <= len(data):
                            next_chunk = data[start_pos+16:start_pos+32]
                            print(f"      Próximos 16 bytes: {next_chunk.hex()}")
                            print(f"      (esses NÃO devem ser criptografados)")
        
        except Exception as e:
            print(f"   ❌ Erro ao testar XOR: {e}")
    
    # Análise de entropia (detecta criptografia)
    print(f"\n📊 Análise de entropia:")
    
    # Calcula entropia dos primeiros 256 bytes
    chunk = data[:min(256, len(data))]
    from collections import Counter
    import math
    
    freq = Counter(chunk)
    entropy = -sum((count/len(chunk)) * math.log2(count/len(chunk)) 
                   for count in freq.values())
    
    print(f"   Entropia: {entropy:.2f} bits/byte")
    print(f"   Interpretação:")
    if entropy > 7.5:
        print(f"      → Alta entropia: dados criptografados ou comprimidos")
    elif entropy > 6:
        print(f"      → Média entropia: dados mistos")
    else:
        print(f"      → Baixa entropia: texto ou dados estruturados")
    
    # Recomendações finais
    print(f"\n💡 Recomendações:")
    
    if data[:5] == b'RPGMV' and encryption_key:
        print(f"   1. Use descriptografia padrão com XOR no offset 16")
        print(f"   2. Chave: {encryption_key}")
        print(f"   3. Execute: python rpgmaker_decrypter_FINAL.py /caminho/jogo")
    elif data[:5] != b'RPGMV':
        print(f"   1. Arquivo pode já estar descriptografado")
        print(f"   2. Ou usa criptografia não-padrão")
        print(f"   3. Verifique js/plugins/ para plugins de criptografia")
    else:
        print(f"   1. Forneça a chave de criptografia para análise completa")
        print(f"   2. Chave está em data/System.json")


def analyze_system_json(game_folder):
    """Analisa System.json"""
    system_paths = [
        Path(game_folder) / 'data' / 'System.json',
        Path(game_folder) / 'www' / 'data' / 'System.json'
    ]
    
    print(f"\n{'='*70}")
    print(f"📋 Análise do System.json")
    print(f"{'='*70}")
    
    for system_path in system_paths:
        if system_path.exists():
            print(f"\n✅ Encontrado: {system_path}")
            
            try:
                import json
                with open(system_path, 'r', encoding='utf-8') as f:
                    system_data = json.load(f)
                
                print(f"\n🔑 Configurações de criptografia:")
                print(f"   hasEncryptedImages: {system_data.get('hasEncryptedImages', False)}")
                print(f"   hasEncryptedAudio: {system_data.get('hasEncryptedAudio', False)}")
                
                key = system_data.get('encryptionKey', '')
                if key:
                    print(f"   encryptionKey: {key}")
                    print(f"   Tamanho da chave: {len(key)} caracteres ({len(key)//2} bytes)")
                else:
                    print(f"   ❌ Chave não encontrada!")
                
                return key
                
            except Exception as e:
                print(f"   ❌ Erro ao ler: {e}")
    
    print(f"\n❌ System.json não encontrado em nenhuma localização padrão")
    return None


def check_rpg_core_js(game_folder):
    """Verifica se rpg_core.js tem valores customizados"""
    core_paths = [
        Path(game_folder) / 'js' / 'rpg_core.js',
        Path(game_folder) / 'www' / 'js' / 'rpg_core.js'
    ]
    
    print(f"\n{'='*70}")
    print(f"🔍 Verificando rpg_core.js")
    print(f"{'='*70}")
    
    for core_path in core_paths:
        if core_path.exists():
            print(f"\n✅ Encontrado: {core_path}")
            
            try:
                with open(core_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Procura pela classe Decrypter
                if 'Decrypter' in content:
                    print(f"\n🔍 Procurando valores customizados:")
                    
                    # Extrai linhas relevantes
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if any(keyword in line for keyword in 
                               ['_headerlength', 'SIGNATURE', '.VER', '.REMAIN']):
                            print(f"   {line.strip()}")
                
            except Exception as e:
                print(f"   ❌ Erro ao ler: {e}")


def main():
    print("="*70)
    print("  Diagnóstico Avançado RPG Maker MV/MZ")
    print("="*70)
    
    if len(sys.argv) < 2:
        print("\n❌ Uso: python diagnostico_avancado.py /caminho/jogo [arquivo_teste]")
        print("\nExemplos:")
        print("  python diagnostico_avancado.py /sdcard/joiplay/deathzone")
        print("  python diagnostico_avancado.py /sdcard/joiplay/deathzone img/system/Window.png_")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    
    if not Path(game_folder).exists():
        print(f"❌ Pasta não encontrada: {game_folder}")
        sys.exit(1)
    
    print(f"\n📁 Jogo: {game_folder}")
    
    # Analisa System.json
    encryption_key = analyze_system_json(game_folder)
    
    # Verifica rpg_core.js
    check_rpg_core_js(game_folder)
    
    # Se foi fornecido arquivo específico, analisa
    if len(sys.argv) > 2:
        test_file = Path(sys.argv[2])
        if not test_file.exists():
            # Tenta relativo à pasta do jogo
            test_file = Path(game_folder) / sys.argv[2]
        
        if test_file.exists():
            analyze_file_deep(test_file, encryption_key)
        else:
            print(f"\n❌ Arquivo não encontrado: {sys.argv[2]}")
    else:
        # Procura um arquivo de exemplo
        print(f"\n🔍 Procurando arquivo de exemplo para análise...")
        
        test_paths = [
            'img/system/Window.png_',
            'img/system/Window.rpgmvp',
            'audio/bgm/*.ogg_',
            'audio/bgm/*.rpgmvo'
        ]
        
        for pattern in test_paths:
            from glob import glob
            matches = glob(str(Path(game_folder) / pattern))
            if matches:
                analyze_file_deep(Path(matches[0]), encryption_key)
                break
        else:
            print(f"   ⚠️  Nenhum arquivo criptografado encontrado para análise")
            print(f"   Execute: python diagnostico_avancado.py {game_folder} caminho/arquivo.png_")
    
    print(f"\n{'='*70}")
    print(f"✅ Diagnóstico concluído")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
