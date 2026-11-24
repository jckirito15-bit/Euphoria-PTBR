$ErrorActionPreference = 'Stop'
$raizInfra = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $raizInfra
$pastaDownload = Join-Path $raizInfra 'trabalho/infra'
New-Item -ItemType Directory -Force $pastaDownload | Out-Null
# Versão estável verificada em https://www.renpy.org/latest.html em 2026-11-03.
$pacotesInfra = @(
    @{Nome='sdk'; Hash='ff57648f9c04f27e381c48af6d8e3ee3cdec296bed4d3831f47f09b0a71b505e'},
    @{Nome='rapt'; Hash='8a12be34a2f5238d125ff6dd76a56772fd8e44838af864f81bca82c1059b00e6'}
)
foreach ($pacoteInfra in $pacotesInfra) {
    $arquivoInfra = Join-Path $pastaDownload ($pacoteInfra.Nome + '.zip')
    if (!(Test-Path -LiteralPath $arquivoInfra)) {
        & curl.exe -L --fail --retry 3 ('https://www.renpy.org/dl/8.5.3/renpy-8.5.3-' + $pacoteInfra.Nome + '.zip') -o $arquivoInfra
        if ($LASTEXITCODE) { throw 'Falha ao baixar SDK/RAPT' }
    }
    if ((Get-FileHash -LiteralPath $arquivoInfra -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pacoteInfra.Hash) {
        throw ('Checksum inválido: ' + $arquivoInfra)
    }
}
if (!(Test-Path -LiteralPath 'renpy-sdk/renpy.py')) {
    Expand-Archive -LiteralPath (Join-Path $pastaDownload 'sdk.zip') -DestinationPath $pastaDownload -Force
    Move-Item -LiteralPath (Join-Path $pastaDownload 'renpy-8.5.3-sdk') -Destination (Join-Path $raizInfra 'renpy-sdk')
}
if (!(Test-Path -LiteralPath 'renpy-sdk/rapt/android.py')) {
    Expand-Archive -LiteralPath (Join-Path $pastaDownload 'rapt.zip') -DestinationPath (Join-Path $raizInfra 'renpy-sdk') -Force
}
Set-Content -LiteralPath 'renpy-sdk/rapt/sdk.txt' -Value (Join-Path $raizInfra 'android-sdk') -Encoding ascii
if (!(Test-Path -LiteralPath 'renpy/euphoria/game/traducao.json')) {
    Copy-Item -LiteralPath 'tools/infra/traducao_exemplo.json' -Destination 'renpy/euphoria/game/traducao.json'
}
if (!$env:JAVA_HOME) { $env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.13.9-hotspot' }
$sdkmanagerInfra = Get-ChildItem -LiteralPath 'android-sdk/cmdline-tools' -Recurse -Filter sdkmanager.bat | Select-Object -First 1
if (!$sdkmanagerInfra) { throw 'SDK Android ausente: instale command-line tools em android-sdk/' }
& $sdkmanagerInfra.FullName 'platform-tools' 'platforms;android-36' 'build-tools;35.0.0'
if ($LASTEXITCODE) { throw 'Falha ao preparar SDK Android (verifique licenças e rede)' }
Write-Output 'RenPy 8.5.3 + RAPT preparados. Execute tools\build_apk.bat.'
