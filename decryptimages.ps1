# _Tools/1-decrypt-rpgmvp-FINAL.ps1

<#
.SYNOPSIS
    RPG Maker Decrypter ALL-IN-ONE (Baseado no script Python funcional)
.DESCRIPTION
    Descriptografa arquivos RPG Maker MV/MZ usando o método correto:
    - Ignora header RPGMV (primeiros 16 bytes)
    - XOR apenas nos bytes 16-31
    - Resto do arquivo fica intacto
#>

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ============================================================================
# FUNÇÕES DE UI
# ============================================================================

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host $Title.PadLeft(35 + $Title.Length / 2).PadRight(70) -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Select-Folder {
    param([string]$Description = "Selecione uma pasta")
    
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = $Description
    $folderBrowser.ShowNewFolderButton = $true
    
    if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $folderBrowser.SelectedPath
    }
    return $null
}

# ============================================================================
# FUNÇÕES DE DIAGNÓSTICO
# ============================================================================

function Get-SystemJsonInfo {
    param([string]$GameFolder)
    
    Write-Header "FASE 1: DIAGNÓSTICO"
    
    $systemPaths = @(
        (Join-Path $GameFolder "data\System.json"),
        (Join-Path $GameFolder "www\data\System.json")
    )
    
    Write-Host "🔍 Procurando System.json..." -ForegroundColor Yellow
    
    foreach ($systemPath in $systemPaths) {
        if (Test-Path $systemPath) {
            Write-Success "Encontrado: $(Split-Path $systemPath -Leaf)"
            
            try {
                $systemData = Get-Content $systemPath -Raw -Encoding UTF8 | ConvertFrom-Json
                
                $hasEncryptedImages = $systemData.hasEncryptedImages
                $hasEncryptedAudio = $systemData.hasEncryptedAudio
                $encryptionKey = $systemData.encryptionKey
                
                Write-Host ""
                Write-Host "📊 Configurações de criptografia:" -ForegroundColor Cyan
                Write-Host "   Imagens criptografadas: $hasEncryptedImages"
                Write-Host "   Áudio criptografado: $hasEncryptedAudio"
                Write-Host ""
                
                if ($encryptionKey) {
                    Write-Success "Chave encontrada: $encryptionKey"
                    $keyBytes = $encryptionKey.Length / 2
                    Write-Host "   Tamanho: $($encryptionKey.Length) chars ($keyBytes bytes)" -ForegroundColor Gray
                    
                    return @{
                        Path = $systemPath
                        Key = $encryptionKey
                        HasImages = $hasEncryptedImages
                        HasAudio = $hasEncryptedAudio
                    }
                }
                else {
                    Write-Error-Custom "Chave de criptografia não encontrada!"
                    return $null
                }
            }
            catch {
                Write-Error-Custom "Erro ao ler System.json: $_"
                return $null
            }
        }
    }
    
    Write-Error-Custom "System.json não encontrado!"
    return $null
}

