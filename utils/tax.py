def registration_fee_land(area_m2: float, gov_price_mil_m2: float, rate: float = 0.005) -> float:
    """Registration fee (land) estimate: area * gov_price * rate.
    Inputs: area (m²), gov_price (million VND/m²). Output: million VND.
    """
    return float(area_m2) * float(gov_price_mil_m2) * float(rate)

def non_agri_land_tax_simple(area_m2: float, gov_price_mil_m2: float, rate: float = 0.0003) -> float:
    """Simplified non-agricultural land use tax estimate (illustrative): area * gov_price * rate.
    Note: Real calculation depends on local thresholds, progressive rates, exemptions.
    Output: million VND/year (illustrative).
    """
    return float(area_m2) * float(gov_price_mil_m2) * float(rate)

def pit_transfer_tax(transfer_price_billion_vnd: float, rate: float = 0.02) -> float:
    """Personal income tax (real estate transfer) estimate: 2% * transfer price.
    Input: billion VND. Output: million VND.
    """
    return float(transfer_price_billion_vnd) * 1000.0 * float(rate)
