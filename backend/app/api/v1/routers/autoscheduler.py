"""
AutoScheduler Control API endpoints
Provides REST interface for managing AutoScheduler operations
"""
from datetime import datetime, date
from typing import Optional, Dict, Any
import os
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.autoscheduler_metrics import AutoSchedulerMetrics

router = APIRouter(prefix="/autoscheduler", tags=["AutoScheduler Control"])

# Configuration file path
CONTROL_FILE = Path("data/autoscheduler_control.json")

# Pydantic models
class AutoSchedulerStatus(BaseModel):
    enabled: bool
    next_run_hour: Optional[int] = None
    scheduled_hours: list[int]
    pause_until: Optional[str] = None
    skip_dates: list[str] = []
    current_date: str
    time_until_next_run: Optional[str] = None

class PauseRequest(BaseModel):
    pause_until: str = Field(..., description="Date jusqu'à laquelle pauser (YYYY-MM-DD)")
    reason: Optional[str] = Field(None, description="Raison de la pause")

class ScheduleUpdateRequest(BaseModel):
    hours: list[int] = Field(..., description="Nouvelles heures d'exécution")

# Utility functions
def _load_control_config() -> Dict[str, Any]:
    """Charge la configuration de contrôle depuis le fichier JSON"""
    if not CONTROL_FILE.exists():
        # Créer configuration par défaut
        default_config = {
            "enabled": True,
            "scheduled_hours": [8, 15, 20],
            "skip_dates": [],
            "pause_until": None,
            "last_updated": datetime.now().isoformat(),
            "updated_by": "system"
        }
        _save_control_config(default_config)
        return default_config
    
    try:
        with open(CONTROL_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lecture configuration: {str(e)}"
        )

def _save_control_config(config: Dict[str, Any]):
    """Sauvegarde la configuration de contrôle"""
    try:
        # Créer répertoire si nécessaire
        CONTROL_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Mettre à jour timestamp
        config["last_updated"] = datetime.now().isoformat()
        
        # Sauvegarder
        with open(CONTROL_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur sauvegarde configuration: {str(e)}"
        )

def _get_next_run_info(scheduled_hours: list[int]) -> tuple[Optional[int], Optional[str]]:
    """Calcule la prochaine heure d'exécution et le temps restant"""
    current_hour = datetime.now().hour
    
    # Trouver prochaine heure programmée
    next_hours = [h for h in scheduled_hours if h > current_hour]
    
    if next_hours:
        next_run = min(next_hours)
        hours_until = next_run - current_hour
        time_until = f"dans {hours_until}h"
    elif scheduled_hours:
        # Prochaine exécution demain
        next_run = min(scheduled_hours)
        hours_until = (24 - current_hour) + next_run
        time_until = f"dans {hours_until}h (demain)"
    else:
        next_run = None
        time_until = None
    
    return next_run, time_until

# API Endpoints
@router.get("/status", response_model=AutoSchedulerStatus)
async def get_autoscheduler_status():
    """Obtient le statut actuel de l'AutoScheduler"""
    config = _load_control_config()
    
    # Vérifier si actuellement en pause
    today = date.today().isoformat()
    pause_until = config.get("pause_until")
    skip_dates = config.get("skip_dates", [])
    
    # Déterminer si enabled aujourd'hui
    enabled = (
        config.get("enabled", True) and 
        today not in skip_dates and
        (not pause_until or pause_until < today)
    )
    
    # Calculer prochaine exécution
    scheduled_hours = config.get("scheduled_hours", [8, 15, 20])
    next_run, time_until = _get_next_run_info(scheduled_hours) if enabled else (None, None)
    
    return AutoSchedulerStatus(
        enabled=enabled,
        next_run_hour=next_run,
        scheduled_hours=scheduled_hours,
        pause_until=pause_until,
        skip_dates=skip_dates,
        current_date=today,
        time_until_next_run=time_until
    )

