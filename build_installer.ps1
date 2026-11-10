$ISCC = "C:\Users\bernd\AppData\Local\Programs\Inno Setup 6\ISCC.exe"

Write-Host "=== PyInstaller ===" -ForegroundColor Cyan
python -m PyInstaller --clean -y buckezz.spec
if ($LASTEXITCODE -ne 0) { Write-Host "PyInstaller FAILED" -ForegroundColor Red; exit 1 }

Write-Host "=== Inno Setup ===" -ForegroundColor Cyan
& $ISCC installer.iss
if ($LASTEXITCODE -ne 0) { Write-Host "ISCC FAILED" -ForegroundColor Red; exit 1 }

Write-Host "=== DONE ===" -ForegroundColor Green
Write-Host "Installer: dist_installer\BuckezzDesktop_Setup.exe"
