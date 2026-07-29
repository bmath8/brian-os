# Pulls the fleet's local models sequentially, logging progress + completion.
$log = "C:\Brian\02_Projects\brian-os-fleet\logs\model_pull.log"
"=== model pull started $(Get-Date -Format o) ===" | Out-File $log
$models = @("qwen3:14b","qwen3:8b","deepseek-r1:14b")
foreach ($m in $models) {
    "[$(Get-Date -Format HH:mm:ss)] pulling $m ..." | Add-Content $log
    ollama pull $m *>> $log
    if ($LASTEXITCODE -eq 0) { "[$(Get-Date -Format HH:mm:ss)] DONE $m" | Add-Content $log }
    else { "[$(Get-Date -Format HH:mm:ss)] FAILED $m (exit $LASTEXITCODE)" | Add-Content $log }
}
"=== all pulls finished $(Get-Date -Format o) ===" | Add-Content $log
ollama list *>> $log
