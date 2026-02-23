# InfluxDB Backup and Restore Script
# This prevents data loss when recreating containers

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('backup', 'restore')]
    [string]$Action = 'backup',
    
    [Parameter(Mandatory=$false)]
    [string]$BackupPath = ".\backups\influxdb_backup_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss').tar"
)

$ErrorActionPreference = "Stop"

Write-Host "`n=== InfluxDB Backup/Restore Tool ===" -ForegroundColor Cyan
Write-Host "Action: $Action`n" -ForegroundColor Yellow

# Ensure docker is available
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Error: Docker is not available. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Create backups directory if it doesn't exist
$backupDir = Split-Path -Parent $BackupPath
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
}

if ($Action -eq 'backup') {
    Write-Host "📦 Creating backup of InfluxDB data..." -ForegroundColor Green
    
    # Check if container is running
    $containerStatus = docker ps --filter "name=enersight-influxdb" --format "{{.Status}}"
    if (-not $containerStatus) {
        Write-Host "⚠️  Warning: InfluxDB container is not running." -ForegroundColor Yellow
        Write-Host "   Starting container for backup..." -ForegroundColor Yellow
        docker start enersight-influxdb
        Start-Sleep -Seconds 5
    }
    
    # Backup using influx CLI inside container
    Write-Host "   Creating backup..." -ForegroundColor White
    docker exec enersight-influxdb influx backup /tmp/backup -t my-super-secret-auth-token
    
    # Copy backup out of container
    Write-Host "   Copying backup to: $BackupPath" -ForegroundColor White
    docker cp enersight-influxdb:/tmp/backup $BackupPath
    
    # Clean up temporary backup in container
    docker exec enersight-influxdb rm -rf /tmp/backup
    
    Write-Host "`n✅ Backup completed successfully!" -ForegroundColor Green
    Write-Host "   Location: $BackupPath" -ForegroundColor White
    Write-Host "   Size: $((Get-Item $BackupPath).Length / 1MB) MB`n" -ForegroundColor White
    
} elseif ($Action -eq 'restore') {
    Write-Host "📥 Restoring InfluxDB data from backup..." -ForegroundColor Green
    
    if (-not (Test-Path $BackupPath)) {
        Write-Host "❌ Error: Backup file not found: $BackupPath" -ForegroundColor Red
        Write-Host "`nAvailable backups:" -ForegroundColor Yellow
        Get-ChildItem ".\backups\*.tar" | Select-Object Name, @{N='Size (MB)';E={[math]::Round($_.Length / 1MB, 2)}}, LastWriteTime | Format-Table
        exit 1
    }
    
    # Check if container is running
    $containerStatus = docker ps --filter "name=enersight-influxdb" --format "{{.Status}}"
    if (-not $containerStatus) {
        Write-Host "   Starting InfluxDB container..." -ForegroundColor White
        docker start enersight-influxdb
        Start-Sleep -Seconds 5
    }
    
    # Copy backup into container
    Write-Host "   Copying backup into container..." -ForegroundColor White
    docker cp $BackupPath enersight-influxdb:/tmp/restore_backup
    
    # Restore using influx CLI
    Write-Host "   Restoring data..." -ForegroundColor White
    docker exec enersight-influxdb influx restore /tmp/restore_backup -t my-super-secret-auth-token
    
    # Clean up
    docker exec enersight-influxdb rm -rf /tmp/restore_backup
    
    Write-Host "`n✅ Restore completed successfully!" -ForegroundColor Green
    Write-Host "   InfluxDB data has been restored.`n" -ForegroundColor White
}

Write-Host "Done!`n" -ForegroundColor Cyan
