$docxPath = "C:\Users\Kamaljit\Downloads\Groundwater_STGNN_Research_Paper_HINDI.docx"
$pdfPath = "C:\Users\Kamaljit\Downloads\Groundwater_STGNN_Research_Paper_HINDI.pdf"

Write-Host "Starting Word Application COM automation..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    Write-Host "Opening document: $docxPath"
    $doc = $word.Documents.Open($docxPath, $false, $true, $false)
    Write-Host "Exporting to High-Resolution PDF: $pdfPath"
    $doc.ExportAsFixedFormat($pdfPath, 17, $false, 0)
    $doc.Close([ref]0)
    Write-Host "SUCCESS: PDF created successfully at $pdfPath"
} catch {
    Write-Host "Fallback to SaveAs due to: $_"
    if ($doc) {
        $doc.SaveAs([ref]$pdfPath, [ref]17)
        $doc.Close([ref]0)
    }
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
