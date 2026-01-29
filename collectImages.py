#!/usr/bin/env python3
"""
Coletor de Imagens para Batch Translation
Versão Python com GUI (Tkinter)
"""

import os
import sys
import json
import shutil
import re
import subprocess
from pathlib import Path
from datetime import datetime
from tkinter import Tk, Toplevel, Label, Button, Entry, Listbox, Scrollbar
from tkinter import filedialog, messagebox
from tkinter import END, MULTIPLE, VERTICAL, RIGHT, LEFT, Y, BOTH, X, BOTTOM, TOP


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


class ImageCollector:
    def __init__(self):
        self.source_dir = None
        self.output_dir = None
        self.excluded_dirs = []
        self.image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff')

        # Opções padrão de exclusão
        self.exclusion_options = [
            "particles",
            "parallaxes",
            "tilesets",
            "characters",
            "actors",
            "animations",
            "battlebacks1",
            "battlebacks2",
            "enemies",
            "sv_actors",
            "sv_enemies",
            "system",
            "tiles"
        ]

        # Exclusões pré-marcadas por padrão
        self.default_exclusions = ["particles", "parallaxes", "tilesets", "characters", "actors"]

    def select_folder(self, title):
        """Abre diálogo para selecionar pasta"""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        folder = filedialog.askdirectory(title=title)

        root.destroy()
        return folder if folder else None

    def show_exclusion_dialog(self):
        """Mostra diálogo de seleção de exclusões"""
        result = {'selected': None, 'cancelled': False}

        root = Tk()
        root.title("Selecione pastas para EXCLUIR")
        root.geometry("450x550")
        root.resizable(False, False)

        # Centraliza a janela
        root.eval('tk::PlaceWindow . center')

        # Label de instrução
        label = Label(
            root,
            text="Marque os subdiretórios que NÃO contêm texto para tradução:\n(Imagens dessas pastas serão IGNORADAS)",
            justify=LEFT,
            pady=10,
            padx=10
        )
        label.pack(fill=X)

        # Frame para Listbox com scrollbar
        from tkinter import Frame
        list_frame = Frame(root)
        list_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        scrollbar = Scrollbar(list_frame, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)

        listbox = Listbox(
            list_frame,
            selectmode=MULTIPLE,
            yscrollcommand=scrollbar.set,
            height=15
        )
        listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Adiciona opções
        for option in self.exclusion_options:
            listbox.insert(END, option)

        # Pré-seleciona exclusões padrão
        for i, option in enumerate(self.exclusion_options):
            if option in self.default_exclusions:
                listbox.selection_set(i)

        # Frame para adicionar exclusão customizada
        custom_frame = Frame(root)
        custom_frame.pack(fill=X, padx=10, pady=5)

        Label(custom_frame, text="Adicionar pasta customizada:").pack(anchor='w')

        entry_frame = Frame(custom_frame)
        entry_frame.pack(fill=X, pady=5)

        custom_entry = Entry(entry_frame)
        custom_entry.pack(side=LEFT, fill=X, expand=True)

        def add_custom():
            custom_text = custom_entry.get().strip()
            if custom_text:
                listbox.insert(END, custom_text)
                listbox.selection_set(END)
                custom_entry.delete(0, END)

        add_btn = Button(entry_frame, text="Adicionar", command=add_custom, width=10)
        add_btn.pack(side=LEFT, padx=(5, 0))

        # Botões OK e Cancelar
        btn_frame = Frame(root)
        btn_frame.pack(fill=X, padx=10, pady=15)

        def on_ok():
            selected_indices = listbox.curselection()
            result['selected'] = [listbox.get(i) for i in selected_indices]
            root.destroy()

        def on_cancel():
            result['cancelled'] = True
            root.destroy()

        Button(btn_frame, text="Cancelar", command=on_cancel, width=12).pack(side=RIGHT, padx=5)
        Button(btn_frame, text="OK", command=on_ok, width=12).pack(side=RIGHT, padx=5)

        # Bind Enter para OK
        root.bind('<Return>', lambda e: on_ok())
        root.bind('<Escape>', lambda e: on_cancel())

        root.protocol("WM_DELETE_WINDOW", on_cancel)
        root.mainloop()

        if result['cancelled']:
            return None
        return result['selected']

    def collect_images(self):
        """Coleta todas as imagens do diretório fonte"""
        all_images = []

        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                if file.lower().endswith(self.image_extensions):
                    all_images.append(Path(root) / file)

        return all_images

    def filter_images(self, all_images):
        """Filtra imagens excluindo subdiretórios marcados"""
        filtered = []

        for img_path in all_images:
            should_include = True
            img_str = str(img_path)

            for excluded_dir in self.excluded_dirs:
                # Verifica se o caminho contém o subdiretório excluído
                pattern = rf'[\\/]{re.escape(excluded_dir)}[\\/]|[\\/]{re.escape(excluded_dir)}$'
                if re.search(pattern, img_str, re.IGNORECASE):
                    should_include = False
                    break

            if should_include:
                filtered.append(img_path)

        return filtered

    def copy_images(self, images):
        """Copia imagens para o diretório de saída"""
        mapping = {}
        total = len(images)

        for i, img in enumerate(images, 1):
            # Caminho relativo ao diretório fonte
            relative_path = str(img.relative_to(self.source_dir))

            # Nome do arquivo de destino
            dest_filename = img.name

            # Se já existe arquivo com mesmo nome, adiciona sufixo
            if dest_filename in mapping:
                parent_folder = img.parent.name
                base_name = img.stem
                extension = img.suffix

                dest_filename = f"{base_name}_{parent_folder}{extension}"

                # Se ainda houver conflito, adiciona número
                suffix = 1
                while dest_filename in mapping:
                    dest_filename = f"{base_name}_{parent_folder}_{suffix}{extension}"
                    suffix += 1

            # Adiciona ao mapeamento
            mapping[dest_filename] = relative_path

            # Copia o arquivo
            dest_path = Path(self.output_dir) / dest_filename
            shutil.copy2(img, dest_path)

            # Mostra progresso
            progress = (i / total) * 100
            print(f"\r  [{i}/{total}] ({progress:.1f}%) Copiando... ", end='', flush=True)

        print(f"\r  [{total}/{total}] (100.0%) Concluído!          ")

        return mapping

    def save_config(self, mapping, excluded_count):
        """Salva configuração em JSON"""
        config_file = Path(self.output_dir) / "translation_config.json"

        config = {
            "sourceDirectory": str(self.source_dir),
            "outputDirectory": str(self.output_dir),
            "collectionDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "totalImages": len(mapping),
            "excludedDirectories": self.excluded_dirs,
            "excludedImagesCount": excluded_count,
            "mapping": mapping
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        return config_file

    def run(self):
        """Executa o processo completo"""
        print(f"{Color.CYAN}{'='*60}{Color.ENDC}")
        print(f"{Color.CYAN}{'COLETOR DE IMAGENS PARA BATCH TRANSLATION':^60}{Color.ENDC}")
        print(f"{Color.CYAN}{'='*60}{Color.ENDC}\n")

        # Seleciona diretório fonte
        print(f"{Color.YELLOW}Selecione o diretório BASE do jogo (ex: C:\\Games\\MeuJogo\\www\\img){Color.ENDC}")
        self.source_dir = self.select_folder("Selecione o diretório BASE com as imagens do jogo")

        if not self.source_dir:
            print(f"{Color.RED}X Operação cancelada pelo usuário{Color.ENDC}")
            return False

        self.source_dir = Path(self.source_dir)

        # Mostra dialog de exclusões
        self.excluded_dirs = self.show_exclusion_dialog()

        if self.excluded_dirs is None:
            print(f"{Color.RED}X Operação cancelada pelo usuário{Color.ENDC}")
            return False

        # Seleciona diretório de saída
        print(f"\n{Color.YELLOW}Selecione onde salvar as imagens ANINHADAS para tradução{Color.ENDC}")
        self.output_dir = self.select_folder("Selecione o diretório de SAÍDA para imagens aninhadas")

        if not self.output_dir:
            print(f"{Color.RED}X Operação cancelada pelo usuário{Color.ENDC}")
            return False

        self.output_dir = Path(self.output_dir)

        # Cria diretório de saída se não existir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Mostra configuração
        print(f"\n{Color.CYAN}=== CONFIGURAÇÃO ==={Color.ENDC}")
        print(f"{Color.BOLD}Origem:{Color.ENDC} {self.source_dir}")
        print(f"{Color.BOLD}Destino:{Color.ENDC} {self.output_dir}")

        if self.excluded_dirs:
            print(f"{Color.YELLOW}Pastas excluídas: {', '.join(self.excluded_dirs)}{Color.ENDC}")
        else:
            print(f"Pastas excluídas: Nenhuma")

        # Coleta imagens
        print(f"\n{Color.CYAN}=== COLETANDO IMAGENS ==={Color.ENDC}")

        all_images = self.collect_images()
        filtered_images = self.filter_images(all_images)
        excluded_count = len(all_images) - len(filtered_images)

        print(f"Total de imagens encontradas: {len(all_images)}")
        print(f"{Color.YELLOW}Imagens excluídas (pastas filtradas): {excluded_count}{Color.ENDC}")
        print(f"{Color.GREEN}Imagens a serem coletadas: {len(filtered_images)}{Color.ENDC}")

        if len(filtered_images) == 0:
            print(f"\n{Color.RED}X Nenhuma imagem para coletar após aplicar filtros!{Color.ENDC}")
            print(f"{Color.YELLOW}Tente desmarcar algumas pastas na exclusão.{Color.ENDC}")
            return False

        # Copia imagens
        print(f"\n{Color.CYAN}Copiando imagens...{Color.ENDC}")
        mapping = self.copy_images(filtered_images)

        # Salva configuração
        config_file = self.save_config(mapping, excluded_count)

        # Resultado final
        print(f"\n{Color.GREEN}=== CONCLUÍDO ==={Color.ENDC}")
        print(f"{Color.GREEN}Coletadas: {len(mapping)} imagens{Color.ENDC}")
        print(f"{Color.YELLOW}Excluídas: {excluded_count} imagens{Color.ENDC}")
        print(f"{Color.GREEN}Diretório de saída: {self.output_dir}{Color.ENDC}")
        print(f"{Color.GREEN}Configuração salva em: {config_file}{Color.ENDC}")

        if self.excluded_dirs:
            print(f"\n{Color.YELLOW}=== PASTAS EXCLUÍDAS ==={Color.ENDC}")
            for dir_name in self.excluded_dirs:
                print(f"  X {dir_name}")

        print(f"\n{Color.CYAN}=== PRÓXIMOS PASSOS ==={Color.ENDC}")
        print(f"1. Faça o batch translation das imagens em: {self.output_dir}")
        print(f"2. Se o serviço criar uma pasta 'translated', mantenha-a dentro de: {self.output_dir}")
        print(f"3. Execute restoreImages.py para restaurar as imagens traduzidas")

        # Abre o diretório de saída
        try:
            if sys.platform == 'win32':
                os.startfile(self.output_dir)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self.output_dir])
            else:
                subprocess.run(['xdg-open', self.output_dir])
        except Exception:
            pass

        return True


def main():
    collector = ImageCollector()
    success = collector.run()

    input(f"\n{Color.CYAN}Pressione Enter para sair...{Color.ENDC}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
