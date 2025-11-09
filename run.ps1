# run.ps1 (Versión 2.0 - Más inteligente)
# Detecta el modo -Remix al principio para un flujo de trabajo optimizado.

param(
  [string]$TextFile = "texto.txt",
  [string]$ImagesDir = "images",
  [string]$OutDir = "Out",
  [string]$Resolution = "1080x1920",
  [int]$Fps = 30,
  [ValidateSet("cover","contain")] [string]$Fit = "cover",
  [ValidateSet("length","uniform")] [string]$WordTiming = "length",
  [int]$MinSegMs = 120,
  [switch]$OverwriteAudio,
  [switch]$MediaKeepAudio,
  [double]$MediaAudioVol = $null,
  [switch]$MusicAudio,
  [double]$MusicAudioVol = 0.2,  
  [switch]$AlsoSrt,          
  [switch]$NoBurn,
  [switch]$KbSticky,
  [ValidateSet('loop','freeze','black','slow')] [string]$VideoFill = 'loop',
  [switch]$Remix,
  [ValidateSet('none','in','out')] [string]$KenBurns = 'none',
  [double]$KbZoom = 0.10,
  [ValidateSet('center','tl2br','tr2bl','bl2tr','br2tl','random')] [string]$KbPan = 'center'
)

if ($PSBoundParameters.ContainsKey('MediaAudioVol')) {
  if ($MediaAudioVol -lt 0 -or $MediaAudioVol -gt 1) {
    throw "MediaAudioVol debe estar entre 0.0 y 1.0"
  }
}


$ErrorActionPreference = "Stop"

# --- Rutas (corregido) ---
$ProjectDir = (Get-Location).Path
$ProjectName = Split-Path $ProjectDir -Leaf
$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$PyScript = Join-Path $RootDir "generate_audiovideo_from_txt_drama.py"
$TextPath = Join-Path $ProjectDir $TextFile

# Normaliza la carpeta de imágenes (relativa -> absoluta) y úsala en todo
$ImgPath   = Join-Path $ProjectDir $ImagesDir
$ImagesDir = $ImgPath
$MusicPath = Join-Path $ImagesDir "musica.mp3"

# Salidas
$OutPath   = Join-Path $ProjectDir $OutDir
$VideoOut  = Join-Path $OutPath "video.mp4"
$AssOut    = Join-Path $OutPath "typing.ass"


# --- LÓGICA PRINCIPAL MEJORADA ---

# Primero, creamos la carpeta de salida si no existe
New-Item -ItemType Directory -Force -Path $OutPath | Out-Null

# Si estamos en modo REMIX, tomamos un atajo
if ($Remix) {
    Write-Host ">> MODO REMIX: Regenerando y reemplazando pista de audio..."
    
    # Rutas específicas para el remix
    $RemixAudio = Join-Path $OutPath "audio_remix.mp3"
    $RemixVideoOut = Join-Path $OutPath ($ProjectName + "_remix.mp4")

    if (-not (Test-Path $VideoOut)) {
        throw "ERROR: No se encontró el vídeo base '$VideoOut'. Debes hacer un renderizado completo primero."
    }

    # 1. Llama a Python UNA SOLA VEZ para que genere solo el audio combinado
    # Pasamos solo los argumentos necesarios para el audio
    $pyArgsRemix = @(
        $TextPath,
        "--outdir", $OutPath,
        "--remix-audio-out", $RemixAudio,
        "--overwrite" # Forzamos la sobreescritura para regenerar los audios borrados
    )
    & python $PyScript @pyArgsRemix
    if ($LASTEXITCODE -ne 0) { throw "Python (remix) devolvió código $LASTEXITCODE" }

    # 2. Usa FFMPEG para unir el vídeo viejo y el audio nuevo (casi instantáneo)
    Write-Host ">> Combinando vídeo existente con nueva pista de audio..."
    & ffmpeg -y -i $VideoOut -i $RemixAudio -c:v copy -map 0:v:0 -map 1:a:0 $RemixVideoOut
    if ($LASTEXITCODE -ne 0) { throw "FFmpeg (remix) devolvió código $LASTEXITCODE" }
    
    Write-Host "✅ Remix listo. Vídeo final en: $RemixVideoOut"
    exit 0 # Salimos del script, hemos terminado.
}

