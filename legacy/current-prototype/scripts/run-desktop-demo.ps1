param(
  [string]$GeometryFilePath = "C:\Users\D0n9\Desktop\suboff_solid.x_t",
  [string]$ApiBase = "http://127.0.0.1:8010",
  [int]$TimeoutSeconds = 180
)

if (-not (Test-Path $GeometryFilePath)) {
  throw "Geometry file not found: $GeometryFilePath"
}

function Decode-UnicodeLiteral {
  param([string]$Value)
  return [regex]::Unescape($Value)
}

function Wait-ApiReady {
  param(
    [string]$Url,
    [int]$Seconds
  )

  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    try {
      $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5
      if ($response.status -eq "ok") {
        return
      }
    } catch {
      Start-Sleep -Seconds 2
    }
  }

  throw "API did not become ready in time: $Url"
}

Write-Host "Waiting for backend health endpoint..." -ForegroundColor Cyan
Wait-ApiReady -Url "$ApiBase/api/health" -Seconds 60

Write-Host "Submitting desktop demo task..." -ForegroundColor Cyan
$taskDescription = Decode-UnicodeLiteral '\u5206\u6790\u6f5c\u8247\u5916\u5f62\u5728\u6df1\u6f5c\u7a33\u6001\u5de5\u51b5\u4e0b\u7684\u8868\u9762\u538b\u529b\u5206\u5e03\u4e0e\u963b\u529b\u7279\u5f81\u3002'
$operatingNotes = Decode-UnicodeLiteral '\u6df1\u6f5c\u7a33\u6001 benchmark \u98ce\u683c\u5de5\u51b5\u3002'

$createRaw = & curl.exe -s -X POST "$ApiBase/api/tasks" `
  -F "task_description=$taskDescription" `
  -F "task_type=pressure_distribution" `
  -F "geometry_family_hint=DARPA SUBOFF" `
  -F "operating_notes=$operatingNotes" `
  -F "geometry_file=@$GeometryFilePath"

if (-not $createRaw) {
  throw "Task creation returned an empty response."
}

$run = $createRaw | ConvertFrom-Json
$runId = $run.run_id
Write-Host "Created run: $runId" -ForegroundColor Green

Write-Host "Confirming workflow..." -ForegroundColor Cyan
$confirmBody = @{
  confirmed = $true
  reviewer_notes = (Decode-UnicodeLiteral '\u4f7f\u7528\u672c\u5730 SUBOFF \u51e0\u4f55\u81ea\u52a8\u63d0\u4ea4\u684c\u9762\u6f14\u793a\u4efb\u52a1\u3002')
} | ConvertTo-Json

$null = Invoke-RestMethod -Uri "$ApiBase/api/runs/$runId/confirm" -Method Post -Body $confirmBody -ContentType "application/json"

Write-Host "Polling run status..." -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ((Get-Date) -lt $deadline) {
  $detail = Invoke-RestMethod -Uri "$ApiBase/api/runs/$runId" -Method Get -TimeoutSec 10
  Write-Host ("Run status: {0} | stage: {1}" -f $detail.status, $detail.stage_label)
  if ($detail.status -eq "completed") {
    $runDir = Join-Path (Split-Path -Parent $PSScriptRoot) "runs\$runId"
    Write-Host ""
    Write-Host "Demo run completed." -ForegroundColor Green
    Write-Host "Run ID: $runId" -ForegroundColor Green
    Write-Host "Run directory: $runDir" -ForegroundColor Green
    Write-Host "Report: $runDir\report\final_report.md" -ForegroundColor Green
    return
  }
  if ($detail.status -eq "failed") {
    throw "Run failed. Check runs\$runId for details."
  }
  Start-Sleep -Seconds 2
}

throw "Run did not finish within $TimeoutSeconds seconds."
