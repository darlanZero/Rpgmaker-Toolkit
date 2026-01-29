# --- CONFIGURAÇÃO ---
$pastaOriginal = "C:\Users\anime\Downloads\translation\Hentai4daily\えぶりーでぱんつ!!! 体験版Ver1.03\えぶりーでぱんつ!!!_体験版Ver.1.03\www\data"
$pastaTraduzida = "C:\Users\anime\Downloads\translation\Hentai4daily\えぶりーでぱんつ!!! 体験版Ver1.03\pantiesEverydayTranslatedV1\www\data"
# --------------------

function Reparar-Json($caminhoOrig, $caminhoTrad) {
    if (-not (Test-Path $caminhoTrad)) { return }
    
    $jsonOrig = Get-Content $caminhoOrig -Raw | ConvertFrom-Json
    $jsonTrad = Get-Content $caminhoTrad -Raw | ConvertFrom-Json
    $modificado = $false

    # Função interna para processar listas de comandos
    function Processar-Lista($origList, $tradList) {
        $mudou = $false
        for ($i = 0; $i -lt $origList.Count; $i++) {
            # Código 231 = Show Picture
            if ($origList[$i].code -eq 231) {
                if ([string]::IsNullOrWhiteSpace($tradList[$i].parameters[1])) {
                    $tradList[$i].parameters[1] = $origList[$i].parameters[1]
                    $mudou = $true
                }
            }
        }
        return $mudou
    }

    # Se for arquivo de Mapa
    if ($jsonOrig.events) {
        foreach ($e in $jsonOrig.events) {
            if ($null -eq $e) { continue }
            $tradE = $jsonTrad.events | Where-Object { $_.id -eq $e.id }
            for ($p = 0; $p -lt $e.pages.Count; $p++) {
                if (Processar-Lista $e.pages[$p].list $tradE.pages[$p].list) { $modificado = $true }
            }
        }
    } 
    # Se for CommonEvents
    else {
        for ($i = 0; $i -lt $jsonOrig.Count; $i++) {
            if ($null -eq $jsonOrig[$i]) { continue }
            if (Processar-Lista $jsonOrig[$i].list $jsonTrad[$i].list) { $modificado = $true }
        }
    }

    if ($modificado) {
        $jsonTrad | ConvertTo-Json -Depth 100 | Set-Content $caminhoTrad -Encoding UTF8
        Write-Host "Consertado: $(Split-Path $caminhoTrad -Leaf)" -ForegroundColor Green
    }
}

# Executar para Mapas
Get-ChildItem -Path $pastaOriginal -Filter "Map*.json" | ForEach-Object {
    Reparar-Json $_.FullName (Join-Path $pastaTraduzida $_.Name)
}

# Executar para CommonEvents
Reparar-Json (Join-Path $pastaOriginal "CommonEvents.json") (Join-Path $pastaTraduzida "CommonEvents.json")

Write-Host "`nReparo concluído!" -ForegroundColor Cyan
pause