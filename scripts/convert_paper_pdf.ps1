$docxPath = "C:\Users\Kamaljit\Downloads\Groundwater_STGNN_Research_Paper_FINAL.docx"
$pdfPath = "C:\Users\Kamaljit\Downloads\Groundwater_STGNN_Research_Paper_FINAL.pdf"

Write-Host "Starting Word Application COM automation..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    Write-Host "Opening document: $docxPath"
    $doc = $word.Documents.Open($docxPath)
    Write-Host "Exporting to PDF: $pdfPath"
    # wdFormatPDF = 17
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    $doc.Close([ref]0) # wdDoNotSaveChanges
    Write-Host "SUCCESS: PDF created successfully at $pdfPath"
} catch {
    Write-Host "ERROR: $_"
} finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}
