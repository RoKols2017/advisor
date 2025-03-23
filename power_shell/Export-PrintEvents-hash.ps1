# Путь к файлу
$OutputPath = "C:\Temp\print_events.json"

# Получаем события печати (EventID 307)
Get-WinEvent -LogName "Microsoft-Windows-PrintService/Operational" -FilterXPath "*[System[(EventID=307)]]" |
    ForEach-Object {
        $xml = [xml]$_.ToXml()

        # Извлекаем поля
        $time     = $_.TimeCreated
        $user     = $xml.Event.UserData.DocumentPrinted.Param3
        $docName  = $xml.Event.UserData.DocumentPrinted.Param2
        $printer  = $xml.Event.UserData.DocumentPrinted.Param5
        $computer = $xml.Event.UserData.DocumentPrinted.Param4
        $port     = $xml.Event.UserData.DocumentPrinted.Param6
        $bytes    = [int]$xml.Event.UserData.DocumentPrinted.Param7
        $pages    = [int]$xml.Event.UserData.DocumentPrinted.Param8

        # 🔐 Создаём хеш по ключевым полям
        $hashInput = "$($time.ToUniversalTime().ToString('s'))|$user|$docName|$printer"
        $hashBytes = [System.Text.Encoding]::UTF8.GetBytes($hashInput)
        $sha256    = [System.Security.Cryptography.SHA256]::Create()
        $hash      = [System.BitConverter]::ToString($sha256.ComputeHash($hashBytes)) -replace "-", ""

        # Формируем JSON-объект
        [PSCustomObject]@{
            TimeCreated  = $time
            Param1       = $null             # необязательное поле
            Param2       = $docName
            Param3       = $user
            Param4       = $computer
            Param5       = $printer
            Param6       = $port
            Param7       = $bytes
            Param8       = $pages
            JobID        = $hash             # 💥 у тебя теперь уникальный ID
        }
    } | ConvertTo-Json -Depth 3 | Set-Content -Path $OutputPath -Encoding UTF8
