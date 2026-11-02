@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\GKcode.lnk'); $p=(Get-Command pythonw -ErrorAction SilentlyContinue).Source; if(-not $p){$p=(Get-Command python).Source}; $s.TargetPath=$p; $s.Arguments='\"%~dp0main.py\"'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0icon.ico'; $s.Save()"
echo Da tao GKcode tren Desktop.
pause
