$base='http://localhost:8000'
$jsonHeaders=@{'Content-Type'='application/json'}
$tests=@(
  @{name='GET /'; method='GET'; url="$base/"},
  @{name='GET /health'; method='GET'; url="$base/health"},
  @{name='GET /health/'; method='GET'; url="$base/health/"},
  @{name='GET /study/archaeology'; method='GET'; url="$base/study/archaeology?topic=recursion&confusion_level=4"},
  @{name='POST /study/log'; method='POST'; url="$base/study/log"; body='{"topic":"recursion","content":"struggled with base case","confusion_level":4,"hint_used":"draw_call_stack","outcome":"resolved"}'},
  @{name='POST /socratic/ask'; method='POST'; url="$base/socratic/ask?concept=recursion&user_belief=recursion%20always%20runs%20forever"},
  @{name='POST /socratic/log'; method='POST'; url="$base/socratic/log"; body='{"concept":"recursion","belief":"base case optional","was_correct":false,"corrected_understanding":"base case is required"}'},
  @{name='GET /socratic/history'; method='GET'; url="$base/socratic/history?concept=recursion"},
  @{name='GET /insights/shadow'; method='GET'; url="$base/insights/shadow?days=7"},
  @{name='GET /insights/patterns'; method='GET'; url="$base/insights/patterns"},
  @{name='GET /insights/resonance'; method='GET'; url="$base/insights/resonance?topic=recursion"},
  @{name='GET /insights/contagion'; method='GET'; url="$base/insights/contagion?error_pattern=base_case_missing"},
  @{name='GET /memory/recall'; method='GET'; url="$base/memory/recall?limit=5"},
  @{name='GET /api/study/archaeology'; method='GET'; url="$base/api/study/archaeology?topic=recursion&confusion_level=4"},
  @{name='POST /api/socratic/ask'; method='POST'; url="$base/api/socratic/ask?concept=recursion&user_belief=recursion%20always%20runs%20forever"},
  @{name='GET /api/insights/shadow'; method='GET'; url="$base/api/insights/shadow?days=7"},
  @{name='GET /api/memory/recall'; method='GET'; url="$base/api/memory/recall?limit=5"},
  @{name='GET /docs'; method='GET'; url="$base/docs"},
  @{name='GET /openapi.json'; method='GET'; url="$base/openapi.json"}
)

$results=@()
foreach($t in $tests){
  try {
    if($t.method -eq 'POST'){
      if($t.ContainsKey('body')){ $r=Invoke-WebRequest -Uri $t.url -Method POST -Headers $jsonHeaders -Body $t.body -UseBasicParsing }
      else { $r=Invoke-WebRequest -Uri $t.url -Method POST -UseBasicParsing }
    } else {
      $r=Invoke-WebRequest -Uri $t.url -Method GET -UseBasicParsing
    }
    $results += [pscustomobject]@{endpoint=$t.name; status=$r.StatusCode; ok=($r.StatusCode -ge 200 -and $r.StatusCode -lt 300)}
  } catch {
    $code = if($_.Exception.Response){ [int]$_.Exception.Response.StatusCode } else { -1 }
    $results += [pscustomobject]@{endpoint=$t.name; status=$code; ok=$false}
  }
}

$results | Format-Table -AutoSize

$failed = $results | Where-Object { -not $_.ok }
Write-Host ""
Write-Host "Total:" $results.Count
Write-Host "Passed:" ($results.Count - $failed.Count)
Write-Host "Failed:" $failed.Count
if($failed.Count -gt 0){
  Write-Host "Failed endpoints:"
  $failed | ForEach-Object { Write-Host " -" $_.endpoint "(" $_.status ")" }
}
