# Путь к финальному CSV
$OutputPath = "C:\exports\ad_users.csv"

# Группы пользователей (например, OU = подразделение)
Get-ADUser -Filter * -Properties DisplayName, Department, DistinguishedName |
    Select-Object `
        SamAccountName,
        DisplayName,
        @{Name="OU";Expression={($_.DistinguishedName -split ',') -match '^OU=.*' | ForEach-Object { ($_ -replace '^OU=','') } | Select-Object -First 1 }} |
    Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