# Si NO estamos en modo REMIX, procedemos con el renderizado completo
# --- FLUJO DE RENDERIZADO COMPLETO (como antes) ---

Write-Host ">> MODO RENDERIZADO COMPLETO: Generando vídeo base y ASS typing..."

$pyArgs = @(
  $TextFile,
  "--outdir", $OutPath,
  "--images-dir", $ImgPath,
  "--video-out", $VideoOut,
  "--resolution", $Resolution,
  "--ass-font", "Bebas Neue",
  "--ass-fontsize", "132",
  "--ass-margin-v", "320",
  "--subs-align", "2",
  "--ass-outline", "3",
  "--ass-shadow",  "1",
  "--subs-uppercase",
  "--fps", "$Fps",
  "--fit", $Fit,
  "--ass-typing-out", $AssOut,
  "--subs-word-timing", $WordTiming,
  "--subs-min-seg-ms", "$MinSegMs",
  "--subs-chunk-size", "3",
  "--subs-chunk-hold-ms", "0"
# (opcional) "--subs-chunk-prefix-all"
)

if ($MusicAudio) {
  if (Test-Path $MusicPath) {
    $pyArgs += @("--music-audio", "--music-audio-vol", ("{0:N2}" -f $MusicAudioVol).Replace(',', '.'))
  } else {
    Write-Host "⚠️ Aviso: 'musica.mp3' no encontrado en $ImagesDir. Se ignora -MusicAudio."
  }
}

if ($MediaKeepAudio) { $pyArgs += "--media-keep-audio" }
if ($PSBoundParameters.ContainsKey('MediaAudioVol')) {
  $pyArgs += @("--media-audio-vol", $MediaAudioVol)
}

if ($KenBurns -ne 'none') {
  $pyArgs += @("--kenburns", $KenBurns, "--kb-zoom", ("{0:N2}" -f $KbZoom).Replace(',', '.'), "--kb-pan", $KbPan, "--video-fill", $VideoFill)
  if ($KbSticky) { $pyArgs += "--kb-sticky" }
}
if ($AlsoSrt) {
  $SrtOut = Join-Path $OutPath ($ProjectName + ".srt")
  $pyArgs += @("--subs-out", $SrtOut, "--subs-with-speaker")
}
if ($OverwriteAudio) {
  $pyArgs += "--overwrite"
}

& python $PyScript @pyArgs
if ($LASTEXITCODE -ne 0) { throw "Python devolvió código $LASTEXITCODE" }

if (-not (Test-Path $VideoOut)) { throw "No se generó $VideoOut" }
if (-not (Test-Path $AssOut))   { throw "No se generó $AssOut" }

# === QUEMAR SUBTÍTULOS (si NO pasas -NoBurn) ===
if (-not $NoBurn -and (Test-Path $AssOut) -and (Test-Path $VideoOut)) {
  Push-Location $OutPath
  try {
    $FinalOut = Join-Path -Path "." -ChildPath ($ProjectName + "_typing.mp4")
    Write-Host ">> Quemando subtítulos (ASS) con fuente Bebas Neue -> $FinalOut"

    # 1) Copiar la fuente al proyecto
    $FontSrc     = 'C:\Users\webla\OneDrive\Desktop\RELATOS_EXTRAORDINARIOS\Fonts\Bebas\Bebas_Neue\BebasNeue-Regular.ttf'
    $FontsDirOut = Join-Path $PWD 'Fonts'
    New-Item -ItemType Directory -Force $FontsDirOut | Out-Null
    Copy-Item $FontSrc $FontsDirOut -Force

    # 2) Filtro con rutas RELATIVAS (evita "C:")
    $SubFilter = 'subtitles=typing.ass:fontsdir=./Fonts'

    # 3) Quemar
    & ffmpeg -y -i "video.mp4" -vf $SubFilter -c:v libx264 -preset veryfast -crf 20 -c:a copy "$FinalOut"
    if ($LASTEXITCODE -ne 0) { throw "FFmpeg devolvió código $LASTEXITCODE" }
  }
  finally { Pop-Location }
}


Write-Host "✅ Renderizado completo. Salida en: $OutPath"
