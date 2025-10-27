#!/usr/bin/env python3
"""
Procura todos os arquivos relacionados a Live2D no jogo
"""

import os
import sys
from pathlib import Path

def find_live2d_files(game_folder):
    game_folder = Path(game_folder)
    
    print("="*70)
    print("  BUSCA COMPLETA DE ARQUIVOS LIVE2D")
    print("="*70)
    
    # Extensões para procurar
    extensions = [
        '.model3.json', '.json', '.json_',
        '.moc3', '.moc3_',
        '.physics3.json', '.physics3.json_',
        '.cdi3.json', '.cdi3.json_',
        '.userdata3.json', '.userdata3.json_',
        '.motion3.json', '.motion3.json_',
        '.exp3.json', '.exp3.json_',
        '.png', '.png_'
    ]
    
    print("\n🔍 Procurando em todas as pastas...")
    
    results = {}
    
    # Procura em todo o jogo
    for root, dirs, files in os.walk(game_folder):
        root_path = Path(root)
        
        # Ignora algumas pastas
        if any(x in root_path.parts for x in ['node_modules', '__pycache__', '_backup']):
            continue
        
        for file in files:
            file_path = root_path / file
            ext = ''.join(file_path.suffixes)  # Pega todas as extensões
            
            # Verifica se é arquivo Live2D
            is_live2d = False
            
            # Por extensão
            if any(file.endswith(e) for e in extensions):
                is_live2d = True
            
            # Por palavra-chave no nome
            if any(kw in file.lower() for kw in ['live2d', 'model3', '.moc3', 'motion']):
                is_live2d = True
            
            # Por estar na pasta live2d
            if 'live2d' in str(file_path).lower():
                is_live2d = True
            
            if is_live2d:
                relative = file_path.relative_to(game_folder)
                category = str(relative.parent)
                
                if category not in results:
                    results[category] = []
                
                results[category].append({
                    'name': file,
                    'size': file_path.stat().st_size,
                    'path': relative
                })
    
    # Mostra resultados
    if not results:
        print("\n❌ Nenhum arquivo Live2D encontrado!")
        return
    
    print(f"\n📦 Encontrados arquivos em {len(results)} pastas:\n")
    
    total_files = 0
    
    for category, files in sorted(results.items()):
        print(f"\n📁 {category}/")
        print(f"   Arquivos: {len(files)}")
        
        # Mostra alguns exemplos
        for file_info in sorted(files, key=lambda x: x['name'])[:10]:
            size_kb = file_info['size'] / 1024
            print(f"   - {file_info['name']:40s} ({size_kb:8.1f} KB)")
        
        if len(files) > 10:
            print(f"   ... e mais {len(files)-10} arquivos")
        
        total_files += len(files)
    
    print(f"\n{'='*70}")
    print(f"📊 TOTAL: {total_files} arquivos relacionados a Live2D")
    print(f"{'='*70}")
    
    # Verifica arquivos JSON especificamente
    print("\n🔍 Procurando arquivos .model3.json especificamente...")
    
    json_files = []
    for category, files in results.items():
        for file_info in files:
            if '.model3.json' in file_info['name'] or 'model' in file_info['name'].lower():
                json_files.append(file_info['path'])
    
    if json_files:
        print(f"✅ Encontrados {len(json_files)} arquivos de modelo:")
        for p in json_files:
            print(f"   - {p}")
    else:
        print(f"❌ Nenhum arquivo .model3.json encontrado!")
        print(f"\n💡 Isto significa:")
        print(f"   1. Os modelos podem estar embutidos no plugin")
        print(f"   2. Ou o plugin está tentando gerar os arquivos dinamicamente")
        print(f"   3. Ou há um problema na configuração do plugin")

def check_plugin_config(game_folder):
    """Verifica configuração do plugin Live2D"""
    game_folder = Path(game_folder)
    
    print(f"\n{'='*70}")
    print(f"  VERIFICANDO CONFIGURAÇÃO DO PLUGIN")
    print(f"{'='*70}")
    
    # Procura plugin Live2D
    plugin_paths = [
        game_folder / 'js' / 'plugins' / 'PictureLive2D.js',
        game_folder / 'js' / 'plugins.js'
    ]
    
    for plugin_path in plugin_paths:
        if plugin_path.exists():
            print(f"\n📄 {plugin_path.name}")
            
            with open(plugin_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Procura por caminhos de modelo
            import re
            
            # Procura padrões de caminho
            patterns = [
                r'img/live2d/[^"\']+\.model3\.json',
                r'live2d/[^"\']+\.model3\.json',
                r'\.model3\.json',
            ]
            
            found_paths = []
            for pattern in patterns:
                matches = re.findall(pattern, content)
                found_paths.extend(matches)
            
            if found_paths:
                print(f"   ✅ Encontrados {len(found_paths)} caminhos no código:")
                for path in set(found_paths[:10]):
                    print(f"      - {path}")
            else:
                print(f"   ⚠️  Nenhum caminho .model3.json encontrado no código")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python buscar_live2d.py /caminho/jogo")
        sys.exit(1)
    
    game_folder = sys.argv[1]
    
    if not os.path.isdir(game_folder):
        print(f"❌ Pasta não encontrada: {game_folder}")
        sys.exit(1)
    
    find_live2d_files(game_folder)
    check_plugin_config(game_folder)
    
    print(f"\n{'='*70}")
    print(f"💡 PRÓXIMOS PASSOS:")
    print(f"{'='*70}")
    print(f"1. Se encontrou arquivos .json_ → descriptografe-os")
    print(f"2. Se não encontrou .json → o problema é do plugin")
    print(f"3. Verifique o arquivo js/plugins/PictureLive2D.js")
    print(f"{'='*70}")
