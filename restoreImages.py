#!/usr/bin/env python3
"""
Restaurador de Imagens Traduzidas
Versão Python com GUI (Tkinter)
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from tkinter import Tk, messagebox, filedialog


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


class ImageRestorer:
    def __init__(self):
        self.output_dir = None
        self.source_dir = None
        self.translated_dir = None
        self.config = None
        self.mapping = {}
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff')

    def select_folder(self, title):
        """Abre diálogo para selecionar pasta"""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        folder = filedialog.askdirectory(title=title)

        root.destroy()
        return folder if folder else None

    def ask_yes_no(self, title, question):
        """Mostra diálogo de confirmação Sim/Não"""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        result = messagebox.askyesno(title, question)

        root.destroy()
        return result

    def load_config(self):
        """Carrega configuração do JSON"""
        config_file = Path(self.output_dir) / "translation_config.json"

        if not config_file.exists():
            print(f"\n{Color.RED}X Arquivo de configuração não encontrado!{Color.ENDC}")
            print(f"{Color.RED}X Esperado em: {config_file}{Color.ENDC}")
            print(f"\n{Color.YELLOW}Certifique-se de que:{Color.ENDC}")
            print("1. Este é o mesmo diretório usado no collectImages.py")
            print("2. O arquivo translation_config.json não foi deletado")
            return False

        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.source_dir = Path(self.config['sourceDirectory'])
        self.mapping = self.config.get('mapping', {})

        return True

    def get_translated_files(self):
        """Obtém lista de arquivos traduzidos"""
        files = []

        for file in Path(self.translated_dir).iterdir():
            if file.is_file() and file.suffix.lower() in self.image_extensions:
                files.append(file)

        return files

    def restore_images(self, translated_files, create_backup):
        """Restaura imagens para os locais originais"""
        total = len(translated_files)
        restored = 0
        not_found = []
        backup_count = 0

        for i, file in enumerate(translated_files, 1):
            # Busca o caminho original
            original_relative_path = self.mapping.get(file.name)

            if original_relative_path:
                original_full_path = self.source_dir / original_relative_path

                # Cria backup se necessário
                if create_backup and original_full_path.exists():
                    backup_path = original_full_path.with_suffix(original_full_path.suffix + '.backup')

                    # Se já existe backup, não sobrescreve
                    if not backup_path.exists():
                        shutil.copy2(original_full_path, backup_path)
                        backup_count += 1

                # Garante que o diretório de destino existe
                original_full_path.parent.mkdir(parents=True, exist_ok=True)

                # Copia o arquivo traduzido de volta
                shutil.copy2(file, original_full_path)
                restored += 1

                # Mostra progresso
                progress = (i / total) * 100
                print(f"\r  [{i}/{total}] ({progress:.1f}%) Restaurando... ", end='', flush=True)
            else:
                not_found.append(file.name)

        print(f"\r  [{total}/{total}] (100.0%) Concluído!          ")

        return restored, not_found, backup_count

    def run(self):
        """Executa o processo completo"""
        print(f"{Color.CYAN}{'='*60}{Color.ENDC}")
        print(f"{Color.CYAN}{'RESTAURADOR DE IMAGENS TRADUZIDAS':^60}{Color.ENDC}")
        print(f"{Color.CYAN}{'='*60}{Color.ENDC}\n")

        # Seleciona diretório de output
        print(f"{Color.YELLOW}Selecione o diretório onde estão as imagens ANINHADAS{Color.ENDC}")
        print("(O mesmo diretório escolhido como saída no collectImages.py)")

        self.output_dir = self.select_folder("Selecione o diretório com as imagens aninhadas")

        if not self.output_dir:
            print(f"{Color.RED}X Operação cancelada pelo usuário{Color.ENDC}")
            return False

        self.output_dir = Path(self.output_dir)

        # Carrega configuração
        if not self.load_config():
            return False

        # Mostra configuração carregada
        print(f"\n{Color.GREEN}=== CONFIGURAÇÃO CARREGADA ==={Color.ENDC}")
        print(f"Diretório original do jogo: {self.source_dir}")
        print(f"Total de imagens coletadas: {self.config.get('totalImages', 'N/A')}")
        print(f"Data da coleta: {self.config.get('collectionDate', 'N/A')}")

        # Pergunta se as imagens foram traduzidas
        was_translated = self.ask_yes_no(
            "Confirmação",
            f"As imagens foram TRADUZIDAS?\n\n"
            f"SIM = Buscar em '{self.output_dir}\\translated'\n"
            f"NÃO = Usar imagens de '{self.output_dir}'"
        )

        # Define o diretório de imagens traduzidas
        if was_translated:
            self.translated_dir = self.output_dir / "translated"

            if not self.translated_dir.exists():
                print(f"\n{Color.RED}X Pasta 'translated' não encontrada!{Color.ENDC}")
                print(f"{Color.RED}X Esperado em: {self.translated_dir}{Color.ENDC}")
                return False

            print(f"\n{Color.GREEN}Usando imagens de: {self.translated_dir}{Color.ENDC}")
        else:
            self.translated_dir = self.output_dir
            print(f"\n{Color.GREEN}Usando imagens de: {self.translated_dir}{Color.ENDC}")

        # Pergunta se quer criar backup
        create_backup = self.ask_yes_no(
            "Confirmação",
            "Deseja criar BACKUP das imagens originais antes de sobrescrever?\n\n(Recomendado: SIM)"
        )

        # Obtém arquivos traduzidos
        translated_files = self.get_translated_files()

        if not translated_files:
            print(f"\n{Color.RED}X Nenhuma imagem encontrada em: {self.translated_dir}{Color.ENDC}")
            return False

        print(f"\n{Color.CYAN}=== RESTAURANDO IMAGENS ==={Color.ENDC}")
        print(f"Encontradas {len(translated_files)} imagens para restaurar\n")

        # Restaura imagens
        restored, not_found, backup_count = self.restore_images(translated_files, create_backup)

        # Resultado final
        print(f"\n{Color.GREEN}=== CONCLUÍDO ==={Color.ENDC}")
        print(f"{Color.GREEN}Restauradas: {restored} de {len(translated_files)} imagens{Color.ENDC}")

        if create_backup:
            print(f"{Color.GREEN}Backups criados: {backup_count} arquivos (.backup){Color.ENDC}")

        if not_found:
            print(f"\n{Color.YELLOW}ATENÇÃO: Arquivos não encontrados no mapeamento:{Color.ENDC}")
            for name in not_found[:10]:
                print(f"  - {name}")
            if len(not_found) > 10:
                print(f"  ... e mais {len(not_found) - 10} arquivos")
            print(f"\n{Color.YELLOW}Estes arquivos não foram restaurados (não estavam na coleta original){Color.ENDC}")

        print(f"\n{Color.GREEN}Imagens restauradas em: {self.source_dir}{Color.ENDC}")

        # Pergunta se quer abrir o diretório
        if self.ask_yes_no("Confirmação", "Deseja abrir o diretório do jogo?"):
            try:
                if sys.platform == 'win32':
                    os.startfile(self.source_dir)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', self.source_dir])
                else:
                    subprocess.run(['xdg-open', self.source_dir])
            except Exception:
                pass

        return True


def main():
    restorer = ImageRestorer()
    success = restorer.run()

    input(f"\n{Color.CYAN}Pressione Enter para sair...{Color.ENDC}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