function Test-SampleFile {
    param(
        [string]$GameFolder,
        [string]$EncryptionKey
    )
    
    Write-Host ""
    Write-Host "🔍 Procurando arquivo de exemplo..." -ForegroundColor Yellow
    
    $searchPatterns = @(
        "img\system\*.rpgmvp",
        "img\system\*.png_",
        "img\pictures\*.rpgmvp",
        "img\pictures\*.png_"
    )
    
    foreach ($pattern in $searchPatterns) {
        $fullPattern = Join-Path $GameFolder $pattern
        $files = Get-ChildItem -Path $fullPattern -ErrorAction SilentlyContinue
        
        if ($files) {
            $sampleFile = $files[0].FullName
            Write-Success "Arquivo de exemplo: $(Split-Path $sampleFile -Leaf)"
            
            $data = [System.IO.File]::ReadAllBytes($sampleFile)
            
            Write-Host ""
            Write-Host "📊 Análise:" -ForegroundColor Cyan
            Write-Host "   Tamanho: $($data.Length) bytes"
            
            $first16Hex = ($data[0..15] | ForEach-Object { $_.ToString("X2") }) -join " "
            Write-Host "   Primeiros 16 bytes: $first16Hex" -ForegroundColor Gray
            
            # Verifica header RPGMV
            $rpgmvHeader = [System.Text.Encoding]::ASCII.GetString($data[0..4])
            if ($rpgmvHeader -eq "RPGMV") {
                Write-Success "Header RPGMV detectado"
                
                $standardHeader = "52 50 47 4D 56 00 00 00 00 03 01 00 00 00 00 00"
                if ($first16Hex -eq $standardHeader) {
                    Write-Success "Header PADRÃO (comum)"
                }
                else {
                    Write-Warning-Custom "Header CUSTOMIZADO"
                    Write-Host "   Esperado: $standardHeader" -ForegroundColor Gray
                    Write-Host "   Atual:    $first16Hex" -ForegroundColor Gray
                }
            }
            else {
                Write-Error-Custom "Header RPGMV não encontrado!"
            }
            
            # Testa XOR
            Write-Host ""
            Write-Host "🧪 Teste de XOR:" -ForegroundColor Cyan
            
            $keyBytes = [byte[]]::new($EncryptionKey.Length / 2)
            for ($i = 0; $i -lt $EncryptionKey.Length; $i += 2) {
                $keyBytes[$i / 2] = [Convert]::ToByte($EncryptionKey.Substring($i, 2), 16)
            }
            
            # XOR nos bytes 16-31 (MÉTODO CORRETO)
            $encryptedHeader = $data[16..31]
            $decryptedHeader = [byte[]]::new(16)
            
            for ($i = 0; $i -lt 16; $i++) {
                $decryptedHeader[$i] = $encryptedHeader[$i] -bxor $keyBytes[$i]
            }
            
            $encHex = ($encryptedHeader | ForEach-Object { $_.ToString("X2") }) -join " "
            $decHex = ($decryptedHeader | ForEach-Object { $_.ToString("X2") }) -join " "
            
            Write-Host "   Criptografado:     $encHex" -ForegroundColor Gray
            Write-Host "   Descriptografado:  $decHex" -ForegroundColor Gray
            
            # Assinatura PNG esperada
            $pngSignature = @(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
            $isValid = $true
            
            for ($i = 0; $i -lt 8; $i++) {
                if ($decryptedHeader[$i] -ne $pngSignature[$i]) {
                    $isValid = $false
                    break
                }
            }
            
            if ($isValid) {
                Write-Success "XOR funcionou! Assinatura PNG válida"
                return $true
            }
            else {
                Write-Error-Custom "XOR não produziu assinatura válida"
                $expectedHex = ($pngSignature | ForEach-Object { $_.ToString("X2") }) -join " "
                Write-Host "   Esperado: $expectedHex ..." -ForegroundColor Gray
                return $false
            }
        }
    }
    
    Write-Warning-Custom "Nenhum arquivo de exemplo encontrado"
    return $true
}

# ============================================================================
# FUNÇÃO DE DESCRIPTOGRAFIA
# ============================================================================

function Decrypt-AllFiles {
    param(
        [string]$GameFolder,
        [string]$EncryptionKey
    )
    
    Write-Header "FASE 2: DESCRIPTOGRAFIA"
    
    $encryptedExtensions = @{
        '.rpgmvp' = '.png'
        '.png_'   = '.png'
        '.rpgmvo' = '.ogg'
        '.ogg_'   = '.ogg'
        '.rpgmvm' = '.m4a'
        '.m4a_'   = '.m4a'
    }
    
    $signatures = @{
        '.png' = @(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
        '.ogg' = @(0x4F, 0x67, 0x67, 0x53)
        '.m4a' = @(0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70)
    }
    
    Write-Host "🔍 Procurando arquivos criptografados..." -ForegroundColor Yellow
    
    $encryptedFiles = @()
    foreach ($ext in $encryptedExtensions.Keys) {
        $files = Get-ChildItem -Path $GameFolder -Filter "*$ext" -Recurse -File
        $encryptedFiles += $files
    }
    
    if ($encryptedFiles.Count -eq 0) {
        Write-Warning-Custom "Nenhum arquivo criptografado encontrado!"
        return @{ Success = 0; Failed = 0 }
    }
    
    $total = $encryptedFiles.Count
    Write-Info "Encontrados $total arquivos para descriptografar"
    
    Write-Host ""
    Write-Host "🔓 Iniciando descriptografia..." -ForegroundColor Yellow
    Write-Host "   Método: XOR apenas nos bytes 16-31" -ForegroundColor Gray
    Write-Host "   Chave: $($EncryptionKey.Substring(0, [Math]::Min(16, $EncryptionKey.Length)))..." -ForegroundColor Gray
    Write-Host ""
    
    $keyBytes = [byte[]]::new($EncryptionKey.Length / 2)
    for ($i = 0; $i -lt $EncryptionKey.Length; $i += 2) {
        $keyBytes[$i / 2] = [Convert]::ToByte($EncryptionKey.Substring($i, 2), 16)
    }
    
    $stats = @{ Success = 0; Failed = 0 }
    $progressCount = 0
    
    foreach ($file in $encryptedFiles) {
        $progressCount++
        $progress = ($progressCount / $total) * 100
        
        Write-Progress -Activity "Descriptografando arquivos" `
                       -Status "$progressCount de $total" `
                       -PercentComplete $progress
        
        $fileName = $file.Name
        if ($fileName.Length -gt 40) {
            $fileName = $fileName.Substring(0, 37) + "..."
        }
        
        Write-Host "  [$progressCount/$total] ($($progress.ToString('F1'))%) $($fileName.PadRight(40)) " -NoNewline
        
        try {
            # Lê arquivo
            $data = [System.IO.File]::ReadAllBytes($file.FullName)
            
            if ($data.Length -lt 32) {
                Write-Host "muito pequeno" -ForegroundColor Red
                $stats.Failed++
                continue
            }
            
            # Verifica header RPGMV
            $header = [System.Text.Encoding]::ASCII.GetString($data[0..4])
            if ($header -ne "RPGMV") {
                Write-Host "sem header RPGMV" -ForegroundColor Yellow
                $stats.Failed++
                continue
            }
            
            # DESCRIPTOGRAFIA CORRETA:
            # - Bytes 0-15: Header RPGMV (ignorar)
            # - Bytes 16-31: Criptografados (aplicar XOR)
            # - Bytes 32+: Resto do arquivo (copiar direto)
            
            $encryptedHeader = $data[16..31]
            $unencryptedBody = $data[32..($data.Length - 1)]
            
            $decryptedHeader = [byte[]]::new(16)
            for ($i = 0; $i -lt 16; $i++) {
                $decryptedHeader[$i] = $encryptedHeader[$i] -bxor $keyBytes[$i]
            }
            
            # Arquivo final = decryptedHeader + unencryptedBody
            $finalData = $decryptedHeader + $unencryptedBody
            
            # Verifica assinatura
            $outputExt = $encryptedExtensions[$file.Extension]
            $expectedSig = $signatures[$outputExt]
            
            if ($expectedSig) {
                $isValid = $true
                for ($i = 0; $i -lt $expectedSig.Length; $i++) {
                    if ($finalData[$i] -ne $expectedSig[$i]) {
                        $isValid = $false
                        break
                    }
                }
                
                if (-not $isValid) {
                    Write-Host "assinatura inválida" -ForegroundColor Red
                    $stats.Failed++
                    continue
                }
            }
            
            # Salva
            $outputPath = $file.FullName -replace [regex]::Escape($file.Extension), $outputExt
            [System.IO.File]::WriteAllBytes($outputPath, $finalData)
            
            Write-Host "$($finalData.Length) bytes" -ForegroundColor Green
            $stats.Success++
            
        }
        catch {
            Write-Host $_.Exception.Message -ForegroundColor Red
            $stats.Failed++
        }
    }
    
    Write-Progress -Activity "Descriptografando arquivos" -Completed
    
    Write-Host ""
    Write-Host ("-" * 70) -ForegroundColor Gray
    Write-Success "Descriptografados: $($stats.Success)"
    if ($stats.Failed -gt 0) {
        Write-Error-Custom "Falhas: $($stats.Failed)"
    }
    Write-Host ("-" * 70) -ForegroundColor Gray
    
    return $stats
}

# ============================================================================
# FUNÇÃO DE VERIFICAÇÃO
# ============================================================================

function Test-Integrity {
    param([string]$GameFolder)
    
    Write-Header "FASE 3: VERIFICAÇÃO DE INTEGRIDADE"
    
    Write-Host "🔍 Verificando arquivos descriptografados..." -ForegroundColor Yellow
    Write-Host ""
    
    $signatures = @{
        '.png' = @(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A)
        '.ogg' = @(0x4F, 0x67, 0x67, 0x53)
    }
    
    $corrupted = @()
    $valid = 0
    
    foreach ($ext in $signatures.Keys) {
        $files = Get-ChildItem -Path $GameFolder -Filter "*$ext" -Recurse -File
        
        foreach ($file in $files) {
            try {
                $header = [System.IO.File]::ReadAllBytes($file.FullName)[0..($signatures[$ext].Length - 1)]
                
                $isValid = $true
                for ($i = 0; $i -lt $signatures[$ext].Length; $i++) {
                    if ($header[$i] -ne $signatures[$ext][$i]) {
                        $isValid = $false
                        break
                    }
                }
                
                if ($isValid) {
                    $valid++
                }
                else {
                    $corrupted += $file
                }
            }
            catch {
                $corrupted += $file
            }
        }
    }
    
    Write-Host ("-" * 70) -ForegroundColor Gray
    Write-Success "Arquivos válidos: $valid"
    
    if ($corrupted.Count -gt 0) {
        Write-Error-Custom "Arquivos corrompidos: $($corrupted.Count)"
        Write-Host ""
        Write-Host "📋 Lista de corrompidos:" -ForegroundColor Yellow
        
        $showCount = [Math]::Min(10, $corrupted.Count)
        for ($i = 0; $i -lt $showCount; $i++) {
            $relativePath = $corrupted[$i].FullName.Replace($GameFolder, "").TrimStart('\')
            Write-Host "   - $relativePath" -ForegroundColor Gray
        }
        
        if ($corrupted.Count -gt 10) {
            Write-Host "   ... e mais $($corrupted.Count - 10) arquivos" -ForegroundColor Gray
        }
    }
    else {
        Write-Success "Todos os arquivos estão íntegros!"
    }
    
    Write-Host ("-" * 70) -ForegroundColor Gray
    
    return $corrupted.Count
}

# ============================================================================
# FUNÇÃO PARA DESATIVAR CRIPTOGRAFIA
# ============================================================================

function Disable-Encryption {
    param([string]$GameFolder)
    
    Write-Host ""
    Write-Host "🔧 Desativando flags de criptografia..." -ForegroundColor Yellow
    
    $systemPaths = @(
        (Join-Path $GameFolder "data\System.json"),
        (Join-Path $GameFolder "www\data\System.json")
    )
    
    foreach ($systemPath in $systemPaths) {
        if (Test-Path $systemPath) {
            try {
                $systemData = Get-Content $systemPath -Raw -Encoding UTF8 | ConvertFrom-Json
                
                # Backup
                $backupPath = "$systemPath.backup"
                if (-not (Test-Path $backupPath)) {
                    Copy-Item $systemPath $backupPath
                    Write-Success "Backup: $(Split-Path $backupPath -Leaf)"
                }
                
                # Desativa
                $systemData.hasEncryptedImages = $false
                $systemData.hasEncryptedAudio = $false
                
                $systemData | ConvertTo-Json -Depth 100 | Set-Content $systemPath -Encoding UTF8
                
                Write-Success "System.json atualizado"
            }
            catch {
                Write-Error-Custom "Erro: $_"
            }
        }
    }
}

# ============================================================================
# MAIN
# ============================================================================

Write-Header "RPG MAKER DECRYPTER ALL-IN-ONE"

# Seleciona pasta do jogo
Write-Host "📁 Selecione a pasta do JOGO..." -ForegroundColor Yellow
$GameFolder = Select-Folder -Description "Selecione a pasta do jogo RPG Maker"

if ([string]::IsNullOrEmpty($GameFolder)) {
    Write-Error-Custom "Operação cancelada"
    Read-Host "Pressione ENTER para sair"
    exit 1
}

Write-Host "✅ Jogo: $GameFolder" -ForegroundColor Green
Write-Host ""

# Fase 1: Diagnóstico
$systemInfo = Get-SystemJsonInfo -GameFolder $GameFolder

if (-not $systemInfo) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Red
    Write-Host "❌ ERRO: Não foi possível encontrar a chave de criptografia" -ForegroundColor Red
    Write-Host ("=" * 70) -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
    exit 1
}

Test-SampleFile -GameFolder $GameFolder -EncryptionKey $systemInfo.Key

# Fase 2: Descriptografia
$stats = Decrypt-AllFiles -GameFolder $GameFolder -EncryptionKey $systemInfo.Key

# Fase 3: Verificação
$corruptedCount = Test-Integrity -GameFolder $GameFolder

# Desativa criptografia
Disable-Encryption -GameFolder $GameFolder

# Resumo final
Write-Header "RESUMO FINAL"

Write-Host "📊 Estatísticas:" -ForegroundColor Cyan
Write-Success "Descriptografados: $($stats.Success)"

if ($stats.Failed -gt 0) {
    Write-Error-Custom "Falhas: $($stats.Failed)"
}

if ($corruptedCount -gt 0) {
    Write-Error-Custom "Corrompidos: $corruptedCount"
}

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan

if ($stats.Failed -eq 0 -and $corruptedCount -eq 0) {
    Write-Host "✨ SUCESSO TOTAL! ✨" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎮 Agora você pode testar o jogo!" -ForegroundColor Green
}
else {
    Write-Warning-Custom "⚠️  Processo concluído com alguns erros"
    Write-Host ""
    Write-Host "💡 Execute novamente se necessário" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Pressione ENTER para sair"