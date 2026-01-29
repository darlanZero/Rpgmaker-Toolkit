# Compara o CommonEvents original e traduzido e restaura apenas os comandos de plugin (356)
$pathOrig = "c:\Users\anime\Downloads\translation\Hentai4daily\えぶりーでぱんつ!!! 体験版Ver1.03\えぶりーでぱんつ!!!_体験版Ver.1.03\www\data\CommonEvents.json"
$pathTrad = "c:\Users\anime\Downloads\translation\Hentai4daily\えぶりーでぱんつ!!! 体験版Ver1.03\PantiesEverydayV2\www\data\CommonEvents.json"

$orig = Get-Content $pathOrig -Raw | ConvertFrom-Json
$trad = Get-Content $pathTrad -Raw | ConvertFrom-Json

for ($i=0; $i -lt $orig.Count; $i++) {
    if ($null -eq $orig[$i]) { continue }
    $oList = $orig[$i].list
    $tList = $trad[$i].list
    for ($j=0; $j -lt $oList.Count; $j++) {
        # Código 356 é Plugin Command. O Translator++ costuma estragar as strings aqui.
        if ($oList[$j].code -eq 356) {
            $tList[$j].parameters[0] = $oList[$j].parameters[0]
        }
    }
}

$trad | ConvertTo-Json -Depth 100 | Set-Content $pathTrad -Encoding UTF8
Write-Host "Lógica de plugins restaurada!" -ForegroundColor Green