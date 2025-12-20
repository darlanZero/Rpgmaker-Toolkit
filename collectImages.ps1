# ===== ETAPA 1: Coletar Imagens (COM GUI + EXCLUSÃO DE PASTAS) =====
# Salve como: CollectImages.ps1

Add-Type -AssemblyName System.Windows.Forms

# Função para selecionar pasta
function Select-Folder {
    param([string]$Description)
    
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = $Description
    $folderBrowser.ShowNewFolderButton = $true
    
    if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $folderBrowser.SelectedPath
    }
    return $null
}

# Função para mostrar checklist de exclusões
function Show-ExclusionDialog {
    param([string[]]$DefaultExclusions)
    
    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Selecione pastas para EXCLUIR"
    $form.Size = New-Object System.Drawing.Size(450, 500)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    
    # Label de instrução
    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(10, 10)
    $label.Size = New-Object System.Drawing.Size(420, 40)
    $label.Text = "Marque os subdiretórios que NÃO contêm texto para tradução:`n(Imagens dessas pastas serão IGNORADAS)"
    $form.Controls.Add($label)
    
    # CheckedListBox
    $checkedListBox = New-Object System.Windows.Forms.CheckedListBox
    $checkedListBox.Location = New-Object System.Drawing.Point(10, 55)
    $checkedListBox.Size = New-Object System.Drawing.Size(410, 320)
    $checkedListBox.CheckOnClick = $true
    
    # Adiciona itens padrão
    $exclusionOptions = @(
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
    )
    
    foreach ($option in $exclusionOptions) {
        $index = $checkedListBox.Items.Add($option)
        if ($DefaultExclusions -contains $option) {
            $checkedListBox.SetItemChecked($index, $true)
        }
    }
    
    $form.Controls.Add($checkedListBox)
    
    # Campo para adicionar exclusão customizada
    $customLabel = New-Object System.Windows.Forms.Label
    $customLabel.Location = New-Object System.Drawing.Point(10, 385)
    $customLabel.Size = New-Object System.Drawing.Size(200, 20)
    $customLabel.Text = "Adicionar pasta customizada:"
    $form.Controls.Add($customLabel)
    
    $customTextBox = New-Object System.Windows.Forms.TextBox
    $customTextBox.Location = New-Object System.Drawing.Point(10, 405)
    $customTextBox.Size = New-Object System.Drawing.Size(250, 20)
    $form.Controls.Add($customTextBox)
    
    $addButton = New-Object System.Windows.Forms.Button
    $addButton.Location = New-Object System.Drawing.Point(270, 403)
    $addButton.Size = New-Object System.Drawing.Size(75, 23)
    $addButton.Text = "Adicionar"
    $addButton.Add_Click({
        if ($customTextBox.Text.Trim() -ne "") {
            $index = $checkedListBox.Items.Add($customTextBox.Text.Trim())
            $checkedListBox.SetItemChecked($index, $true)
            $customTextBox.Clear()
        }
    })
    $form.Controls.Add($addButton)
    
    # Botões OK e Cancelar
    $okButton = New-Object System.Windows.Forms.Button
    $okButton.Location = New-Object System.Drawing.Point(180, 435)
    $okButton.Size = New-Object System.Drawing.Size(75, 23)
    $okButton.Text = "OK"
    $okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.Controls.Add($okButton)
    $form.AcceptButton = $okButton
    
    $cancelButton = New-Object System.Windows.Forms.Button
    $cancelButton.Location = New-Object System.Drawing.Point(260, 435)
    $cancelButton.Size = New-Object System.Drawing.Size(75, 23)
    $cancelButton.Text = "Cancelar"
    $cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
    $form.Controls.Add($cancelButton)
    $form.CancelButton = $cancelButton
    
    $result = $form.ShowDialog()
    
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
        $selected = @()
        foreach ($item in $checkedListBox.CheckedItems) {
            $selected += $item.ToString()
        }
        return $selected
    }
    
    return $null
}

# ===== INÍCIO DO SCRIPT =====

Write-Host "=== COLETOR DE IMAGENS PARA BATCH TRANSLATION ===" -ForegroundColor Cyan
Write-Host "`nSelecione o diretório BASE do jogo (ex: C:\Games\MeuJogo\www\img)" -ForegroundColor Yellow

$sourceDir = Select-Folder -Description "Selecione o diretório BASE com as imagens do jogo"

if (-not $sourceDir) {
    Write-Host "✗ Operação cancelada pelo usuário" -ForegroundColor Red
    exit 1
}

# Mostra dialog de exclusões (com padrões pré-marcados)
$defaultExclusions = @("particles", "parallaxes", "tilesets", "characters", "actors")
$excludedDirs = Show-ExclusionDialog -DefaultExclusions $defaultExclusions

if ($null -eq $excludedDirs) {
    Write-Host "✗ Operação cancelada pelo usuário" -ForegroundColor Red
    exit 1
}

# Seleciona diretório de saída
Write-Host "`nSelecione onde salvar as imagens ANINHADAS para tradução" -ForegroundColor Yellow

$outputDir = Select-Folder -Description "Selecione o diretório de SAÍDA para imagens aninhadas"

if (-not $outputDir) {
    Write-Host "✗ Operação cancelada pelo usuário" -ForegroundColor Red
    exit 1
}

