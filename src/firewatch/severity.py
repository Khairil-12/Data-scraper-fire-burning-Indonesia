"""Transparent severity rules for satellite observations."""


def classify_severity(confidence: str, frp_mw: float | None) -> tuple[str, str]:
    """Return project-derived severity and readable reason."""
    confidence = confidence.strip().lower()
    if confidence == "low":
        return "low", "Confidence low; satellite detection requires review"
    if frp_mw is None:
        return "moderate", "FRP unavailable; satellite detection requires review"
    if confidence == "high" and frp_mw >= 25:
        return "severe", f"FRP {frp_mw:g} MW; confidence high"
    if frp_mw >= 100:
        return "severe", f"FRP {frp_mw:g} MW; confidence {confidence}"
    if frp_mw >= 25:
        return "high", f"FRP {frp_mw:g} MW; confidence {confidence}"
    return "moderate", f"FRP {frp_mw:g} MW; confidence {confidence}"
