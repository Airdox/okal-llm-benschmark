$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$args = "--remote-debugging-port=9222 --user-data-dir=E:\okal_chrome_profile --no-first-run --no-default-browser-check https://huggingface.co/"
$shell = New-Object -ComObject Shell.Application
$shell.ShellExecute($chrome, $args, "", "open", 1)
Write-Host "ShellExecute Chrome called."