# Cria o diretório de output
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

# Arquivo de configuração (salva no diretório de saída)
$configFile = Join-Path $outputDir "translation_config.json"

# Extensões de imagem suportadas
$imageExtensions = @('*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.webp', '*.tiff')

Write-Host "`n=== CONFIGURAÇÃO ===" -ForegroundColor Cyan
Write-Host "Origem: $sourceDir" -ForegroundColor Gray
Write-Host "Destino: $outputDir" -ForegroundColor Gray

if ($excludedDirs.Count -gt 0) {
    Write-Host "Pastas excluídas: $($excludedDirs -join ', ')" -ForegroundColor Yellow
} else {
    Write-Host "Pastas excluídas: Nenhuma" -ForegroundColor Gray
}

Write-Host "`n=== COLETANDO IMAGENS ===" -ForegroundColor Cyan

# Coleta todas as imagens
$allImages = Get-ChildItem -Path $sourceDir -Recurse -Include $imageExtensions -File

# Filtra imagens excluindo os subdiretórios marcados
$images = $allImages | Where-Object {
    $imagePath = $_.FullName
    $shouldInclude = $true
    
    foreach ($excludedDir in $excludedDirs) {
        # Verifica se o caminho contém o subdiretório excluído
        # Usa \\ ou / para garantir que é um diretório completo, não parte do nome
        if ($imagePath -match "[\\/]$excludedDir[\\/]" -or $imagePath -match "[\\/]$excludedDir$") {
            $shouldInclude = $false
            break
        }
    }
    
    $shouldInclude
}

$excludedCount = $allImages.Count - $images.Count

Write-Host "Total de imagens encontradas: $($allImages.Count)" -ForegroundColor Gray
Write-Host "Imagens excluídas (pastas filtradas): $excludedCount" -ForegroundColor Yellow
Write-Host "Imagens a serem coletadas: $($images.Count)" -ForegroundColor Green

if ($images.Count -eq 0) {
    Write-Host "`n✗ Nenhuma imagem para coletar após aplicar filtros!" -ForegroundColor Red
    Write-Host "Tente desmarcar algumas pastas na exclusão." -ForegroundColor Yellow
    exit 1
}

# Mapeamento: nome do arquivo de saída -> caminho original relativo
$mapping = @{}
$counter = 0

foreach ($img in $images) {
    $counter++
    
    # Caminho relativo ao diretório fonte
    $relativePath = $img.FullName.Substring($sourceDir.Length).TrimStart('\', '/')
    
    # Nome do arquivo de destino (mantém o nome original)
    $destFileName = $img.Name
    
    # Se já existe arquivo com mesmo nome, adiciona sufixo baseado no diretório pai
    if ($mapping.ContainsKey($destFileName)) {
        $parentFolder = Split-Path -Leaf (Split-Path -Parent $img.FullName)
        $baseName = [System.IO.Path]::GetFileNameWithoutExtension($img.Name)
        $extension = $img.Extension
        
        $destFileName = "${baseName}_${parentFolder}${extension}"
        
        # Se ainda houver conflito, adiciona número
        $suffix = 1
        while ($mapping.ContainsKey($destFileName)) {
            $destFileName = "${baseName}_${parentFolder}_${suffix}${extension}"
            $suffix++
        }
    }
    
    # Adiciona ao mapeamento
    $mapping[$destFileName] = $relativePath
    
    # Copia o arquivo
    $destPath = Join-Path $outputDir $destFileName
    Copy-Item -Path $img.FullName -Destination $destPath -Force
    
    Write-Progress -Activity "Coletando imagens" -Status "$counter de $($images.Count)" -PercentComplete (($counter / $images.Count) * 100)
}

# Cria configuração completa
$config = @{
    sourceDirectory = $sourceDir
    outputDirectory = $outputDir
    collectionDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    totalImages = $counter
    excludedDirectories = $excludedDirs
    excludedImagesCount = $excludedCount
    mapping = $mapping
}

# Salva configuração em JSON
$config | ConvertTo-Json -Depth 10 | Set-Content -Path $configFile -Encoding UTF8

Write-Host "`n=== CONCLUÍDO ===" -ForegroundColor Green
Write-Host "✓ Coletadas: $counter imagens" -ForegroundColor Green
Write-Host "✓ Excluídas: $excludedCount imagens" -ForegroundColor Yellow
Write-Host "✓ Diretório de saída: $outputDir" -ForegroundColor Green
Write-Host "✓ Configuração salva em: $configFile" -ForegroundColor Green

if ($excludedDirs.Count -gt 0) {
    Write-Host "`n=== PASTAS EXCLUÍDAS ===" -ForegroundColor Yellow
    foreach ($dir in $excludedDirs) {
        Write-Host "  ✗ $dir" -ForegroundColor Gray
    }
}

Write-Host "`n=== PRÓXIMOS PASSOS ===" -ForegroundColor Cyan
Write-Host "1. Faça o batch translation das imagens em: $outputDir" -ForegroundColor White
Write-Host "2. Se o serviço criar uma pasta 'translated', mantenha-a dentro de: $outputDir" -ForegroundColor White
Write-Host "3. Execute RestoreImages.ps1 para restaurar as imagens traduzidas" -ForegroundColor White

# Abre o diretório de saída
explorer.exe $outputDir
