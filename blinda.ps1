# blinda.ps1 — impedisce standby/hibernate/sleep-coperchio durante il job notturno.
# Lancia PRIMA del night_runner. A fine notte ripristina con: .\blinda.ps1 -Restore
# NB: powercfg /change non richiede admin per lo schema utente corrente.
param([switch]$Restore)

if ($Restore) {
    Write-Host "Ripristino timeout standard..."
    powercfg /change standby-timeout-ac 30
    powercfg /change hibernate-timeout-ac 0
    powercfg /change disk-timeout-ac 20
    powercfg /change monitor-timeout-ac 10
    Write-Host "Fatto. (Il PC torna a dormire normalmente.)"
    return
}

Write-Host "Blindo il PC per il job notturno (solo su alimentazione AC)..."
powercfg /change standby-timeout-ac 0      # niente sospensione
powercfg /change hibernate-timeout-ac 0    # niente ibernazione
powercfg /change disk-timeout-ac 0         # disco sempre attivo
powercfg /change monitor-timeout-ac 15     # schermo puo' spegnersi (ok, non sospende)

# Chiusura coperchio (laptop) = non fare nulla, su AC. GUID sottogruppo pulsanti/coperchio.
$lid = "5ca83367-6e45-459f-a23e-88566f97c267"
powercfg /setacvalueindex SCHEME_CURRENT 4f971e89-eebd-4455-a8de-9e59040e7347 $lid 0
powercfg /setactive SCHEME_CURRENT

Write-Host ""
Write-Host "OK. Standby/hibernate OFF su AC, coperchio=niente. TIENI IL PC COLLEGATO."
Write-Host "Stato attuale:"
powercfg /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE | Select-String "Current AC"
