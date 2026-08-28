$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$OutputDir = Join-Path $ProjectRoot "public\media\video-graded"
$LogDir = Join-Path $ProjectRoot ".qa\grade-logs"
$SourceRoot = "E:\OneDrive\Desktop\StoreoPatch"
$Ffmpeg = "C:\Users\周亚楠\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"

# Evidence-preserving grade derived from the peg canary:
# - gentle toe lift to retain black-robot detail;
# - restrained highlight roll-off on the white work surface;
# - slight red/magenta neutralization;
# - no local relighting, vignette, blur, or hue-selective object recoloring.
$EvidenceGrade = "curves=master='0/0.032 0.080/0.118 0.250/0.300 0.500/0.525 0.800/0.785 1/0.950',colorbalance=rs=-0.018:bs=0.015:rm=-0.014:bm=0.012:rh=-0.012:bh=0.008,eq=saturation=0.95"
$Finish = "scale=1920:1080:flags=lanczos,fps=30,unsharp=5:5:0.22:3:3:0,format=yuv420p"

$Jobs = @(
    @{ Name = "placement"; Source = "扔到桶\夹到桶-4K60 无音乐.mp4"; Start = "108"; Duration = "18"; Speed = ""; Poster = "6" },
    @{ Name = "picking"; Source = "pick玩具\pick 玩具 4K60 无声音.mp4"; Start = "74"; Duration = "18"; Speed = ""; Poster = "6" },
    @{ Name = "peg"; Source = "插销\插销 4K60 无音频.mp4"; Start = "8.6"; Duration = "9.4"; Speed = ""; Poster = "3" },
    @{ Name = "bowl"; Source = "碗\碗 4k60.mp4"; Start = "18"; Duration = "12"; Speed = ""; Poster = "3" },
    @{ Name = "cup"; Source = "夹杯子\夹杯子 4K60 无音频.mp4"; Start = "7.2"; Duration = "5.5"; Speed = ""; Poster = "2" },
    @{ Name = "picnic"; Source = "野餐袋\Picnic_Bag01.mp4"; Start = "12"; Duration = "38"; Speed = "setpts=0.5*PTS"; Poster = "6" }
)

New-Item -ItemType Directory -Force -Path $OutputDir, $LogDir | Out-Null

function Start-GradeJob($Job) {
    $Source = Join-Path $SourceRoot $Job.Source
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Missing source video: $Source"
    }

    $FilterParts = @($EvidenceGrade)
    if ($Job.Speed) { $FilterParts += $Job.Speed }
    $FilterParts += $Finish
    $Filter = $FilterParts -join ","

    $Output = Join-Path $OutputDir ($Job.Name + ".mp4")
    $Stdout = Join-Path $LogDir ($Job.Name + ".stdout.log")
    $Stderr = Join-Path $LogDir ($Job.Name + ".stderr.log")
    $Args = @(
        "-hide_banner", "-y", "-ss", $Job.Start, "-i", ('"' + $Source + '"'),
        "-t", $Job.Duration, "-vf", ('"' + $Filter + '"'),
        "-an", "-map_metadata", "-1",
        "-c:v", "libx264", "-preset", "slow", "-crf", "19",
        "-profile:v", "high", "-level:v", "4.2", "-threads", "0",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", ('"' + $Output + '"')
    )

    return Start-Process -FilePath $Ffmpeg -ArgumentList $Args -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -WindowStyle Hidden -PassThru
}

# Two concurrent 4K decodes keep CPU utilization high without multiplying memory pressure.
for ($Index = 0; $Index -lt $Jobs.Count; $Index += 2) {
    $Batch = $Jobs[$Index..([Math]::Min($Index + 1, $Jobs.Count - 1))]
    $Processes = foreach ($Job in $Batch) {
        $Existing = Join-Path $OutputDir ($Job.Name + ".mp4")
        if ((Test-Path -LiteralPath $Existing) -and (Get-Item -LiteralPath $Existing).Length -gt 100000) {
            continue
        }
        [PSCustomObject]@{ Job = $Job; Process = Start-GradeJob $Job }
    }

    foreach ($Entry in $Processes) {
        $Entry.Process.WaitForExit()
        $Entry.Process.Refresh()
        $Encoded = Join-Path $OutputDir ($Entry.Job.Name + ".mp4")
        $HasValidOutput = (Test-Path -LiteralPath $Encoded) -and (Get-Item -LiteralPath $Encoded).Length -gt 100000
        if (-not $HasValidOutput) {
            throw "Grading failed for $($Entry.Job.Name). See $LogDir."
        }
    }
}

foreach ($Job in $Jobs) {
    $Video = Join-Path $OutputDir ($Job.Name + ".mp4")
    $Poster = Join-Path $OutputDir ($Job.Name + ".jpg")
    & $Ffmpeg -hide_banner -loglevel error -y -ss $Job.Poster -i $Video -frames:v 1 -vf "scale=1920:1080:flags=lanczos" -q:v 2 $Poster
    if ($LASTEXITCODE -ne 0) {
        throw "Poster extraction failed for $($Job.Name)."
    }
}

"completed" | Set-Content -LiteralPath (Join-Path $LogDir "status.txt") -Encoding ascii
