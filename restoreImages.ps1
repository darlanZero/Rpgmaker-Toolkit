# ===== ETAPA 2: Restaurar Imagens Traduzidas (COM GUI) =====
# Salve como: RestoreImages.ps1

Add-Type -AssemblyName System.Windows.Forms

# Função para selecionar pasta
function Select-Folder {
    param([string]$Description)
    
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = $Description
    $folderBrowser.ShowNewFolderButton = $false
    
    if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $folderBrowser.SelectedPath
    }
    return $null
}

# Função para perguntar sim/não
function Ask-YesNo {
    param([string]$Question)
    
    $result = [System.Windows.Forms.MessageBox]::Show(
        $Question,
        "Confirmação",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    
    return $result -eq [System.Windows.Forms.DialogResult]::Yes
}

Write-Host "=== RESTAURADOR DE IMAGENS TRADUZIDAS ===" -ForegroundColor Cyan

# Seleciona diretório de output (onde as imagens aninhadas estão)
Write-Host "`nSelecione o diretório onde estão as imagens ANINHADAS" -ForegroundColor Yellow
Write-Host "(O mesmo diretório escolhido como saída no CollectImages.ps1)" -ForegroundColor Gray

$outputDir = Select-Folder -Description "Selecione o diretório com as imagens aninhadas"

if (-not $outputDir) {
    Write-Host "✗ Operação cancelada pelo usuário" -ForegroundColor Red
    exit 1
}

# Verifica se existe o arquivo de configuração
$configFile = Join-Path $outputDir "translation_config.json"

if (-not (Test-Path $configFile)) {
    Write-Host "`n✗ Arquivo de configuração não encontrado!" -ForegroundColor Red
    Write-Host "✗ Esperado em: $configFile" -ForegroundColor Red
    Write-Host "`nCertifique-se de que:" -ForegroundColor Yellow
    Write-Host "1. Este é o mesmo diretório usado no CollectImages.ps1" -ForegroundColor White
    Write-Host "2. O arquivo translation_config.json não foi deletado" -ForegroundColor White
    exit 1
}

# Lê a configuração
$config = Get-Content -Path $configFile -Encoding UTF8 | ConvertFrom-Json

$sourceDir = $config.sourceDirectory

Write-Host "`n=== CONFIGURAÇÃO CARREGADA ===" -ForegroundColor Green
Write-Host "Diretório original do jogo: $sourceDir" -ForegroundColor Gray
Write-Host "Total de imagens coletadas: $($config.totalImages)" -ForegroundColor Gray
Write-Host "Data da coleta: $($config.collectionDate)" -ForegroundColor Gray

# Pergunta se as imagens foram traduzidas
Write-Host "`n"
$wasTranslated = Ask-YesNo -Question "As imagens foram TRADUZIDAS?`n`nSIM = Buscar em '$outputDir\translated'`nNÃO = Usar imagens de '$outputDir'"

# Define o diretório de imagens traduzidas
if ($wasTranslated) {
    $translatedDir = Join-Path $outputDir "translated"
    
    if (-not (Test-Path $translatedDir)) {
        Write-Host "`n✗ Pasta 'translated' não encontrada!" -ForegroundColor Red
        Write-Host "✗ Esperado em: $translatedDir" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n✓ Usando imagens de: $translatedDir" -ForegroundColor Green
} else {
    $translatedDir = $outputDir
    Write-Host "`n✓ Usando imagens de: $translatedDir" -ForegroundColor Green
}

# Pergunta se quer criar backup
$createBackup = Ask-YesNo -Question "Deseja criar BACKUP das imagens originais antes de sobrescrever?`n`n(Recomendado: SIM)"

# Converte mapping para hashtable
$mappingHash = @{}
$config.mapping.PSObject.Properties | ForEach-Object {
    $mappingHash[$_.Name] = $_.Value
}

Write-Host "`n=== RESTAURANDO IMAGENS ===" -ForegroundColor Cyan

$translatedFiles = Get-ChildItem -Path $translatedDir -File -Include $imageExtensions
$counter = 0
$restored = 0
$notFound = @()
$backupCount = 0

foreach ($file in $translatedFiles) {
    $counter++
    
    # Busca o caminho original
    $originalRelativePath = $mappingHash[$file.Name]
    
    if ($originalRelativePath) {
        $originalFullPath = Join-Path $sourceDir $originalRelativePath
        
        # Cria backup se necessário
        if ($createBackup -and (Test-Path $originalFullPath)) {
            $backupPath = "$originalFullPath.backup"
            
            # Se já existe backup, não sobrescreve
            if (-not (Test-Path $backupPath)) {
                Copy-Item -Path $originalFullPath -Destination $backupPath -Force
                $backupCount++
            }
        }
        
        # Garante que o diretório de destino existe
        $destDir = Split-Path -Parent $originalFullPath
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        }
        
        # Copia o arquivo traduzido de volta
        Copy-Item -Path $file.FullName -Destination $originalFullPath -Force
        $restored++
        
        Write-Progress -Activity "Restaurando imagens" -Status "$counter de $($translatedFiles.Count)" -PercentComplete (($counter / $translatedFiles.Count) * 100)
    } else {
        $notFound += $file.Name
    }
}

Write-Host "`n=== CONCLUÍDO ===" -ForegroundColor Green
Write-Host "✓ Restauradas: $restored de $($translatedFiles.Count) imagens" -ForegroundColor Green

if ($createBackup) {
    Write-Host "✓ Backups criados: $backupCount arquivos (.backup)" -ForegroundColor Green
}

if ($notFound.Count -gt 0) {
    Write-Host "`n⚠ ATENÇÃO: Arquivos não encontrados no mapeamento:" -ForegroundColor Yellow
    $notFound | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    Write-Host "`nEstes arquivos não foram restaurados (não estavam na coleta original)" -ForegroundColor Yellow
}

Write-Host "`n✓ Imagens restauradas em: $sourceDir" -ForegroundColor Green

# Pergunta se quer abrir o diretório
if (Ask-YesNo -Question "Deseja abrir o diretório do jogo?") {
    explorer.exe $sourceDir
}