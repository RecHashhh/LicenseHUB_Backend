from datetime import date, timedelta

from app.models.license import LicenseStatusEnum


def calculate_status(expiration_date: date | None, threshold_days: int = 30) -> LicenseStatusEnum:
    """
    Calcula el estado de una licencia basado en su fecha de vencimiento.
    
    Args:
        expiration_date: Fecha de vencimiento de la licencia (puede ser None)
        threshold_days: Días de anticipación para considerar "Proxima a vencer"
    
    Returns:
        LicenseStatusEnum: Estado calculado (Activa, Vencida o Proxima a vencer)
    """
    if expiration_date is None:
        return LicenseStatusEnum.active  # Se asume activa si no hay fecha de vencimiento
    
    today = date.today()
    if expiration_date < today:
        return LicenseStatusEnum.expired
    if expiration_date <= today + timedelta(days=threshold_days):
        return LicenseStatusEnum.expiring
    return LicenseStatusEnum.active
