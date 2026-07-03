"""Parsing specifiche tecniche da titolo prodotto e description."""

import re
from typing import Dict, Optional


class SubwooferSpecParser:
    """Estrae e valida specifiche subwoofer auto da titolo/description."""

    def __init__(self):
        # Pattern regex per specifiche comuni
        self.HEIGHT_PATTERN = re.compile(r'(\d+(?:[.,]\d+)?)\s*(?:cm|cm\.|centimetri)', re.IGNORECASE)
        self.RCA_PATTERN = re.compile(r'\bRCA\b|\bRCA\s+input\b', re.IGNORECASE)
        self.SPEAKER_PATTERN = re.compile(
            r'speaker\s+level|speaker\s+input|cavo\s+altoparlante|speaker wire',
            re.IGNORECASE
        )
        self.AMP_PATTERN = re.compile(
            r'amplificato|amplificatore|integrato|attivo|powered|active',
            re.IGNORECASE
        )
        self.PASSIVE_PATTERN = re.compile(
            r'passivo|passive(?!\s*sub)|non\s+amplificato|senza\s+amplificatore',
            re.IGNORECASE
        )
        self.POWER_PATTERN = re.compile(r'(\d+)\s*(?:W|watt|W RMS|watt RMS)', re.IGNORECASE)
        self.IMPEDANCE_PATTERN = re.compile(r'(\d+)\s*(?:ohm|ω)', re.IGNORECASE)

    def parse(self, title: str, description: str = "") -> Dict:
        """Estrae specifiche da titolo e description."""
        full_text = f"{title} {description}"

        # Height parsing
        height_cm = None
        height_match = self.HEIGHT_PATTERN.search(full_text)
        if height_match:
            try:
                height_str = height_match.group(1).replace(',', '.')
                height_cm = float(height_str)
            except ValueError:
                pass

        # Check amplificator
        has_amplifier = bool(self.AMP_PATTERN.search(full_text))
        is_passive = bool(self.PASSIVE_PATTERN.search(full_text))

        # Se esplicito "passivo" → not amplificato
        if is_passive:
            has_amplifier = False

        # Ingressi
        has_rca = bool(self.RCA_PATTERN.search(full_text))
        has_speaker_input = bool(self.SPEAKER_PATTERN.search(full_text))

        # Power
        power_w = None
        power_match = self.POWER_PATTERN.search(full_text)
        if power_match:
            try:
                power_w = int(power_match.group(1))
            except ValueError:
                pass

        # Impedance
        impedance = None
        impedance_match = self.IMPEDANCE_PATTERN.search(full_text)
        if impedance_match:
            try:
                impedance = int(impedance_match.group(1))
            except ValueError:
                pass

        return {
            "height_cm": height_cm,
            "has_amplifier": has_amplifier,
            "has_rca": has_rca,
            "has_speaker_input": has_speaker_input,
            "power_w": power_w,
            "impedance_ohm": impedance,
            "is_passive": is_passive,
            "confidence": self._calc_confidence(height_cm, has_amplifier, has_rca, has_speaker_input),
        }

    def _calc_confidence(self, height_cm, has_amp, has_rca, has_speaker):
        """Score 0-100 sulla qualità del parsing."""
        score = 0
        if height_cm is not None:
            score += 25
        if has_amp:
            score += 25
        if has_rca:
            score += 25
        if has_speaker:
            score += 25
        return score

    def validate_specs(self, specs: Dict, criteria: Dict) -> tuple[bool, list[str]]:
        """Valida specs contro criteri. Ritorna (is_valid, reasons)."""
        reasons = []

        # Amplificatore obbligatorio
        if not specs["has_amplifier"]:
            reasons.append("❌ No amplifier")
            return False, reasons

        # Passivo escluso esplicitamente
        if specs["is_passive"]:
            reasons.append("❌ Passive (excluded)")
            return False, reasons

        # Almeno uno tra RCA e speaker
        if not (specs["has_rca"] or specs["has_speaker_input"]):
            reasons.append("❌ No RCA/speaker input")
            return False, reasons

        # Altezza (se nota)
        if specs["height_cm"] and specs["height_cm"] > criteria.get("max_height_cm", 7):
            reasons.append(f"❌ Height {specs['height_cm']}cm > {criteria.get('max_height_cm')}cm")
            return False, reasons

        # Tutto ok
        reasons.append("✅ Pass all specs")
        return True, reasons


def test_parser():
    """Test parser su sample titles."""
    parser = SubwooferSpecParser()

    test_cases = [
        "Pioneer TS-WX310A Subwoofer Auto Amplificato 1300W RCA Speaker Level",
        "JBL BassPro SL Subwoofer Amplificato Altezza 6.9 cm RCA Ingresso Cavo",
        "Sony XS-FB10G Subwoofer Passivo 10cm NON AMPLIFICATO",
        "Alpine SWR-1241D Subwoofer Amplificatore 150W RCA Speaker Input 6.8cm",
        "Kenwood KSC-SW11 Compact Subwoofer Amplificato RCA Speaker Level 7 cm",
    ]

    criteria = {"max_height_cm": 7.0}

    print("=" * 70)
    print("SPEC PARSER TEST")
    print("=" * 70)

    for title in test_cases:
        specs = parser.parse(title)
        is_valid, reasons = parser.validate_specs(specs, criteria)

        print(f"\n📦 {title[:60]}")
        print(f"   Height: {specs['height_cm']}cm | Amp: {specs['has_amplifier']} | "
              f"RCA: {specs['has_rca']} | Speaker: {specs['has_speaker_input']}")
        print(f"   Confidence: {specs['confidence']}/100")
        print(f"   Status: {reasons[0]}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_parser()
