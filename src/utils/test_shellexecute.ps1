$shell = New-Object -ComObject Shell.Application
$shell.ShellExecute("notepad.exe", "", "", "open", 1)
Write-Host "ShellExecute called successfully."
