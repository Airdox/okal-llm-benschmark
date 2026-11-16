Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

param (
    [string]$OutputPath = "E:\okal llm benschmark\data\screenshots\desktop_screenshot.png"
)

$dir = [System.IO.Path]::GetDirectoryName($OutputPath)
if (-not [System.IO.Directory]::Exists($dir)) {
    [System.IO.Directory]::CreateDirectory($dir) | Out-Null
}

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $bitmap.Size)
$bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "Screenshot captured successfully: $OutputPath"
