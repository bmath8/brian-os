# Host resource probe — true Windows RAM/commit/VRAM (WSL's /proc/meminfo only sees the VM).
# Writes comms/resource_status.json (readable by WSL agents at /mnt/c). Run via WSL interop or host.
$o = Get-CimInstance Win32_OperatingSystem
$ramPct = [math]::Round((1 - ($o.FreePhysicalMemory / $o.TotalVisibleMemorySize)) * 100)
$ramFreeGB = [math]::Round($o.FreePhysicalMemory / 1MB, 1)
$ramTotGB = [math]::Round($o.TotalVisibleMemorySize / 1MB, 1)
$commit = [math]::Round((Get-Counter '\Memory\% Committed Bytes In Use' -EA SilentlyContinue).CounterSamples.CookedValue)
$vram = (& nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>$null) -split ','
$vu = 0; $vt = 0
if ($vram.Count -ge 2) { $vu = [int]$vram[0].Trim(); $vt = [int]$vram[1].Trim() }
$vfree = if ($vt -gt 0) { $vt - $vu } else { 0 }
$obj = [ordered]@{
  ts = (Get-Date -Format s); ram_pct = $ramPct; ram_free_gb = $ramFreeGB; ram_total_gb = $ramTotGB
  commit_pct = $commit; vram_used_mb = $vu; vram_total_mb = $vt; vram_free_mb = $vfree
}
$json = $obj | ConvertTo-Json -Compress
$json | Set-Content "C:\Brian\02_Projects\brian-os-fleet\comms\resource_status.json"
$json
