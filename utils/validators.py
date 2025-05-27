def is_valid_dota_mmr(text):
    """Проверяет, что введённый MMR для Dota 2 в допустимом диапазоне"""
    if not text.isdigit():
        return False
    mmr = int(text)
    return 50 <= mmr <= 17000

def is_valid_faceit_elo(text):
    """Проверяет, что введённый ELO для Faceit в допустимом диапазоне"""
    if not text.isdigit():
        return False
    elo = int(text)
    return 100 <= elo <= 5000