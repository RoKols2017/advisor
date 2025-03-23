# Требует PowerShell 7+
# Запускать через: pwsh -File Export-PrintEvents.ps1

$OutputPath = "C:\exports\print_events.csv"
$DaysBack = 7  # количество дней для анализа
$StartTime = (Get-Date).AddDays(-$DaysBack)

# Получаем все события за нужный период (быстрее, чем XPath)
$events = Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-PrintService/Operational'
    Id = 307
    StartTime = $StartTime
} -ErrorAction Stop

Write-Host "Найдено событий: $($events.Count)"

# Параллельная обработка событий (PowerShell 7+)
$processed = $events | ForEach-Object -Parallel {
    try {
        $xml = [xml]$_.ToXml()
        $data = $xml.Event.UserData.DocumentPrinted

        [PSCustomObject]@{
            TimeCreated   = $_.TimeCreated
            UserName      = $data.Param2
            DocumentName  = $data.Param1
            PrinterName   = $data.Param5
            JobID         = $data.Param6
            Pages         = [int]$data.Param4
            Bytes         = [int]$data.Param3
        }
    } catch {
        Write-Warning "Ошибка при обработке события: $_"
    }
} -ThrottleLimit 8  # можно увеличить в зависимости от CPU

# Сохраняем результат
$processed | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

Write-Host "✅ Экспорт завершён: $OutputPath"
