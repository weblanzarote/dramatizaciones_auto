param(
  [Parameter(Mandatory = $true)]
  [string]$Project,

  [string]$TxtName = 'texto.txt',
  [string]$Resolution = '1920x1080',
  [ValidateSet('contain','cover')][string]$Fit = 'contain',
  [switch]$DryRun,
  [switch]$BurnSubs,
  [switch]$EmbedSubsSoft,
  [switch]$SubsWithSpeaker,
  [string]$SubsFont = 'Arial',
  [double]$SubsFontsize = 7.0,
  [int]$SubsMarginV = 100,
  [int]$SubsOutline = 2,
  [int]$SubsAlign = 2,
  [int]$SubsShadow = 1
)

$ErrorActionPreference = 'Stop'

$Base = Split-Path -LiteralPath $MyInvocation.MyCommand.Path
Set-Location $Base

$TXT  = Join-Path $Project $TxtName
$IMGS = Join-Path $Project 'images'
$OUT  = Join-Path $Project 'Out'
$MP4  = Join-Path $OUT "$Project.mp4"
$SRT  = Join-Path $OUT "$Project.srt"

$argsList = @(
  $TXT, '--images-dir', $IMGS, '--outdir', $OUT,
  '--video-out', $MP4, '--subs-out', $SRT,
  '--resolution', $Resolution, '--fps', '30',
  '--fit', $Fit, '--pad-ms', '200',
  '--model', 'eleven_multilingual_v2', '--ext', '.mp3'
)

if ($DryRun) { $argsList += '--dry-run' }
if ($SubsWithSpeaker) { $argsList += '--subs-with-speaker' }
if ($BurnSubs)        { $argsList += '--burn-subs' }
if ($EmbedSubsSoft)   { $argsList += '--embed-subs-soft' }
if ($BurnSubs) { $argsList += '--burn-subs' }
$argsList += @('--subs-align', $SubsAlign, '--subs-font', $SubsFont, '--subs-fontsize', $SubsFontsize,
               '--subs-margin-v', $SubsMarginV, '--subs-outline', $SubsOutline,
               '--subs-shadow', $SubsShadow)

python .\generate_audiovideo_from_txt_drama.py @argsList
