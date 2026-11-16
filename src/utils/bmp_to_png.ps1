param (
    [Parameter(Mandatory=$true)][string]$InputBmp,
    [Parameter(Mandatory=$true)][string]$OutputPng
)

Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile($InputBmp)
$img.Save($OutputPng, [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()
Write-Host "Saved PNG: $OutputPng"
