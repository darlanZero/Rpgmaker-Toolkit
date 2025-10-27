#!/usr/bin/env python3
"""
RPG Maker MV/MZ Decrypter - VERSÃO FINAL CORRETA
Baseado na especificação técnica: apenas os primeiros 16 bytes são criptografados

ESTRUTURA DO ARQUIVO:
[Bytes 0-15]   Header RPGMV (16 bytes) - NÃO criptografado
[Bytes 16-31]  Header original do arquivo (16 bytes) - CRIPTOGRAFADO com XOR
[Bytes 32-EOF] Resto do arquivo - NÃO criptografado

Este script implementa a descriptografia correta conforme documentação oficial.
"""

import os
import sys
import json
from pathlib import Path

class RPGMakerDecrypter:
    def __init__(self, game_folder):
        self.game_folder = Path(game_folder)
        self.encryption_key = None
        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Mapeamento de extensões
        self.encrypted_extensions = {
            '.rpgmvp': '.png',
            '.png_': '.png',
            '.rpgmvo': '.ogg',
            '.ogg_': '.ogg',
            '.rpgmvm': '.m4a',
            '.m4a_': '.m4a',
        }
        
        # Assinaturas de arquivo
        self.signatures = {
            '.png': b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
            '.ogg': b'OggS',
            '.m4a': b'\x00\x00\x00\x20\x66\x74\x79\x70'  # ftyp
        }
    
    def load_encryption_key(self):
        """Carrega chave do System.json"""
        system_paths = [
            self.game_folder / 'data' / 'System.json',
            self.game_folder / 'www' / 'data' / 'System.json'
        ]
        
        for system_path in system_paths:
            if system_path.exists():
                try:
                    with open(system_path, 'r', encoding='utf-8') as f:
                        system_data = json.load(f)
                    
                    self.encryption_key = system_data.get('encryptionKey', '')
                    
                    if self.encryption_key:
                        print(f"✅ Chave encontrada: {self.encryption_key}")
                        print(f"📍 Arquivo: {system_path.relative_to(self.game_folder)}")
                        return True
                except Exception as e:
                    print(f"⚠️  Erro ao ler {system_path}: {e}")
        
        print("❌ Chave de criptografia não encontrada!")
        return False
    
    def verify_rpgmv_header(self, data):
        """
        Verifica se o arquivo tem header RPGMV padrão
        Header padrão: 52 50 47 4D 56 00 00 00 00 03 01 00 00 00 00 00
        """
        standard_header = bytes.fromhex("5250474d56000000000301000000000000")
        
        if len(data) < 16:
            return False, "Arquivo muito pequeno"
        
        header = data[:16]
        
        # Verifica se começa com "RPGMV"
        if header[:5] != b'RPGMV':
            return False, f"Header não é RPGMV: {header[:8].hex()}"
        
        # Avisa se não é o header padrão
        if header != standard_header:
            print(f"      ⚠️  Header customizado: {header.hex()}")
        
        return True, "OK"
    
    def decrypt_file(self, input_path, output_path):
        """
        Descriptografa arquivo RPG Maker MV/MZ
        
        IMPLEMENTAÇÃO CORRETA:
        1. Lê arquivo inteiro
        2. Verifica header RPGMV (bytes 0-15)
        3. Extrai bytes 16-31 (header original criptografado)
        4. Faz XOR APENAS desses 16 bytes com a chave
        5. Junta: [header descriptografado] + [resto do arquivo não criptografado]
        """
        try:
            # Lê arquivo
            with open(input_path, 'rb') as f:
                encrypted_data = f.read()
            
            if len(encrypted_data) < 32:
                return False, "Arquivo muito pequeno"
            
            # Verifica header RPGMV
            is_valid, msg = self.verify_rpgmv_header(encrypted_data)
            if not is_valid:
                return False, msg
            
            # Converte chave hex para bytes
            key_bytes = bytes.fromhex(self.encryption_key)
            
            if len(key_bytes) != 16:
                return False, f"Chave inválida (tamanho: {len(key_bytes)})"
            
            # CRÍTICO: Extrai APENAS os 16 bytes criptografados
            rpgmv_header = encrypted_data[0:16]      # Header RPGMV (não usar)
            encrypted_header = encrypted_data[16:32]  # 16 bytes criptografados
            unencrypted_body = encrypted_data[32:]    # Resto (não criptografado)
            
            # XOR nos 16 bytes criptografados
            decrypted_header = bytearray()
            for i in range(16):
                decrypted_header.append(encrypted_header[i] ^ key_bytes[i])
            
            # Reconstrói arquivo: header descriptografado + corpo não criptografado
            final_data = bytes(decrypted_header) + unencrypted_body
            
            # Verifica assinatura
            expected_ext = output_path.suffix
            if expected_ext in self.signatures:
                expected_sig = self.signatures[expected_ext]
                sig_len = len(expected_sig)
                
                if not final_data[:sig_len].startswith(expected_sig):
                    actual_sig = final_data[:sig_len].hex()
                    expected_sig_hex = expected_sig.hex()
                    return False, f"Assinatura inválida: {actual_sig} != {expected_sig_hex}"
            
            # Salva arquivo
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(final_data)
            
            return True, f"{len(final_data)} bytes"
            
        except Exception as e:
            return False, str(e)
    
    def find_encrypted_files(self):
        """Encontra todos os arquivos criptografados"""
        encrypted_files = []
        
        search_folders = ['img', 'audio', 'movies']
        
        for folder_name in search_folders:
            folder_path = self.game_folder / folder_name
            if not folder_path.exists():
                continue
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.suffix in self.encrypted_extensions:
                        encrypted_files.append(file_path)
        
        return encrypted_files
    
    def decrypt_all(self):
        """Descriptografa todos os arquivos"""
        import time
        
        print("\n🔍 Procurando arquivos criptografados...")
        encrypted_files = self.find_encrypted_files()
        
        if not encrypted_files:
            print("❌ Nenhum arquivo criptografado encontrado!")
            return
        
        print(f"📦 Encontrados: {len(encrypted_files)} arquivos")
        
        # Agrupa por pasta
        files_by_folder = {}
        for file_path in encrypted_files:
            folder = file_path.parent
            if folder not in files_by_folder:
                files_by_folder[folder] = []
            files_by_folder[folder].append(file_path)
        
        print(f"📂 Pastas: {len(files_by_folder)}")
        print("\n" + "="*70)
        print("🔓 DESCRIPTOGRAFIA CORRETA: XOR apenas nos primeiros 16 bytes")
        print("="*70)
        
        start_time = time.time()
        current_file = 0
        
        for folder, files in files_by_folder.items():
            relative_folder = folder.relative_to(self.game_folder)
            print(f"\n📁 {relative_folder} ({len(files)} arquivos)")
            
            for file_path in files:
                current_file += 1
                
                # Define arquivo de saída
                output_ext = self.encrypted_extensions[file_path.suffix]
                output_path = file_path.with_suffix(output_ext)
                
                # Progresso
                progress = (current_file / len(encrypted_files)) * 100
                print(f"  [{current_file}/{len(encrypted_files)}] ({progress:.1f}%) ", end='')
                print(f"{file_path.name[:40]:40s} ", end='', flush=True)
                
                # Descriptografa
                success, message = self.decrypt_file(file_path, output_path)
                
                if success:
                    print(f"✅ {message}")
                    self.stats['success'] += 1
                else:
                    print(f"❌ {message}")
                    self.stats['failed'] += 1
        
        # Resumo final
        total_time = time.time() - start_time
        
        print("\n" + "="*70)
        print(f"⏱️  Tempo total: {total_time:.2f}s ({total_time/60:.1f} min)")
        print(f"✅ Sucesso: {self.stats['success']}")
        print(f"❌ Falhas: {self.stats['failed']}")
        print(f"⏭️  Ignorados: {self.stats['skipped']}")
        print("="*70)
        
        if self.stats['failed'] > 0:
            print("\n⚠️  Arquivos com falha podem ter:")
            print("   - Header customizado (verifique rpg_core.js)")
            print("   - Criptografia não-padrão (plugins)")
            print("   - Chave incorreta")
    
    def disable_encryption(self):
        """Desativa flags de criptografia no System.json"""
        system_paths = [
            self.game_folder / 'data' / 'System.json',
            self.game_folder / 'www' / 'data' / 'System.json'
        ]
        
        for system_path in system_paths:
            if system_path.exists():
                try:
                    with open(system_path, 'r', encoding='utf-8') as f:
                        system_data = json.load(f)
                    
                    # Backup
                    backup_path = system_path.with_suffix('.json.backup')
                    if not backup_path.exists():
                        import shutil
                        shutil.copy2(system_path, backup_path)
                        print(f"💾 Backup criado: {backup_path.name}")
                    
                    # Desativa criptografia
                    system_data['hasEncryptedImages'] = False
                    system_data['hasEncryptedAudio'] = False
                    
                    with open(system_path, 'w', encoding='utf-8') as f:
                        json.dump(system_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ {system_path.name} atualizado")
                    
                except Exception as e:
                    print(f"⚠️  Erro ao atualizar {system_path}: {e}")


def main():
    print("="*70)
    print("  RPG Maker MV/MZ Decrypter - VERSÃO FINAL")
    print("  Implementação correta: XOR apenas nos primeiros 16 bytes")
    print("="*70)
    
    if len(sys.argv) < 2:
        print("\n❌ Uso: python rpgmaker_decrypter_FINAL.py /caminho/para/jogo")
        print("\nExemplo:")
        print("  python rpgmaker_decrypter_FINAL.py /sdcard/joiplay/deathzone")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    
    if not os.path.isdir(game_folder):
        print(f"❌ Pasta não encontrada: {game_folder}")
        sys.exit(1)
    
    print(f"\n📁 Jogo: {game_folder}\n")
    
    decrypter = RPGMakerDecrypter(game_folder)
    
    # Carrega chave
    if not decrypter.load_encryption_key():
        print("\n💡 Procure por 'encryptionKey' no arquivo data/System.json")
        sys.exit(1)
    
    # Descriptografa
    decrypter.decrypt_all()
    
    # Desativa criptografia
    print()
    decrypter.disable_encryption()
    
    print("\n🎉 Processo concluído!")
    print("🎮 Agora teste o jogo no JoiPlay")
    print("\n💡 Se ainda houver erros, execute:")
    print("   python verificar_integridade.py /caminho/para/jogo")


if __name__ == "__main__":
    main()
