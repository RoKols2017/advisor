# Параметры
$OutputPath = "C:\Temp\print_events.json"
$DaysBack = 7
$StartTime = (Get-Date).AddDays(-$DaysBack)

# Получение событий печати (307) за последние N дней
$events = Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-PrintService/Operational'
    Id = 307
    StartTime = $StartTime
} -ErrorAction Stop

Write-Host "📄 Найдено событий: $($events.Count)"

# Подготовка данных
$export = @()

foreach ($e in $events) {
    try {
        $xml = [xml]$e.ToXml()
        $data = $xml.Event.UserData.DocumentPrinted

        $eventObject = [PSCustomObject]@{
            TimeCreated = $e.TimeCreated
            Param1 = $data.Param1
            Param2 = $data.Param2
            Param3 = $data.Param3
            Param4 = $data.Param4
            Param5 = $data.Param5
            Param6 = $data.Param6
        }

        $export += $eventObject
    }
    catch {
        Write-Warning "❌ Ошибка в событии: $_"
    }
}

# Конвертация в JSON и сохранение
$export | ConvertTo-Json -Depth 3 | Out-File -FilePath $OutputPath -Encoding UTF8

Write-Host "✅ Экспорт в JSON завершён: $OutputPath"
