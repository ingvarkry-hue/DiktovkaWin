# Удаление DiktovkaWin: Win+R -> powershell -ExecutionPolicy Bypass -File C:\DiktovkaWin\uninstall.ps1
$ErrorActionPreference = 'SilentlyContinue'
Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "C:\DiktovkaWin\*" } | Stop-Process -Force
$Wsh = New-Object -ComObject WScript.Shell
Remove-Item "$env:USERPROFILE\Desktop\DiktovkaWin.lnk" -Force
Remove-Item "$([Environment]::GetFolderPath('Startup'))\DiktovkaWin.lnk" -Force
Set-Location $env:USERPROFILE
Remove-Item "C:\DiktovkaWin" -Recurse -Force
Write-Host "DiktovkaWin удалена."
