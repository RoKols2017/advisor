# Путь к CSV
$OutputPath = "C:\temp\print_events.csv"

# Загружаем события печати (Event ID 307 = Print Success)
Get-WinEvent -LogName "Microsoft-Windows-PrintService/Operational" -FilterXPath "*[System[(EventID=307)]]" |
    ForEach-Object {
    $xml = [xml]$_.ToXml()
    $data = $xml.Event.UserData.DocumentPrinted

    $pagesRaw = $data.Param4
    $bytesRaw = $data.Param3

    $pages = 0
    $bytes = 0

    if ($pagesRaw -match '^\d+$') { $pages = [int]$pagesRaw }
    if ($bytesRaw -match '^\d+$') { $bytes = [int]$bytesRaw }

    [PSCustomObject]@{
        TimeCreated   = $_.TimeCreated
        UserName      = $data.Param2
        DocumentName  = $data.Param1
        PrinterName   = $data.Param5
        JobID         = $data.Param6
        Pages         = $pages
        Bytes         = $bytes
    }
}
 | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
