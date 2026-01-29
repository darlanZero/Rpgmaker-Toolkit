#!/usr/bin/env python3
"""
RPG Maker Decrypter ALL-IN-ONE
Diagnóstico + Descriptografia + Verificação em um único comando
"""

import os
import sys
import json
from pathlib import Path
from collections import Counter
import math

class Color:
    """Cores ANSI para terminal"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class RPGMakerDecrypterAllInOne:
    def __init__(self, game_folder):
        self.game_folder = Path(game_folder)
        self.encryption_key = None
        self.stats = {
            'success': 0,
            'failed': 0,
            'corrupted': 0
        }
        
        self.encrypted_extensions = {
            '.rpgmvp': '.png',
            '.png_': '.png',
            '.rpgmvo': '.ogg',
            '.ogg_': '.ogg',
            '.rpgmvm': '.m4a',
            '.m4a_': '.m4a',
        }
        
        self.signatures = {
            '.png': b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A',
            '.ogg': b'OggS',
            '.m4a': b'\x00\x00\x00\x20\x66\x74\x79\x70'
        }
    
    def print_header(self, title):
        """Imprime cabeçalho formatado"""
        print(f"\n{Color.BOLD}{'='*70}{Color.ENDC}")
        print(f"{Color.BOLD}{Color.CYAN}{title:^70}{Color.ENDC}")
        print(f"{Color.BOLD}{'='*70}{Color.ENDC}\n")
    
    def print_success(self, msg):
        print(f"{Color.GREEN}✅ {msg}{Color.ENDC}")
    
    def print_error(self, msg):
        print(f"{Color.RED}❌ {msg}{Color.ENDC}")
    
    def print_warning(self, msg):
        print(f"{Color.YELLOW}⚠️  {msg}{Color.ENDC}")
    
    def print_info(self, msg):
        print(f"{Color.CYAN}ℹ️  {msg}{Color.ENDC}")
    
    def diagnose_system_json(self):
        """Fase 1: Diagnóstico do System.json"""
        self.print_header("FASE 1: DIAGNÓSTICO")
        
        system_paths = [
            self.game_folder / 'data' / 'System.json',
            self.game_folder / 'www' / 'data' / 'System.json'
        ]
        
        print("🔍 Procurando System.json...")
        
        for system_path in system_paths:
            if system_path.exists():
                self.print_success(f"Encontrado: {system_path.relative_to(self.game_folder)}")
                
                try:
                    with open(system_path, 'r', encoding='utf-8') as f:
                        system_data = json.load(f)
                    
                    has_encrypted_images = system_data.get('hasEncryptedImages', False)
                    has_encrypted_audio = system_data.get('hasEncryptedAudio', False)
                    self.encryption_key = system_data.get('encryptionKey', '')
                    
                    print(f"\n📊 Configurações de criptografia:")
                    print(f"   Imagens criptografadas: {has_encrypted_images}")
                    print(f"   Áudio criptografado: {has_encrypted_audio}")
                    
                    if self.encryption_key:
                        self.print_success(f"Chave encontrada: {self.encryption_key}")
                        print(f"   Tamanho: {len(self.encryption_key)} chars ({len(self.encryption_key)//2} bytes)")
                        return True
                    else:
                        self.print_error("Chave de criptografia não encontrada!")
                        return False
                    
                except Exception as e:
                    self.print_error(f"Erro ao ler System.json: {e}")
                    return False
        
        self.print_error("System.json não encontrado!")
        return False
    
    def diagnose_sample_file(self):
        """Analisa um arquivo de exemplo"""
        print("\n🔍 Procurando arquivo de exemplo...")
        
        # Procura arquivo .png_ ou .rpgmvp
        search_paths = [
            'img/system/*.png_',
            'img/system/*.rpgmvp',
            'img/pictures/*.png_',
            'img/pictures/*.rpgmvp'
        ]
        
        from glob import glob
        
        for pattern in search_paths:
            matches = glob(str(self.game_folder / pattern))
            if matches:
                sample_file = Path(matches[0])
                self.print_success(f"Arquivo de exemplo: {sample_file.name}")
                
                with open(sample_file, 'rb') as f:
                    data = f.read()
                
                print(f"\n📊 Análise:")
                print(f"   Tamanho: {len(data)} bytes")
                print(f"   Primeiros 16 bytes: {data[:16].hex()}")
                
                # Verifica header RPGMV
                if data[:5] == b'RPGMV':
                    self.print_success("Header RPGMV detectado")
                    
                    standard_header = bytes.fromhex("5250474d56000000000301000000000000")
                    if data[:16] == standard_header:
                        self.print_success("Header PADRÃO (comum)")
                    else:
                        self.print_warning("Header CUSTOMIZADO")
                        print(f"   Esperado: {standard_header.hex()}")
                        print(f"   Atual:    {data[:16].hex()}")
                else:
                    self.print_error("Header RPGMV não encontrado!")
                
                # Testa XOR
                if self.encryption_key:
                    key_bytes = bytes.fromhex(self.encryption_key)
                    encrypted_header = data[16:32]
                    decrypted_header = bytes([encrypted_header[i] ^ key_bytes[i] for i in range(16)])
                    
                    print(f"\n🧪 Teste de XOR:")
                    print(f"   Criptografado:     {encrypted_header.hex()}")
                    print(f"   Descriptografado:  {decrypted_header.hex()}")
                    
                    # Verifica se deu certo
                    if decrypted_header.startswith(self.signatures['.png']):
                        self.print_success("XOR funcionou! Assinatura PNG válida")
                        return True
                    else:
                        self.print_error("XOR não produziu assinatura válida")
                        return False
                
                return True
        
        self.print_warning("Nenhum arquivo de exemplo encontrado")
        return True
    
    def decrypt_all_files(self):
        """Fase 2: Descriptografia"""
        self.print_header("FASE 2: DESCRIPTOGRAFIA")
        
        print("🔍 Procurando arquivos criptografados...")
        
        encrypted_files = []
        for ext in self.encrypted_extensions:
            for root, dirs, files in os.walk(self.game_folder):
                for file in files:
                    if file.endswith(ext):
                        encrypted_files.append(Path(root) / file)
        
        if not encrypted_files:
            self.print_warning("Nenhum arquivo criptografado encontrado!")
            return
        
        total = len(encrypted_files)
        self.print_info(f"Encontrados {total} arquivos para descriptografar")
        
        print(f"\n🔓 Iniciando descriptografia...")
        print(f"   Método: XOR apenas nos bytes 16-31")
        print(f"   Chave: {self.encryption_key[:16]}...\n")
        
        import time
        start_time = time.time()
        
        key_bytes = bytes.fromhex(self.encryption_key)
        
        for i, file_path in enumerate(encrypted_files, 1):
            progress = (i / total) * 100
            print(f"  [{i}/{total}] ({progress:.1f}%) {file_path.name[:40]:40s} ", end='', flush=True)
            
            try:
                # Lê arquivo
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                if len(data) < 32:
                    self.print_error("muito pequeno")
                    self.stats['failed'] += 1
                    continue
                
                # Verifica header RPGMV
                if data[:5] != b'RPGMV':
                    self.print_warning("sem header RPGMV")
                    self.stats['failed'] += 1
                    continue
                
                # DESCRIPTOGRAFIA CORRETA:
                # XOR apenas nos bytes 16-31
                encrypted_header = data[16:32]
                unencrypted_body = data[32:]
                
                decrypted_header = bytes([encrypted_header[i] ^ key_bytes[i] for i in range(16)])
                
                # Arquivo final
                final_data = decrypted_header + unencrypted_body
                
                # Verifica assinatura
                output_ext = self.encrypted_extensions[file_path.suffix]
                expected_sig = self.signatures.get(output_ext)
                
                if expected_sig and not final_data.startswith(expected_sig):
                    self.print_error(f"assinatura inválida")
                    self.stats['failed'] += 1
                    continue
                
                # Salva
                output_path = file_path.with_suffix(output_ext)
                with open(output_path, 'wb') as f:
                    f.write(final_data)
                
                self.print_success(f"{len(final_data)} bytes")
                self.stats['success'] += 1
                
            except Exception as e:
                self.print_error(str(e))
                self.stats['failed'] += 1
        
        elapsed = time.time() - start_time
        
        print(f"\n{'─'*70}")
        print(f"⏱️  Tempo: {elapsed:.2f}s ({elapsed/60:.1f} min)")
        self.print_success(f"Descriptografados: {self.stats['success']}")
        if self.stats['failed'] > 0:
            self.print_error(f"Falhas: {self.stats['failed']}")
        print(f"{'─'*70}")
    
    def verify_integrity(self):
        """Fase 3: Verificação"""
        self.print_header("FASE 3: VERIFICAÇÃO DE INTEGRIDADE")
        
        print("🔍 Verificando arquivos descriptografados...\n")
        
        corrupted = []
        valid = 0
        
        # Verifica PNGs
        for root, dirs, files in os.walk(self.game_folder):
            for file in files:
                if file.endswith('.png'):
                    png_path = Path(root) / file
                    
                    try:
                        with open(png_path, 'rb') as f:
                            header = f.read(8)
                        
                        if header != self.signatures['.png']:
                            corrupted.append(png_path)
                        else:
                            valid += 1
                    except:
                        corrupted.append(png_path)
        
        # Verifica OGGs
        for root, dirs, files in os.walk(self.game_folder):
            for file in files:
                if file.endswith('.ogg'):
                    ogg_path = Path(root) / file
                    
                    try:
                        with open(ogg_path, 'rb') as f:
                            header = f.read(4)
                        
                        if header != self.signatures['.ogg']:
                            corrupted.append(ogg_path)
                        else:
                            valid += 1
                    except:
                        corrupted.append(ogg_path)
        
        print(f"{'─'*70}")
        self.print_success(f"Arquivos válidos: {valid}")
        
        if corrupted:
            self.print_error(f"Arquivos corrompidos: {len(corrupted)}")
            print(f"\n📋 Lista de corrompidos:")
            for f in corrupted[:10]:  # Mostra apenas os 10 primeiros
                print(f"   - {f.relative_to(self.game_folder)}")
            if len(corrupted) > 10:
                print(f"   ... e mais {len(corrupted)-10} arquivos")
        else:
            self.print_success("Todos os arquivos estão íntegros!")
        
        print(f"{'─'*70}")
        
        self.stats['corrupted'] = len(corrupted)
    
    def disable_encryption(self):
        """Desativa criptografia no System.json"""
        print("\n🔧 Desativando flags de criptografia...")
        
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
                        self.print_success(f"Backup: {backup_path.name}")
                    
                    # Desativa
                    system_data['hasEncryptedImages'] = False
                    system_data['hasEncryptedAudio'] = False
                    
                    with open(system_path, 'w', encoding='utf-8') as f:
                        json.dump(system_data, f, ensure_ascii=False, indent=2)
                    
                    self.print_success("System.json atualizado")
                    
                except Exception as e:
                    self.print_error(f"Erro: {e}")
    
    def run(self):
        """Executa todo o processo"""
        self.print_header("RPG MAKER DECRYPTER ALL-IN-ONE")
        
        print(f"📁 Jogo: {self.game_folder}\n")
        
        # Fase 1: Diagnóstico
        if not self.diagnose_system_json():
            print(f"\n{Color.RED}{'='*70}{Color.ENDC}")
            print(f"{Color.RED}❌ ERRO: Não foi possível encontrar a chave de criptografia{Color.ENDC}")
            print(f"{Color.RED}{'='*70}{Color.ENDC}")
            return False
        
        self.diagnose_sample_file()
        
        # Fase 2: Descriptografia
        self.decrypt_all_files()
        
        # Fase 3: Verificação
        self.verify_integrity()
        
        # Desativa criptografia
        self.disable_encryption()
        
        # Resumo final
        self.print_header("RESUMO FINAL")
        
        print(f"📊 Estatísticas:")
        self.print_success(f"Descriptografados: {self.stats['success']}")
        
        if self.stats['failed'] > 0:
            self.print_error(f"Falhas: {self.stats['failed']}")
        
        if self.stats['corrupted'] > 0:
            self.print_error(f"Corrompidos: {self.stats['corrupted']}")
        
        print(f"\n{'='*70}")
        
        if self.stats['failed'] == 0 and self.stats['corrupted'] == 0:
            self.print_success("✨ SUCESSO TOTAL! ✨")
            print(f"\n{Color.GREEN}🎮 Agora você pode testar o jogo no JoiPlay!{Color.ENDC}")
            return True
        else:
            self.print_warning("⚠️  Processo concluído com alguns erros")
            print(f"\n{Color.YELLOW}💡 Execute novamente se necessário{Color.ENDC}")
            return False


def main():
    print(f"{Color.BOLD}{Color.CYAN}{'='*70}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.CYAN}{'RPG MAKER DECRYPTER ALL-IN-ONE':^70}{Color.ENDC}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*70}{Color.ENDC}\n")

    # Verifica se foi passado como argumento ou pergunta interativamente
    if len(sys.argv) >= 2:
        game_folder = sys.argv[1]
    else:
        print(f"{Color.YELLOW}📁 Nenhum diretório especificado como argumento.{Color.ENDC}\n")
        game_folder = input(f"{Color.CYAN}Digite o caminho completo do jogo: {Color.ENDC}").strip()

        # Remove aspas se o usuário colocar
        if game_folder.startswith('"') and game_folder.endswith('"'):
            game_folder = game_folder[1:-1]
        if game_folder.startswith("'") and game_folder.endswith("'"):
            game_folder = game_folder[1:-1]

    if not game_folder:
        print(f"{Color.RED}❌ Nenhum diretório informado!{Color.ENDC}")
        sys.exit(1)

    if not os.path.isdir(game_folder):
        print(f"{Color.RED}❌ Pasta não encontrada: {game_folder}{Color.ENDC}")
        sys.exit(1)

    print(f"\n{Color.GREEN}✅ Diretório válido: {game_folder}{Color.ENDC}\n")

    decrypter = RPGMakerDecrypterAllInOne(game_folder)
    success = decrypter.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
