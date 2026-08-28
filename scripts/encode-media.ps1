$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$OutputDir = Join-Path $ProjectRoot "public\media\video"
$LogDir = Join-Path $ProjectRoot ".qa\encode-logs"
$SourceRoot = "E:\OneDrive\Desktop\StoreoPatch"
$Ffmpeg = "C:\Users\周亚楠\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

New-Item -ItemType Directory -Force -Path $OutputDir, $LogDir | Out-Null

$Jobs = @(
    @{ Name = "placement"; Source = "扔到桶\夹到桶-4K60 无音乐.mp4"; Start = "108"; Duration = "18"; Filter = "scale=1280:720:flags=lanczos,fps=30,format=yuv420p"; Poster = "6" },
    @{ Name = "picking"; Source = "pick玩具\pick 玩具 4K60 无声音.mp4"; Start = "74"; Duration = "18"; Filter = "scale=1280:720:flags=lanczos,fps=30,format=yuv420p"; Poster = "6" },
    @{ Name = "peg"; Source = "插销\插销 4K60 无音频.mp4"; Start = "8.6"; Duration = "9.4"; Filter = "scale=1280:720:flags=lanczos,fps=30,format=yuv420p"; Poster = "3" },
    @{ Name = "bowl"; Source = "碗\碗 4k60.mp4"; Start = "18"; Duration = "12"; Filter = "scale=1280:720:flags=lanczos,fps=30,format=yuv420p"; Poster = "3" },
    @{ Name = "cup"; Source = "夹杯子\夹杯子 4K60 无音频.mp4"; Start = "7.2"; Duration = "5.5"; Filter = "scale=1280:720:flags=lanczos,fps=30,format=yuv420p"; Poster = "2" },
    @{ Name = "picnic"; Source = "野餐袋\Picnic_Bag01.mp4"; Start = "12"; Duration = "38"; Filter = "setpts=0.5*PTS,scale=1280:720:flags=lanczos,fps=30,format=yuv420p"; Poster = "6" }
)

function Start-EncodeJob($Job) {
    $Source = Join-Path $SourceRoot $Job.Source
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing source video: $Source"
    }

    $Output = Join-Path $OutputDir ($Job.Name + ".mp4")
    $Stdout = Join-Path $LogDir ($Job.Name + ".stdout.log")
    $Stderr = Join-Path $LogDir ($Job.Name + ".stderr.log")
    $Args = @(
        "-hide_banner", "-y", "-ss", $Job.Start, "-i", ('"' + $Source + '"'),
        "-t", $Job.Duration, "-vf", $Job.Filter,
        "-an", "-map_metadata", "-1",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-profile:v", "high", "-level:v", "4.1", "-threads", "7",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", ('"' + $Output + '"')
    )

    return Start-Process -FilePath $Ffmpeg -ArgumentList $Args -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -WindowStyle Hidden -PassThru
}

for ($Index = 0; $Index -lt $Jobs.Count; $Index += 2) {
    $Batch = $Jobs[$Index..([Math]::Min($Index + 1, $Jobs.Count - 1))]
    $Processes = @()
    foreach ($Job in $Batch) {
        $Existing = Join-Path $OutputDir ($Job.Name + ".mp4")
        if ((Test-Path -LiteralPath $Existing) -and (Get-Item -LiteralPath $Existing).Length -gt 100000) {
            continue
        }
        $Processes += [PSCustomObject]@{ Job = $Job; Process = Start-EncodeJob $Job }
    }
    foreach ($Entry in $Processes) {
        $Entry.Process.WaitForExit()
        $Entry.Process.Refresh()
        $Encoded = Join-Path $OutputDir ($Entry.Job.Name + ".mp4")
        $HasValidOutput = (Test-Path -LiteralPath $Encoded) -and (Get-Item -LiteralPath $Encoded).Length -gt 100000
        if (-not $HasValidOutput) {
            throw "Encoding failed for $($Entry.Job.Name). See $LogDir."
        }
    }
}

foreach ($Job in $Jobs) {
    $Video = Join-Path $OutputDir ($Job.Name + ".mp4")
    $Poster = Join-Path $OutputDir ($Job.Name + ".jpg")
    & $Ffmpeg -hide_banner -loglevel error -y -ss $Job.Poster -i $Video -frames:v 1 -vf "scale=1280:720:flags=lanczos" -q:v 2 $Poster
    if ($LASTEXITCODE -ne 0) {
        throw "Poster extraction failed for $($Job.Name)."
    }
}

"completed" | Set-Content -LiteralPath (Join-Path $LogDir "status.txt") -Encoding ascii
