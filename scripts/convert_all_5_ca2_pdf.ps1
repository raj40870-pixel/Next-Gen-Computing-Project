$folder = "C:\Users\Kamaljit\OneDrive\Desktop\CA2_Individual_Reports"
$files = Get-ChildItem -Path $folder -Filter "*.docx"

Write-Host "Starting Word Application for batch conversion..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    foreach ($f in $files) {
        $pdfPath = [System.IO.Path]::ChangeExtension($f.FullName, ".pdf")
        Write-Host "Converting $($f.Name) to PDF..."
        $doc = $word.Documents.Open($f.FullName, $false, $true, $false)
        $doc.ExportAsFixedFormat($pdfPath, 17, $false, 0)
        $doc.Close([ref]0)
        Write-Host "SUCCESS: Created $pdfPath"
    }
} catch {
    Write-Host "Error occurred: $_"
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
