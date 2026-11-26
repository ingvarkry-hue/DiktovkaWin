# Установка DiktovkaWin — транскрибатор для KIMI и мессенджеров (Windows).
# Одна команда (Win+R, вставить, Enter):
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/ingvarkry-hue/DiktovkaWin/main/install.ps1 | iex"
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Base = "C:\DiktovkaWin"
$RepoRaw = "https://raw.githubusercontent.com/ingvarkry-hue/DiktovkaWin/main"

Write-Host "==> Проверяю Python..." -ForegroundColor Cyan
$py = $null
foreach ($cmd in @("py -3.12", "py -3", "python")) {
    try { & ($cmd.Split(' ')[0]) ($cmd.Split(' ') | Select-Object -Skip 1) --version 2>$null; if ($LASTEXITCODE -eq 0) { $py = $cmd; break } } catch {}
}
if (-not $py) {
    Write-Host "==> Ставлю Python 3.12 через winget..." -ForegroundColor Cyan
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --silent
    $py = "py -3.12"
}
& ($py.Split(' ')[0]) ($py.Split(' ') | Select-Object -Skip 1) --version

Write-Host "==> Создаю папку $Base..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force $Base | Out-Null
Set-Location $Base

Write-Host "==> Скачиваю файлы DiktovkaWin..." -ForegroundColor Cyan
foreach ($f in @("DiktovkaWin.py", "requirements.txt", "config.example.json", "icon.png")) {
    Invoke-RestMethod "$RepoRaw/$f" -OutFile "$Base\$f"
}

Write-Host "==> Создаю виртуальное окружение и ставлю библиотеки..." -ForegroundColor Cyan
& ($py.Split(' ')[0]) ($py.Split(' ') | Select-Object -Skip 1) -m venv "$Base\venv"
& "$Base\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$Base\venv\Scripts\python.exe" -m pip install -r "$Base\requirements.txt"

Write-Host "==> Подготавливаю config.json..." -ForegroundColor Cyan
if (-not (Test-Path "$Base\config.json")) { Copy-Item "$Base\config.example.json" "$Base\config.json" }

Write-Host "==> Скачиваю модель распознавания (~1,6 ГБ, один раз)..." -ForegroundColor Cyan
& "$Base\venv\Scripts\python.exe" "$Base\DiktovkaWin.py" --download

Write-Host "==> Создаю ярлыки (рабочий стол и автозапуск)..." -ForegroundColor Cyan
$Wsh = New-Object -ComObject WScript.Shell
$Target = "$Base\venv\Scripts\pythonw.exe"
$Args = "`"$Base\DiktovkaWin.py`""
$Wsh.CreateShortcut("$env:USERPROFILE\Desktop\DiktovkaWin.lnk").TargetPath = $Target
$lnk = $Wsh.CreateShortcut("$env:USERPROFILE\Desktop\DiktovkaWin.lnk")
$lnk.TargetPath = $Target; $lnk.Arguments = $Args; $lnk.WorkingDirectory = $Base
$lnk.IconLocation = "$Base\icon.png"; $lnk.Save()
$StartUp = [Environment]::GetFolderPath('Startup')
$lnk2 = $Wsh.CreateShortcut("$StartUp\DiktovkaWin.lnk")
$lnk2.TargetPath = $Target; $lnk2.Arguments = $Args; $lnk2.WorkingDirectory = $Base
$lnk2.IconLocation = "$Base\icon.png"; $lnk2.Save()

Write-Host ""
Write-Host "Готово! DiktovkaWin запущена." -ForegroundColor Green
Write-Host "Нажмите F8 (или свою клавишу из config.json) и говорите."
Start-Process -FilePath $Target -ArgumentList $Args -WorkingDirectory $Base
