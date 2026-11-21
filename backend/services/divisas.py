def convertir_a_moneda_base(monto: float, moneda_origen: str, moneda_base: str = "GTQ") -> float:
    """
    Convierte un monto de una moneda origen a la moneda base utilizando tasas de cambio de referencia.
    """
    tasas = {
        "GTQ": 1.0,
        "USD": 7.80,  # 1 USD = 7.80 GTQ
        "MXN": 0.45,  # 1 MXN = 0.45 GTQ
        "EUR": 8.50   # 1 EUR = 8.50 GTQ
    }
    
    origen = (moneda_origen or "GTQ").upper()
    base = moneda_base.upper()
    
    if origen == base:
        return monto
        
    tasa_origen = tasas.get(origen, 1.0)
    tasa_base = tasas.get(base, 1.0)
    
    en_base = monto * tasa_origen
    return en_base / tasa_base