@router.post("/enable")
async def enable_autoscheduler():
    """Active l'AutoScheduler"""
    config = _load_control_config()
    
    config["enabled"] = True
    config["pause_until"] = None  # Supprimer pause éventuelle
    config["updated_by"] = "api"
    
    _save_control_config(config)
    
    return {
        "status": "success",
        "message": "AutoScheduler activé",
        "enabled": True,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/disable")
async def disable_autoscheduler():
    """Désactive l'AutoScheduler"""
    config = _load_control_config()
    
    config["enabled"] = False
    config["updated_by"] = "api"
    
    _save_control_config(config)
    
    return {
        "status": "success", 
        "message": "AutoScheduler désactivé",
        "enabled": False,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/pause")
async def pause_autoscheduler(request: PauseRequest):
    """Met en pause l'AutoScheduler jusqu'à une date donnée"""
    try:
        # Valider format de date
        pause_date = datetime.strptime(request.pause_until, "%Y-%m-%d").date()
        today = date.today()
        
        if pause_date <= today:
            raise HTTPException(
                status_code=400,
                detail="La date de pause doit être dans le futur"
            )
            
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    
    config = _load_control_config()
    
    config["pause_until"] = request.pause_until
    config["updated_by"] = "api"
    
    if request.reason:
        config["pause_reason"] = request.reason
    
    _save_control_config(config)
    
    return {
        "status": "success",
        "message": f"AutoScheduler en pause jusqu'au {request.pause_until}",
        "pause_until": request.pause_until,
        "reason": request.reason,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/pause-today")
async def pause_autoscheduler_today():
    """Met en pause l'AutoScheduler pour aujourd'hui seulement"""
    config = _load_control_config()
    today = date.today().isoformat()
    
    skip_dates = config.get("skip_dates", [])
    if today not in skip_dates:
        skip_dates.append(today)
    
    config["skip_dates"] = skip_dates
    config["updated_by"] = "api"
    
    _save_control_config(config)
    
    return {
        "status": "success",
        "message": f"AutoScheduler en pause pour aujourd'hui ({today})",
        "skip_date": today,
        "timestamp": datetime.now().isoformat()
    }

@router.put("/schedule")
async def update_schedule(request: ScheduleUpdateRequest):
    """Met à jour les heures d'exécution de l'AutoScheduler"""
    
    # Validation des heures
    for hour in request.hours:
        if not (0 <= hour <= 23):
            raise HTTPException(
                status_code=400,
                detail=f"Heure invalide: {hour}. Doit être entre 0 et 23"
            )
    
    if len(request.hours) == 0:
        raise HTTPException(
            status_code=400,
            detail="Au moins une heure d'exécution est requise"
        )
    
    config = _load_control_config()
    
    old_hours = config.get("scheduled_hours", [])
    config["scheduled_hours"] = sorted(request.hours)  # Trier pour cohérence
    config["updated_by"] = "api"
    
    _save_control_config(config)
    
    return {
        "status": "success",
        "message": "Horaires d'exécution mis à jour",
        "old_schedule": old_hours,
        "new_schedule": config["scheduled_hours"],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/metrics")
async def get_autoscheduler_metrics():
    """Obtient les métriques quotidiennes de l'AutoScheduler"""
    try:
        metrics = AutoSchedulerMetrics()
        summary = metrics.get_daily_summary()
        
        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur récupération métriques: {str(e)}"
        )

@router.get("/health")
async def autoscheduler_health():
    """Health check pour le module AutoScheduler"""
    
    try:
        # Vérifier fichier de configuration
        config = _load_control_config()
        
        # Vérifier métriques
        metrics = AutoSchedulerMetrics()
        daily_summary = metrics.get_daily_summary()
        
        return {
            "status": "healthy",
            "module": "AutoScheduler Control",
            "version": "1.7.0",
            "config_status": "ok",
            "metrics_status": "ok",
            "current_config": {
                "enabled": config.get("enabled"),
                "scheduled_hours": config.get("scheduled_hours"),
                "has_pause": config.get("pause_until") is not None
            },
            "today_metrics": {
                "runs_completed": daily_summary.get("runs_completed", 0),
                "products_discovered": daily_summary.get("products_discovered", 0),
                "tokens_consumed": daily_summary.get("tokens_consumed", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )