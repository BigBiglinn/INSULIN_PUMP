# Updates contents lists and page references in Word, then exports the PDF.
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open("$dir\Project_Report.docx")
    $doc.Repaginate()
    for ($i = 0; $i -lt 2; $i++) {
        foreach ($t in $doc.TablesOfContents) { $t.Update() }
        $doc.Fields.Update() | Out-Null
        $doc.Repaginate()
    }
    "pages: " + $doc.ComputeStatistics(2)
    $doc.Save()
    $doc.ExportAsFixedFormat("$dir\Project_Report.pdf", 17)
    $doc.Close()
} finally {
    $word.Quit()
}
