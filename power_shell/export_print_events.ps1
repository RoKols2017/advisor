<#
.SYNOPSIS
    Экспорт событий печати (Event ID 307) в JSON с учётом новых событий и поддержкой параметров запуска.

.DESCRIPTION
    Скрипт предназначен для запуска через Планировщик задач или вручную.
    Поддерживает параметры -Start и -End, либо использует файл-индикатор последнего запуска.
    Сохраняет выгрузку в JSON-файл с динамическим именем по дате и времени начала.
    Для надёжности внедрён 1-минутный буфер, исключающий потерю событий.
    Все расчёты ведутся во времени UTC, чтобы обеспечить универсальность вне зависимости от часового пояса.

.PARAMETER Start
    (необязательный) Время начала в формате ISO 8601, например "2025-03-25T06:00:00"

.PARAMETER End
    (необязательный) Время окончания в формате ISO 8601, например "2025-03-25T18:00:00"

.NOTES
    - Используется событие 307 из лога "Microsoft-Windows-PrintService/Operational"
    - События фильтруются по TimeCreated с учётом UTC
    - last_run.txt используется как fallback при отсутствии параметров
    - Дубли допускаются (1 минута перекрытия)
    - Выходной JSON содержит уникальный JobID (SHA256 от ключевых полей)
#>

param (
    [string]$Start,
    [string]$End
)

# === Настройки ===
$OutputDir = "C:\Temp"
$LastRunFile = Join-Path $OutputDir "last_run.txt"

# === Подготовка диапазона дат ===
$now = (Get-Date).ToUniversalTime()
$startTime = $null
$endTime = $null

# Используем параметры, если переданы
if ($Start -and $End) {
    try {
        $startTime = [DateTime]::Parse($Start).ToUniversalTime()
        $endTime   = [DateTime]::Parse($End).ToUniversalTime()
    } catch {
        Write-Host "❌ Ошибка парсинга дат из параметров"
        exit 1
    }
}
# Если параметров нет, пробуем last_run.txt
elseif (Test-Path $LastRunFile) {
    try {
        $lastRunText = Get-Content $LastRunFile -Raw
        $startTime = [DateTime]::Parse($lastRunText).ToUniversalTime()
        $endTime = $now
    } catch {
        Write-Host "❌ Ошибка чтения файла last_run.txt"
        exit 1
    }
}
# Если параметров и файла нет — выгружаем всё
else {
    Write-Host "⚠️ Параметры не переданы и файл last_run.txt не найден. Выполняется полная выгрузка."
    $startTime = [DateTime]"2000-01-01T00:00:00Z"
    $endTime = $now
}

# === Формируем имя выходного файла ===
$filenamePrefix = $startTime.ToString("yyyy-MM-dd-HH-mm")
$outputFile = Join-Path $OutputDir "$filenamePrefix-prn-event.json"

Write-Host "📤 Диапазон: $startTime UTC ➡ $endTime UTC"
Write-Host "📁 Файл выгрузки: $outputFile"

# === Получение событий ===
$events = Get-WinEvent -LogName "Microsoft-Windows-PrintService/Operational" -FilterXPath "*[System[(EventID=307)]]" |
    Where-Object {
        $_.TimeCreated.ToUniversalTime() -ge $startTime -and $_.TimeCreated.ToUniversalTime() -le $endTime
    } |
    ForEach-Object {
        $xml = [xml]$_.ToXml()

        $time     = $_.TimeCreated
        $user     = $xml.Event.UserData.DocumentPrinted.Param3
        $docName  = $xml.Event.UserData.DocumentPrinted.Param2
        $printer  = $xml.Event.UserData.DocumentPrinted.Param5
        $computer = $xml.Event.UserData.DocumentPrinted.Param4
        $port     = $xml.Event.UserData.DocumentPrinted.Param6
        $bytes    = [int]$xml.Event.UserData.DocumentPrinted.Param7
        $pages    = [int]$xml.Event.UserData.DocumentPrinted.Param8

        $hashInput = "$($time.ToUniversalTime().ToString('s'))|$user|$docName|$printer"
        $hashBytes = [System.Text.Encoding]::UTF8.GetBytes($hashInput)
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        $hash = [System.BitConverter]::ToString($sha256.ComputeHash($hashBytes)) -replace "-", ""

        [PSCustomObject]@{
            TimeCreated  = $time
            Param1       = $null
            Param2       = $docName
            Param3       = $user
            Param4       = $computer
            Param5       = $printer
            Param6       = $port
            Param7       = $bytes
            Param8       = $pages
            JobID        = $hash
        }
    }

# === Сохранение JSON ===
if ($events.Count -gt 0) {
    $events | ConvertTo-Json -Depth 3 | Set-Content -Path $outputFile -Encoding UTF8
    Write-Host "✅ Успешно выгружено: $($events.Count) событий"

    # Обновляем last_run.txt с буфером -1 минута
    $newStartTime = $endTime.AddMinutes(-1)
    $newStartTime.ToString("yyyy-MM-ddTHH:mm:ssZ") | Set-Content -Path $LastRunFile -Encoding UTF8
    Write-Host "📌 Обновлён файл last_run.txt: $newStartTime (UTC -1м)"
}
else {
    Write-Host "ℹ️ Нет новых событий в заданном диапазоне."
}
