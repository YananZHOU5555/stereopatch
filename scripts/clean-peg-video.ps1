param(
  [string]$InputVideo = ".\public\media\video-graded\peg.mp4",
  [string]$OutputVideo = ".\public\media\video-graded\peg-clean.mp4",
  [string]$DirtMask = ".\.qa\peg-cleanup\peg_dirt_mask.png",
  [string]$BackgroundPlate = ".\.qa\peg-cleanup\peg_background_plate.png",
  [double]$DurationSeconds = 9.4,
  [string]$Ffmpeg = "C:\Users\周亚楠\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
)

$ErrorActionPreference = "Stop"

foreach ($path in @($InputVideo, $DirtMask, $BackgroundPlate, $Ffmpeg)) {
  if (-not (Test-Path -LiteralPath $path)) {
    throw "Required input not found: $path"
  }
}

$outputDirectory = Split-Path -Parent $OutputVideo
if ($outputDirectory) {
  New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
}

$filter = @"
[0:v]split=3[base][repairin][compare];
[repairin]removelogo=f='$($DirtMask -replace '\\','\\\\')'[repaired];
[compare]boxblur=10:1[current_low];
[2:v]boxblur=10:1[plate_low];
[current_low][plate_low]blend=all_mode=difference,format=gray,geq=lum='if(lte(lum(X,Y),45),255,0)'[background_visible];
[1:v]format=gray[static_mask];
[static_mask][background_visible]blend=all_mode=multiply[dynamic_mask];
[base][repaired][dynamic_mask]maskedmerge,format=yuv420p[out]
"@ -replace "`r?`n", ""

& $Ffmpeg `
  -hide_banner -loglevel warning `
  -i $InputVideo `
  -loop 1 -framerate 30 -i $DirtMask `
  -loop 1 -framerate 30 -i $BackgroundPlate `
  -filter_complex $filter `
  -map "[out]" -map_metadata 0 -t $DurationSeconds `
  -an -c:v libx264 -preset slow -crf 15 -pix_fmt yuv420p `
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 `
  -movflags +faststart -y $OutputVideo

if ($LASTEXITCODE -ne 0) {
  throw "ffmpeg failed with exit code $LASTEXITCODE"
}

Write-Host "Created $OutputVideo"
