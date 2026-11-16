$action = New-ScheduledTaskAction -Execute 'C:\Program Files\Google\Chrome\Application\chrome.exe' -Argument '--remote-debugging-port=9222 --user-data-dir=E:\okal_chrome_profile --no-first-run --no-default-browser-check https://huggingface.co/'
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
Register-ScheduledTask -TaskName 'LaunchChromeBenchmark' -Action $action -Principal $principal -Force | Out-Null
Start-ScheduledTask -TaskName 'LaunchChromeBenchmark'
Start-Sleep -Seconds 3
Get-ScheduledTask -TaskName 'LaunchChromeBenchmark' | Select-Object TaskName, State
