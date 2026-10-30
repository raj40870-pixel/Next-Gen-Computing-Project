$docxPath = "C:\Users\Kamaljit\OneDrive\Desktop\GroundWatch_CA2_Project_Report_MASTER.docx"
$pdfPath = "C:\Users\Kamaljit\OneDrive\Desktop\GroundWatch_CA2_Project_Report_MASTER.pdf"

Write-Host "Converting $docxPath to $pdfPath ..."
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = [Microsoft.Office.Interop.Word.WdAlertLevel]::wdAlertsNone

try {
    $doc = $word.Documents.Open($docxPath, $false, $true, $false)
    $doc.ExportAsFixedFormat($pdfPath, 17, $false, 0)
    $doc.Close([ref]0)
    Write-Host "SUCCESS: PDF created at $pdfPath"
} catch {
    Write-Host "Error: $_"
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
