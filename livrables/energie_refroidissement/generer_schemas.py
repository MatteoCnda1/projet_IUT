#!/usr/bin/env python3
"""Générateur des schémas vectoriels SVG pour l'énergie et le refroidissement.
Campus de Luminy - Marseille (Projet IUT BUT3 R&T - Point 14).

Produit :
1. schemas/synoptique_electrique.svg
2. schemas/aeraulique_salle_serveur.svg
"""

import pathlib

HERE = pathlib.Path(__file__).parent
SCHEMAS_DIR = HERE / "schemas"
SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)


def generer_synoptique_electrique():
    svg_path = SCHEMAS_DIR / "synoptique_electrique.svg"
    w, h = 1680, 1180

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="background:#0f172a; font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, sans-serif;">')

    # Definitions & Gradients
    svg.append('''<defs>
      <linearGradient id="headerGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#1e293b"/>
        <stop offset="50%" stop-color="#334155"/>
        <stop offset="100%" stop-color="#1e293b"/>
      </linearGradient>
      <linearGradient id="cardGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#1e293b"/>
        <stop offset="100%" stop-color="#0f172a"/>
      </linearGradient>
      <linearGradient id="gradVoieA" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#1e40af"/>
        <stop offset="100%" stop-color="#2563eb"/>
      </linearGradient>
      <linearGradient id="gradVoieB" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#991b1b"/>
        <stop offset="100%" stop-color="#dc2626"/>
      </linearGradient>
      <linearGradient id="gradGen" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#065f46"/>
        <stop offset="100%" stop-color="#059669"/>
      </linearGradient>
      <linearGradient id="gradATS" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#92400e"/>
        <stop offset="100%" stop-color="#d97706"/>
      </linearGradient>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">
        <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.4"/>
      </filter>
      <marker id="arrowA" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
        <path d="M 0 0 L 8 4 L 0 8 z" fill="#3b82f6"/>
      </marker>
      <marker id="arrowB" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
        <path d="M 0 0 L 8 4 L 0 8 z" fill="#ef4444"/>
      </marker>
      <marker id="arrowGreen" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
        <path d="M 0 0 L 8 4 L 0 8 z" fill="#10b981"/>
      </marker>
      <marker id="arrowYellow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
        <path d="M 0 0 L 8 4 L 0 8 z" fill="#f59e0b"/>
      </marker>
      <marker id="arrowGrey" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
        <path d="M 0 0 L 8 4 L 0 8 z" fill="#94a3b8"/>
      </marker>
    </defs>''')

    # Background subtle grid pattern
    svg.append('<rect width="100%" height="100%" fill="#0f172a"/>')

    # Top Header Banner
    svg.append(f'''
    <g transform="translate(30, 20)">
      <rect width="{w - 60}" height="70" rx="10" fill="url(#headerGrad)" stroke="#475569" stroke-width="1.5" filter="url(#shadow)"/>
      <circle cx="35" cy="35" r="18" fill="#3b82f6" opacity="0.2"/>
      <path d="M 35 22 L 35 48 M 25 35 L 45 35" stroke="#3b82f6" stroke-width="3" stroke-linecap="round"/>
      <text x="65" y="32" fill="#f8fafc" font-size="20" font-weight="700" letter-spacing="0.5">ARCHITECTURE ÉLECTRIQUE REDONDANTE 2N (VOIES A &amp; B) – SALLE SERVEUR &amp; LOCAUX TECHNIQUES</text>
      <text x="65" y="54" fill="#94a3b8" font-size="13">Campus IUT de Luminy (Marseille) • Sous-sol J05 Sud • P_nom: 3.82 kW • P_pic: 6.22 kW • Autonomie: 42 min (N) / 95 min (2N) • Conforme EN 50600 Class 3 / Tier III</text>
    </g>
    ''')

    # ==============================================================================
    # NIVEAU 1 : ARRIVÉES NORMAL / SECOURS ET ATS CAMPUS
    # ==============================================================================
    # Grid Arrival (Enedis)
    svg.append('''
    <!-- Enedis Arrival -->
    <g transform="translate(100, 110)" filter="url(#shadow)">
      <rect width="260" height="90" rx="8" fill="url(#cardGrad)" stroke="#38bdf8" stroke-width="2"/>
      <rect x="0" y="0" width="260" height="26" rx="8" fill="#0369a1"/>
      <text x="130" y="18" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">SOURCE NORMALE (RÉSEAU ENEDIS)</text>
      <text x="15" y="46" fill="#e2e8f0" font-size="12" font-weight="600">Arrivée TGBT Campus Luminy</text>
      <text x="15" y="64" fill="#94a3b8" font-size="11">400 V Triphasé + N + PE • 50 Hz</text>
      <text x="15" y="80" fill="#38bdf8" font-size="10" font-weight="600">Comptage Tarif Vert Enedis</text>
    </g>

    <!-- Generator Secours -->
    <g transform="translate(460, 110)" filter="url(#shadow)">
      <rect width="260" height="90" rx="8" fill="url(#cardGrad)" stroke="#10b981" stroke-width="2"/>
      <rect x="0" y="0" width="260" height="26" rx="8" fill="url(#gradGen)"/>
      <text x="130" y="18" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">SOURCE SECOURS (GROUPE ÉLECTROGÈNE)</text>
      <text x="15" y="46" fill="#e2e8f0" font-size="12" font-weight="600">Groupe Électrogène Campus 250 kVA</text>
      <text x="15" y="64" fill="#94a3b8" font-size="11">Démarrage auto &lt; 15 s • Cuve 500 L</text>
      <text x="15" y="80" fill="#10b981" font-size="10" font-weight="600">Autonomie continue &gt; 24h à pleine charge</text>
    </g>

    <!-- Inverseur ATS Campus -->
    <g transform="translate(260, 230)" filter="url(#shadow)">
      <rect width="300" height="85" rx="8" fill="url(#cardGrad)" stroke="#f59e0b" stroke-width="2"/>
      <rect x="0" y="0" width="300" height="26" rx="8" fill="url(#gradATS)"/>
      <text x="150" y="18" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">INVERSEUR DE SOURCE NORMAL / SECOURS (ATS)</text>
      <text x="15" y="46" fill="#e2e8f0" font-size="12" font-weight="600">ATS Tétrapolaire 4P 160A motorisé</text>
      <text x="15" y="63" fill="#94a3b8" font-size="11">Verrouillage mécanique + électrique</text>
      <text x="15" y="78" fill="#fbbf24" font-size="10" font-weight="600">Temps de commutation : ~8 à 10 secondes</text>
    </g>
    ''')

    # Liaison cables Enedis & GE -> ATS
    svg.append('''
    <!-- Cable Enedis to ATS -->
    <path d="M 230 200 L 230 272 L 260 272" stroke="#38bdf8" stroke-width="3" fill="none" marker-end="url(#arrowGrey)"/>
    <text x="180" y="245" fill="#38bdf8" font-size="10" font-weight="600">Voie Normale</text>

    <!-- Cable GE to ATS -->
    <path d="M 590 200 L 590 272 L 560 272" stroke="#10b981" stroke-width="3" fill="none" marker-end="url(#arrowGreen)"/>
    <text x="600" y="245" fill="#10b981" font-size="10" font-weight="600">Voie Secours</text>
    ''')

    # L.TECH Power Distribution Box on the Right
    svg.append('''
    <!-- Départ TGBT vers 6 L.TECH -->
    <g transform="translate(1120, 110)" filter="url(#shadow)">
      <rect width="520" height="205" rx="10" fill="url(#cardGrad)" stroke="#64748b" stroke-width="2"/>
      <rect x="0" y="0" width="520" height="28" rx="10" fill="#334155"/>
      <text x="260" y="19" fill="#f8fafc" font-size="12" font-weight="bold" text-anchor="middle">DISTRIBUTION ÉLECTRIQUE SECILISÉE VERS LES 6 LOCAUX TECHNIQUES (L.TECH)</text>

      <g transform="translate(15, 38)">
        <rect width="240" height="70" rx="6" fill="#1e293b" stroke="#475569"/>
        <text x="10" y="18" fill="#38bdf8" font-size="11" font-weight="bold">N-1-LT01 (Sous-sol • 6.7 m²)</text>
        <text x="10" y="34" fill="#cbd5e1" font-size="10">1x C9200L-48P • PoE 103W • P_nom: 148W</text>
        <text x="10" y="48" fill="#94a3b8" font-size="10">Onduleur APC 1.5 kVA (Charge: 14.8%)</text>
        <text x="10" y="62" fill="#10b981" font-size="10" font-weight="bold">Autonomie batterie : ~72 min</text>
      </g>

      <g transform="translate(265, 38)">
        <rect width="240" height="70" rx="6" fill="#1e293b" stroke="#475569"/>
        <text x="10" y="18" fill="#38bdf8" font-size="11" font-weight="bold">N-1-LT02 (Sous-sol • 16.0 m²)</text>
        <text x="10" y="34" fill="#cbd5e1" font-size="10">1x C9200L-48P • PoE 70W • P_nom: 115W</text>
        <text x="10" y="48" fill="#94a3b8" font-size="10">Onduleur APC 1.5 kVA (Charge: 11.5%)</text>
        <text x="10" y="62" fill="#10b981" font-size="10" font-weight="bold">Autonomie batterie : ~79 min</text>
      </g>

      <g transform="translate(15, 118)">
        <rect width="240" height="75" rx="6" fill="#1e293b" stroke="#f59e0b" stroke-width="1.5"/>
        <text x="10" y="17" fill="#f59e0b" font-size="11" font-weight="bold">N0-LT01 (Placard RDC • 2.3 m²)</text>
        <text x="10" y="32" fill="#cbd5e1" font-size="10">2x C9200L-48P • PoE 333W • P_nom: 423W</text>
        <text x="10" y="46" fill="#94a3b8" font-size="10">Onduleur APC 1.5 kVA (Charge: 42.3%)</text>
        <text x="10" y="60" fill="#ef4444" font-size="10" font-weight="bold">Ventilation forcée dédiée 185 m³/h</text>
        <text x="10" y="72" fill="#10b981" font-size="9">Autonomie : ~33 min</text>
      </g>

      <g transform="translate(265, 118)">
        <rect width="240" height="75" rx="6" fill="#1e293b" stroke="#475569"/>
        <text x="10" y="17" fill="#38bdf8" font-size="11" font-weight="bold">N0-LT02, N1-LT01, N1-LT02</text>
        <text x="10" y="32" fill="#cbd5e1" font-size="10">N0-LT02 (565W) • N1-LT01 (282W)</text>
        <text x="10" y="46" fill="#cbd5e1" font-size="10">N1-LT02 (487W • Baie 42U au sol)</text>
        <text x="10" y="60" fill="#94a3b8" font-size="10">3x Onduleurs APC 1.5 kVA dédiés</text>
        <text x="10" y="72" fill="#10b981" font-size="9">Autonomie : ~22 à 49 min</text>
      </g>
    </g>

    <!-- Cable ATS to L.TECH panel -->
    <path d="M 560 272 L 1120 272" stroke="#94a3b8" stroke-width="2.5" stroke-dasharray="6,4" fill="none" marker-end="url(#arrowGrey)"/>
    <text x="750" y="264" fill="#94a3b8" font-size="10" font-weight="600">6 lignes dédiées C20A 3G4mm² vers les L.TECH</text>
    ''')

    # ==============================================================================
    # NIVEAU 2 : TGBT SALLE SERVEUR (DÉCOUPLAGE VOIE A ET VOIE B)
    # ==============================================================================
    # Distribution bus from ATS to Voie A and Voie B
    svg.append('''
    <!-- Busbar from ATS downwards -->
    <path d="M 410 315 L 410 345" stroke="#f59e0b" stroke-width="3" fill="none"/>
    <path d="M 230 345 L 750 345" stroke="#f59e0b" stroke-width="3" fill="none"/>
    <path d="M 230 345 L 230 380" stroke="#3b82f6" stroke-width="3" fill="none" marker-end="url(#arrowA)"/>
    <path d="M 750 345 L 750 380" stroke="#ef4444" stroke-width="3" fill="none" marker-end="url(#arrowB)"/>
    <text x="410" y="340" fill="#f59e0b" font-size="11" font-weight="bold" text-anchor="middle">DISTRIBUTION TGBT SALLE SERVEUR (J05 SUD)</text>
    ''')

    # VOIE A - Colonne de Gauche
    svg.append('''
    <!-- CADRE VOIE A -->
    <g transform="translate(40, 380)" filter="url(#shadow)">
      <rect width="470" height="420" rx="10" fill="#0f172a" stroke="#2563eb" stroke-width="2.5"/>
      <rect x="0" y="0" width="470" height="32" rx="10" fill="url(#gradVoieA)"/>
      <text x="235" y="22" fill="#ffffff" font-size="14" font-weight="bold" text-anchor="middle">VOIE A (ALIMENTATION PRIMAIRE REDONDANTE)</text>

      <!-- Étage 1 : Protection & Bypass -->
      <g transform="translate(15, 45)">
        <rect width="440" height="75" rx="6" fill="#1e293b" stroke="#3b82f6"/>
        <text x="12" y="18" fill="#93c5fd" font-size="11" font-weight="bold">Protection TGBT Voie A &amp; Bypass de Maintenance</text>
        <text x="12" y="36" fill="#e2e8f0" font-size="11">• Disjoncteur différentiel C32A / 300mA Type A-Si (Super-immunisé)</text>
        <text x="12" y="52" fill="#e2e8f0" font-size="11">• Parafoudre débrochable Type 2 (SPD 40 kA) conforme NF C 15-100</text>
        <text x="12" y="68" fill="#60a5fa" font-size="10" font-weight="600">• Inverseur de Bypass manuel 3 positions (Normal / Test / Bypass)</text>
      </g>

      <!-- Étage 2 : Onduleur A -->
      <g transform="translate(15, 135)">
        <rect width="440" height="150" rx="6" fill="#1e293b" stroke="#2563eb" stroke-width="1.5"/>
        <rect x="0" y="0" width="440" height="24" rx="6" fill="#1d4ed8"/>
        <text x="220" y="17" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">ONDULEUR UPS A : APC SMART-UPS SRT 6 kVA (SRT6KRMXLI)</text>

        <text x="12" y="44" fill="#f8fafc" font-size="12" font-weight="600">Technologie : On-Line Double Conversion (VFI-SS-111)</text>
        <text x="12" y="62" fill="#cbd5e1" font-size="11">Capacité : 6 000 VA / 6 000 W • Facteur de puissance : 1.0</text>
        <text x="12" y="80" fill="#cbd5e1" font-size="11">Régime nominal 2N (50% charge) : <tspan fill="#60a5fa" font-weight="bold">1 912 W (31.9% charge)</tspan></text>
        <text x="12" y="98" fill="#cbd5e1" font-size="11">Régime dégradé N (100% salle) : <tspan fill="#f87171" font-weight="bold">3 824 W (63.7% charge)</tspan></text>
        <text x="12" y="116" fill="#93c5fd" font-size="11">Supervision : Carte NMC3 (SNMPv3, NUT, Modbus-TCP, LibreNMS)</text>
        <rect x="12" y="124" width="416" height="20" rx="4" fill="#0f172a" stroke="#3b82f6"/>
        <text x="220" y="138" fill="#93c5fd" font-size="10" font-weight="bold" text-anchor="middle">+ 1 Pack Batterie Externe SRT192RMBP • Autonomie : 42 min (N) / 95 min (2N)</text>
      </g>

      <!-- Étage 3 : Tableau divisionnaire ondulé A -->
      <g transform="translate(15, 300)">
        <rect width="440" height="105" rx="6" fill="#1e293b" stroke="#3b82f6"/>
        <text x="12" y="18" fill="#93c5fd" font-size="11" font-weight="bold">Tableau Divisionnaire Ondulé A (TD-OND-A)</text>
        <text x="12" y="36" fill="#e2e8f0" font-size="11">Départs protégés par disjoncteurs C16A 30mA Si :</text>
        <text x="20" y="54" fill="#93c5fd" font-size="11">➜ Départ A1 : Alimentation PDU A1 (Baie 1 Réseau/Cœur)</text>
        <text x="20" y="72" fill="#93c5fd" font-size="11">➜ Départ A2 : Alimentation PDU A2 (Baie 2 Datacenter/Hyperviseurs)</text>
        <text x="20" y="90" fill="#f59e0b" font-size="11">➜ Départ A-ATS : Source primaire de l'ATS 1U (APC AP4421A)</text>
      </g>
    </g>
    ''')

    # VOIE B - Colonne du Milieu
    svg.append('''
    <!-- CADRE VOIE B -->
    <g transform="translate(560, 380)" filter="url(#shadow)">
      <rect width="470" height="420" rx="10" fill="#0f172a" stroke="#dc2626" stroke-width="2.5"/>
      <rect x="0" y="0" width="470" height="32" rx="10" fill="url(#gradVoieB)"/>
      <text x="235" y="22" fill="#ffffff" font-size="14" font-weight="bold" text-anchor="middle">VOIE B (ALIMENTATION SECONDAIRE INDÉPENDANTE)</text>

      <!-- Étage 1 : Protection & Bypass -->
      <g transform="translate(15, 45)">
        <rect width="440" height="75" rx="6" fill="#1e293b" stroke="#ef4444"/>
        <text x="12" y="18" fill="#fca5a5" font-size="11" font-weight="bold">Protection TGBT Voie B &amp; Bypass de Maintenance</text>
        <text x="12" y="36" fill="#e2e8f0" font-size="11">• Disjoncteur différentiel C32A / 300mA Type A-Si (Super-immunisé)</text>
        <text x="12" y="52" fill="#e2e8f0" font-size="11">• Parafoudre débrochable Type 2 (SPD 40 kA) conforme NF C 15-100</text>
        <text x="12" y="68" fill="#f87171" font-size="10" font-weight="600">• Inverseur de Bypass manuel 3 positions (Normal / Test / Bypass)</text>
      </g>

      <!-- Étage 2 : Onduleur B -->
      <g transform="translate(15, 135)">
        <rect width="440" height="150" rx="6" fill="#1e293b" stroke="#dc2626" stroke-width="1.5"/>
        <rect x="0" y="0" width="440" height="24" rx="6" fill="#b91c1c"/>
        <text x="220" y="17" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">ONDULEUR UPS B : APC SMART-UPS SRT 6 kVA (SRT6KRMXLI)</text>

        <text x="12" y="44" fill="#f8fafc" font-size="12" font-weight="600">Technologie : On-Line Double Conversion (VFI-SS-111)</text>
        <text x="12" y="62" fill="#cbd5e1" font-size="11">Capacité : 6 000 VA / 6 000 W • Facteur de puissance : 1.0</text>
        <text x="12" y="80" fill="#cbd5e1" font-size="11">Régime nominal 2N (50% charge) : <tspan fill="#fca5a5" font-weight="bold">1 912 W (31.9% charge)</tspan></text>
        <text x="12" y="98" fill="#cbd5e1" font-size="11">Régime dégradé N (100% salle) : <tspan fill="#f87171" font-weight="bold">3 824 W (63.7% charge)</tspan></text>
        <text x="12" y="116" fill="#fca5a5" font-size="11">Supervision : Carte NMC3 (SNMPv3, NUT, Modbus-TCP, LibreNMS)</text>
        <rect x="12" y="124" width="416" height="20" rx="4" fill="#0f172a" stroke="#ef4444"/>
        <text x="220" y="138" fill="#fca5a5" font-size="10" font-weight="bold" text-anchor="middle">+ 1 Pack Batterie Externe SRT192RMBP • Autonomie : 42 min (N) / 95 min (2N)</text>
      </g>

      <!-- Étage 3 : Tableau divisionnaire ondulé B -->
      <g transform="translate(15, 300)">
        <rect width="440" height="105" rx="6" fill="#1e293b" stroke="#ef4444"/>
        <text x="12" y="18" fill="#fca5a5" font-size="11" font-weight="bold">Tableau Divisionnaire Ondulé B (TD-OND-B)</text>
        <text x="12" y="36" fill="#e2e8f0" font-size="11">Départs protégés par disjoncteurs C16A 30mA Si :</text>
        <text x="20" y="54" fill="#fca5a5" font-size="11">➜ Départ B1 : Alimentation PDU B1 (Baie 1 Réseau/Cœur)</text>
        <text x="20" y="72" fill="#fca5a5" font-size="11">➜ Départ B2 : Alimentation PDU B2 (Baie 2 Datacenter/Hyperviseurs)</text>
        <text x="20" y="90" fill="#f59e0b" font-size="11">➜ Départ B-ATS : Source secours de l'ATS 1U (APC AP4421A)</text>
      </g>
    </g>
    ''')

    # Climatisation de précision N+1 (Bloc Droite)
    svg.append('''
    <!-- ALIMENTATION CLIMATISATION N+1 -->
    <g transform="translate(1080, 380)" filter="url(#shadow)">
      <rect width="560" height="420" rx="10" fill="#0f172a" stroke="#0ea5e9" stroke-width="2.5"/>
      <rect x="0" y="0" width="560" height="32" rx="10" fill="#0284c7"/>
      <text x="280" y="22" fill="#ffffff" font-size="14" font-weight="bold" text-anchor="middle">CLIMATISATION DE PRÉCISION N+1 (7.2 kW FROID SENSIBLE)</text>

      <g transform="translate(15, 45)">
        <rect width="530" height="75" rx="6" fill="#1e293b" stroke="#0ea5e9"/>
        <text x="12" y="18" fill="#7dd3fc" font-size="11" font-weight="bold">Alimentation Électrique Sécurisée des Groupes Froid</text>
        <text x="12" y="36" fill="#e2e8f0" font-size="11">• Climatiseur Unité 1 (Maître) raccordé au départ Force Voie A (TGBT)</text>
        <text x="12" y="52" fill="#e2e8f0" font-size="11">• Climatiseur Unité 2 (Secours N+1) raccordé au départ Force Voie B (TGBT)</text>
        <text x="12" y="68" fill="#38bdf8" font-size="10" font-weight="600">• Redémarrage automatique échelonné après reprise secteur / groupe électrogène</text>
      </g>

      <g transform="translate(15, 135)">
        <rect width="255" height="150" rx="6" fill="#1e293b" stroke="#38bdf8"/>
        <text x="128" y="20" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">UNITÉ 1 : ACTIVE</text>
        <text x="10" y="44" fill="#cbd5e1" font-size="11">Type : Détente directe DX Inverter</text>
        <text x="10" y="62" fill="#cbd5e1" font-size="11">Capacité sensible : 7.2 kW</text>
        <text x="10" y="80" fill="#cbd5e1" font-size="11">Régime nominal : <tspan fill="#10b981" font-weight="bold">60.6% charge</tspan></text>
        <text x="10" y="98" fill="#cbd5e1" font-size="11">Débit d'air : 1 850 m³/h (EC fans)</text>
        <text x="10" y="116" fill="#cbd5e1" font-size="11">Fluide frigorigène : R32 (Bas GWP)</text>
        <text x="10" y="136" fill="#38bdf8" font-size="10" font-weight="bold">Soufflage allée froide à 22°C</text>
      </g>

      <g transform="translate(290, 135)">
        <rect width="255" height="150" rx="6" fill="#1e293b" stroke="#10b981"/>
        <text x="128" y="20" fill="#10b981" font-size="12" font-weight="bold" text-anchor="middle">UNITÉ 2 : SECOURS (STANDBY)</text>
        <text x="10" y="44" fill="#cbd5e1" font-size="11">Type : Détente directe DX Inverter</text>
        <text x="10" y="62" fill="#cbd5e1" font-size="11">Capacité sensible : 7.2 kW</text>
        <text x="10" y="80" fill="#cbd5e1" font-size="11">Statut : <tspan fill="#10b981" font-weight="bold">Veille active (Standby)</tspan></text>
        <text x="10" y="98" fill="#cbd5e1" font-size="11">Permutation automatique hebdo</text>
        <text x="10" y="116" fill="#cbd5e1" font-size="11">Reprise instantanée si défaut U1</text>
        <text x="10" y="136" fill="#10b981" font-size="10" font-weight="bold">Assure la redondance N+1 stricte</text>
      </g>

      <g transform="translate(15, 300)">
        <rect width="530" height="105" rx="6" fill="#1e293b" stroke="#0ea5e9"/>
        <text x="12" y="18" fill="#7dd3fc" font-size="11" font-weight="bold">Performances Énergétiques &amp; Free-Cooling Nocturne</text>
        <text x="12" y="36" fill="#e2e8f0" font-size="11">• Climat méditerranéen de Luminy : 42% de l'année avec T_ext &lt; 18°C (nuits &amp; mi-saison)</text>
        <text x="12" y="54" fill="#e2e8f0" font-size="11">• Économiseur Free-cooling indirect : EER passe de 3.6 (compression) à 12.0 (free-cooling)</text>
        <text x="12" y="72" fill="#10b981" font-size="11" font-weight="bold">• PUE annuel moyen pondéré : 1.28 (vs 1.60 initial chiffrage) • Gain éco-énergie : -20% OPEX</text>
        <text x="12" y="90" fill="#94a3b8" font-size="10">Supervision T°/HR par sondes Modbus raccordées au collecteur SNMP LibreNMS</text>
      </g>
    </g>
    ''')

    # ==============================================================================
    # NIVEAU 3 : DISTRIBUTION EN BAIES ET RACCORDEMENT IT
    # ==============================================================================
    svg.append('''
    <!-- BAIE 1 : RÉSEAU / CŒUR / DMZ -->
    <g transform="translate(40, 830)" filter="url(#shadow)">
      <rect width="740" height="320" rx="10" fill="url(#cardGrad)" stroke="#475569" stroke-width="2"/>
      <rect x="0" y="0" width="740" height="30" rx="10" fill="#334155"/>
      <text x="370" y="20" fill="#f8fafc" font-size="13" font-weight="bold" text-anchor="middle">BAIE 1 (42U 800x1000) : WAN • FIREWALLS • DMZ • CŒUR • DISTRIBUTION</text>

      <!-- PDU A1 et PDU B1 -->
      <g transform="translate(15, 40)">
        <rect width="345" height="40" rx="4" fill="#1e3a8a" stroke="#3b82f6"/>
        <text x="10" y="18" fill="#ffffff" font-size="11" font-weight="bold">PDU A1 (0U Verticale) : APC AP8959EU3</text>
        <text x="10" y="32" fill="#bfdbfe" font-size="10">Alimentée par Voie A • 230V 16A • Métrée par prise</text>
      </g>
      <g transform="translate(380, 40)">
        <rect width="345" height="40" rx="4" fill="#7f1d1d" stroke="#ef4444"/>
        <text x="10" y="18" fill="#ffffff" font-size="11" font-weight="bold">PDU B1 (0U Verticale) : APC AP8959EU3</text>
        <text x="10" y="32" fill="#fecaca" font-size="10">Alimentée par Voie B • 230V 16A • Métrée par prise</text>
      </g>

      <!-- ATS 1U pour monosource -->
      <g transform="translate(15, 90)">
        <rect width="710" height="42" rx="4" fill="#78350f" stroke="#f59e0b"/>
        <text x="10" y="18" fill="#fef3c7" font-size="11" font-weight="bold">ATS 1U Rackable : APC AP4421A (Automatic Transfer Switch 10A)</text>
        <text x="10" y="33" fill="#fde68a" font-size="10">Entrée 1 sur Voie A | Entrée 2 sur Voie B ➜ Alimente les équipements monosources en &lt; 10 ms sans coupure</text>
      </g>

      <!-- Équipements de Baie 1 -->
      <g transform="translate(15, 142)">
        <rect width="710" height="165" rx="6" fill="#0f172a" stroke="#334155"/>
        <text x="15" y="20" fill="#38bdf8" font-size="11" font-weight="bold">Équipements hébergés en Baie 1 (P_nom: 1 904 W • P_pic: 3 137 W • 24 unités physiques) :</text>

        <!-- Monosources via ATS -->
        <g transform="translate(15, 30)">
          <rect width="680" height="26" rx="4" fill="#1e293b" stroke="#f59e0b"/>
          <text x="10" y="17" fill="#fbbf24" font-size="10" font-weight="bold">[Monosource via ATS]</text>
          <text x="145" y="17" fill="#f8fafc" font-size="10">2x Routeurs Cisco C8200L-1N-4T (EL-RTR1, EL-RTR2) • 2x 20W • FAI 1 &amp; FAI 2</text>
        </g>

        <!-- Double alimentation Voie A + Voie B -->
        <g transform="translate(15, 62)">
          <rect width="680" height="92" rx="4" fill="#1e293b" stroke="#64748b"/>
          <text x="10" y="18" fill="#38bdf8" font-size="10" font-weight="bold">[Double Alim A + B]</text>
          <text x="145" y="18" fill="#f8fafc" font-size="10">2x Pare-feu FortiGate 120G (Alim 1 sur PDU A1, Alim 2 sur PDU B1) • 2x 32W</text>
          <text x="145" y="34" fill="#f8fafc" font-size="10">2x Pare-feu Stormshield SN710 (Qualif ANSSI) (Alim 1 ➜ A1, Alim 2 ➜ B1) • 2x 40W</text>
          <text x="145" y="50" fill="#f8fafc" font-size="10">4x Switchs C9200L-24T (WAN &amp; DMZ) (Alim 1 ➜ A1, Alim 2 ➜ B1) • 4x 45W</text>
          <text x="145" y="66" fill="#f8fafc" font-size="10">6x Switchs C9500-16X-E (Cœur &amp; Distribution SVL) (Alim 1 ➜ A1, Alim 2 ➜ B1) • 6x 140W</text>
          <text x="145" y="82" fill="#f8fafc" font-size="10">6x Serveurs Dell PowerEdge R260 (DMZ RP/DNS/WEB) (Alim 1 ➜ A1, Alim 2 ➜ B1) • 6x 110W</text>
        </g>
      </g>
    </g>

    <!-- BAIE 2 : DATACENTER / HYPERVISEURS / BACKUP -->
    <g transform="translate(820, 830)" filter="url(#shadow)">
      <rect width="820" height="320" rx="10" fill="url(#cardGrad)" stroke="#475569" stroke-width="2"/>
      <rect x="0" y="0" width="820" height="30" rx="10" fill="#334155"/>
      <text x="410" y="20" fill="#f8fafc" font-size="13" font-weight="bold" text-anchor="middle">BAIE 2 (42U 800x1000) : DATACENTER • PROXMOX HA CEPH • ACTIVE DIRECTORY • BACKUP PBS</text>

      <!-- PDU A2 et PDU B2 -->
      <g transform="translate(15, 40)">
        <rect width="385" height="40" rx="4" fill="#1e3a8a" stroke="#3b82f6"/>
        <text x="10" y="18" fill="#ffffff" font-size="11" font-weight="bold">PDU A2 (0U Verticale) : APC AP8959EU3</text>
        <text x="10" y="32" fill="#bfdbfe" font-size="10">Alimentée par Voie A • 230V 16A • Métrée par prise</text>
      </g>
      <g transform="translate(420, 40)">
        <rect width="385" height="40" rx="4" fill="#7f1d1d" stroke="#ef4444"/>
        <text x="10" y="18" fill="#ffffff" font-size="11" font-weight="bold">PDU B2 (0U Verticale) : APC AP8959EU3</text>
        <text x="10" y="32" fill="#fecaca" font-size="10">Alimentée par Voie B • 230V 16A • Métrée par prise</text>
      </g>

      <!-- Équipements de Baie 2 -->
      <g transform="translate(15, 90)">
        <rect width="790" height="217" rx="6" fill="#0f172a" stroke="#334155"/>
        <text x="15" y="20" fill="#38bdf8" font-size="11" font-weight="bold">Équipements hébergés en Baie 2 (P_nom: 1 920 W • P_pic: 3 080 W • 15 serveurs &amp; switchs) :</text>
        <text x="15" y="36" fill="#94a3b8" font-size="10">Tous les équipements de la Baie 2 disposent de doubles blocs d'alimentation redondants (PSU1 sur PDU A2, PSU2 sur PDU B2) :</text>

        <g transform="translate(15, 45)">
          <rect width="760" height="158" rx="4" fill="#1e293b" stroke="#64748b"/>
          <g transform="translate(12, 18)">
            <text x="0" y="0" fill="#10b981" font-size="10" font-weight="bold">Cluster Virtualisation HA :</text>
            <text x="160" y="0" fill="#f8fafc" font-size="10">3x Dell PowerEdge R660xs (NM-PVE1 à 3) • 2x PSU 800W Titanium • P_nom: 3x 200W</text>
            <text x="160" y="14" fill="#94a3b8" font-size="9">Cluster Proxmox VE + Stockage distribué Ceph (NVMe) + Supervision LibreNMS/Grafana</text>
          </g>

          <g transform="translate(12, 54)">
            <text x="0" y="0" fill="#38bdf8" font-size="10" font-weight="bold">Commutateurs Datacenter :</text>
            <text x="160" y="0" fill="#f8fafc" font-size="10">2x Cisco C9300X-12Y-E (25G DT-SW1/2) + 2x C9200L-24T (NM-SW1/2) • P_nom: 350W</text>
            <text x="160" y="14" fill="#94a3b8" font-size="9">Double alimentation redondante 1+1 Platinum • Câblage DAC 25G vers R660xs</text>
          </g>

          <g transform="translate(12, 90)">
            <text x="0" y="0" fill="#fbbf24" font-size="10" font-weight="bold">Serveurs Métier Datacenter :</text>
            <text x="160" y="0" fill="#f8fafc" font-size="10">6x Dell PowerEdge R360 (DT-AD1/2, DT-RAD1/2, DT-DHCP1/2) • 2x PSU 600W • P_nom: 6x 115W</text>
            <text x="160" y="14" fill="#94a3b8" font-size="9">Services d'infrastructure haute disponibilité (Contrôleurs AD, RADIUS 802.1X, DHCP)</text>
          </g>

          <g transform="translate(12, 126)">
            <text x="0" y="0" fill="#f43f5e" font-size="10" font-weight="bold">Serveur Sauvegarde PBS :</text>
            <text x="160" y="0" fill="#f8fafc" font-size="10">1x Dell PowerEdge R760xd2 (DT-BKP1) • 2x PSU 1100W Titanium • ~100 To bruts • P_nom: 250W</text>
            <text x="160" y="14" fill="#94a3b8" font-size="9">Proxmox Backup Server (Dédoublonnage à la source, chiffrement, rétention Règle 3-2-1)</text>
          </g>
        </g>
      </g>
    </g>
    ''')

    # Connecting cables from TD-OND to PDUs
    svg.append('''
    <!-- Liaison Voie A -> PDU A1 & PDU A2 -->
    <path d="M 230 800 L 230 820 L 190 820 L 190 840" stroke="#3b82f6" stroke-width="2.5" fill="none" marker-end="url(#arrowA)"/>
    <path d="M 230 800 L 230 820 L 1010 820 L 1010 840" stroke="#3b82f6" stroke-width="2.5" stroke-dasharray="8,4" fill="none" marker-end="url(#arrowA)"/>

    <!-- Liaison Voie B -> PDU B1 & PDU B2 -->
    <path d="M 750 800 L 750 820 L 550 820 L 550 840" stroke="#ef4444" stroke-width="2.5" fill="none" marker-end="url(#arrowB)"/>
    <path d="M 750 800 L 750 820 L 1240 820 L 1240 840" stroke="#ef4444" stroke-width="2.5" stroke-dasharray="8,4" fill="none" marker-end="url(#arrowB)"/>
    ''')

    svg.append('</svg>')

    svg_path.write_text("\n".join(svg), encoding="utf-8")
    print(f"Schéma unifilaire généré : {svg_path.resolve()}")


def generer_aeraulique_salle_serveur():
    svg_path = SCHEMAS_DIR / "aeraulique_salle_serveur.svg"
    w, h = 1680, 1200

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" style="background:#0b1120; font-family:system-ui, -apple-system, Segoe UI, Roboto, Helvetica, sans-serif;">')

    svg.append('''<defs>
      <linearGradient id="wallGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#334155"/>
        <stop offset="100%" stop-color="#1e293b"/>
      </linearGradient>
      <linearGradient id="coldAisleGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0284c7" stop-opacity="0.35"/>
        <stop offset="100%" stop-color="#38bdf8" stop-opacity="0.15"/>
      </linearGradient>
      <linearGradient id="hotAisleGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#b91c1c" stop-opacity="0.3"/>
        <stop offset="100%" stop-color="#ef4444" stop-opacity="0.1"/>
      </linearGradient>
      <linearGradient id="rackGrad" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#1e293b"/>
        <stop offset="50%" stop-color="#334155"/>
        <stop offset="100%" stop-color="#1e293b"/>
      </linearGradient>
      <linearGradient id="climGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#0369a1"/>
        <stop offset="100%" stop-color="#0284c7"/>
      </linearGradient>
      <filter id="shadowAeraulic" x="-5%" y="-5%" width="110%" height="115%" filterUnits="userSpaceOnUse">
        <feDropShadow dx="0" dy="5" stdDeviation="6" flood-color="#000000" flood-opacity="0.5"/>
      </filter>
      <marker id="coldArrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
        <path d="M 0 0 L 8 4 L 0 8 z" fill="#38bdf8"/>
      </marker>
      <marker id="hotArrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
        <path d="M 0 0 L 8 4 L 0 8 z" fill="#f87171"/>
      </marker>
      <pattern id="perforatedFloor" width="10" height="10" patternUnits="userSpaceOnUse">
        <circle cx="5" cy="5" r="2.2" fill="#38bdf8" opacity="0.6"/>
      </pattern>
    </defs>''')

    # Header Banner
    svg.append(f'''
    <g transform="translate(30, 20)">
      <rect width="{w - 60}" height="70" rx="10" fill="#1e293b" stroke="#475569" stroke-width="1.5" filter="url(#shadowAeraulic)"/>
      <circle cx="35" cy="35" r="18" fill="#0ea5e9" opacity="0.2"/>
      <path d="M 27 35 Q 35 25 43 35 Q 35 45 27 35" fill="none" stroke="#38bdf8" stroke-width="2.5"/>
      <text x="65" y="32" fill="#f8fafc" font-size="20" font-weight="700">PLAN D'IMPLANTATION PHYSIQUE &amp; URBANISATION AÉRAULIQUE (SALLE SERVEUR J05 SUD)</text>
      <text x="65" y="54" fill="#94a3b8" font-size="13">Surface : 25.1 m² (5.85 m × 4.30 m) • Hauteur sous dalle : 3.20 m • Confinement allée froide (CAC) • Climatisation N+1 (2x 7.2 kW) • Extinction Novec 1230 / FK-5-1-12</text>
    </g>
    ''')

    # ==============================================================================
    # PARTIE GAUCHE : VUE EN PLAN (TOP VIEW) DE LA SALLE SERVEUR
    # ==============================================================================
    svg.append('''
    <!-- VUE EN PLAN -->
    <g transform="translate(40, 110)" filter="url(#shadowAeraulic)">
      <!-- Zone title -->
      <rect width="900" height="1020" rx="12" fill="#0f172a" stroke="#334155" stroke-width="2"/>
      <rect x="0" y="0" width="900" height="34" rx="12" fill="#1e293b"/>
      <text x="450" y="23" fill="#f8fafc" font-size="14" font-weight="bold" text-anchor="middle">1. VUE EN PLAN (IMPLANTATION PHYSIQUE 2D) – ÉCHELLE COTÉE 1:25</text>

      <!-- Room walls (Outer perimeter) : 5.85 m x 4.30 m -> Drawn at 760 x 560 px -->
      <g transform="translate(70, 60)">
        <!-- Paroi extérieure avec hachures coupe-feu EI60 -->
        <rect x="0" y="0" width="760" height="560" fill="#1e293b" stroke="#64748b" stroke-width="16" rx="4"/>
        <rect x="8" y="8" width="744" height="544" fill="#0b1120"/>

        <!-- Cotes de la pièce -->
        <text x="380" y="-12" fill="#94a3b8" font-size="12" font-weight="bold" text-anchor="middle">Longueur utile : 5.85 m (mitoyenne partie nord J05 &amp; L.TECH 01)</text>
        <text x="-30" y="280" fill="#94a3b8" font-size="12" font-weight="bold" text-anchor="middle" transform="rotate(-90, -30, 280)">Largeur utile : 4.30 m</text>

        <!-- Porte d'accès sécurisée (Bas-Gauche) -->
        <g transform="translate(40, 544)">
          <!-- Battant de porte ouvert à 90° -->
          <rect x="0" y="0" width="100" height="16" fill="#0b1120"/>
          <path d="M 0 0 L 0 70 A 70 70 0 0 0 70 0 Z" fill="#38bdf8" opacity="0.15"/>
          <path d="M 0 0 L 0 70" stroke="#38bdf8" stroke-width="3"/>
          <text x="110" y="25" fill="#38bdf8" font-size="11" font-weight="bold">Porte EI60 Blindée (Contrôle d'accès Badge RFID / ANSSI)</text>
          <circle cx="8" cy="8" r="4" fill="#10b981"/>
          <!-- Lecteur de badge extérieur -->
          <rect x="-25" y="5" width="16" height="24" rx="2" fill="#0284c7" stroke="#38bdf8"/>
          <text x="-17" y="20" fill="#ffffff" font-size="8" font-weight="bold" text-anchor="middle">RFID</text>
        </g>

        <!-- TGBT Salle Serveur (Mur Sud / Ouest) -->
        <g transform="translate(180, 528)">
          <rect width="180" height="24" rx="3" fill="#1e293b" stroke="#f59e0b" stroke-width="2"/>
          <text x="90" y="16" fill="#fbbf24" font-size="10" font-weight="bold" text-anchor="middle">TGBT SALLE SERVEUR (Voies A &amp; B)</text>
        </g>

        <!-- Système Extinction Incendie Gaz Propre (Coin Sud-Est) -->
        <g transform="translate(630, 470)">
          <circle cx="35" cy="35" r="30" fill="#991b1b" stroke="#ef4444" stroke-width="2"/>
          <text x="35" y="32" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">BONBONNE</text>
          <text x="35" y="44" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">NOVEC 1230</text>
          <text x="35" y="78" fill="#fca5a5" font-size="10" font-weight="bold" text-anchor="middle">FK-5-1-12 (42L / 50 bar)</text>
          <!-- Volet de surpression -->
          <rect x="70" y="20" width="18" height="35" fill="#f59e0b" stroke="#fbbf24"/>
          <text x="100" y="40" fill="#fbbf24" font-size="9" font-weight="bold">Volet 50 Pa</text>
        </g>

        <!-- Détecteur optique laser VESDA (Plafond central) -->
        <g transform="translate(360, 480)">
          <rect width="120" height="30" rx="4" fill="#1e293b" stroke="#ef4444" stroke-width="1.5"/>
          <text x="60" y="19" fill="#fca5a5" font-size="10" font-weight="bold" text-anchor="middle">VESDA Laser Aspiration</text>
        </g>

        <!-- Zone Climatiseurs (Mur Nord / Haut) -->
        <g transform="translate(120, 24)">
          <!-- Clim 1 Active -->
          <rect width="220" height="70" rx="4" fill="url(#climGrad)" stroke="#38bdf8" stroke-width="2"/>
          <text x="110" y="25" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">CLIMATISEUR 1 (ACTIF)</text>
          <text x="110" y="42" fill="#e0f2fe" font-size="10" text-anchor="middle">DX Inverter 7.2 kW • 1 850 m³/h</text>
          <text x="110" y="58" fill="#bae6fd" font-size="9" text-anchor="middle">Voie A • Régulation Inverter ~60%</text>

          <!-- Soufflage sous faux plancher -->
          <path d="M 110 70 L 110 130" stroke="#38bdf8" stroke-width="3" stroke-dasharray="4,3" marker-end="url(#coldArrow)"/>
        </g>

        <g transform="translate(420, 24)">
          <!-- Clim 2 Secours -->
          <rect width="220" height="70" rx="4" fill="#1e293b" stroke="#10b981" stroke-width="2"/>
          <text x="110" y="25" fill="#10b981" font-size="11" font-weight="bold" text-anchor="middle">CLIMATISEUR 2 (STANDBY N+1)</text>
          <text x="110" y="42" fill="#cbd5e1" font-size="10" text-anchor="middle">DX Inverter 7.2 kW • Secours actif</text>
          <text x="110" y="58" fill="#94a3b8" font-size="9" text-anchor="middle">Voie B • Permutation auto hebdo</text>

          <!-- Soufflage sous faux plancher -->
          <path d="M 530 94 L 530 130" stroke="#10b981" stroke-width="2" stroke-dasharray="4,3"/>
        </g>

        <!-- URBANISATION : CONFINEMENT DE L'ALLÉE FROIDE (CAC) -->
        <g transform="translate(160, 160)">
          <!-- Hot aisle perimeter (Chaleur expulsée autour) -->
          <rect x="-40" y="-20" width="500" height="310" rx="8" fill="url(#hotAisleGrad)" stroke="#ef4444" stroke-width="1" stroke-dasharray="6,4"/>
          <text x="210" y="5" fill="#f87171" font-size="11" font-weight="bold" text-anchor="middle">ZONE CHAUDE PÉRIMÉTRIQUE (REPRISE HAUTE EN PLÉNUM 32°C - 35°C)</text>

          <!-- BAIE 1 (Gauche) - 800 mm x 1000 mm -> 120 x 150 px -->
          <g transform="translate(30, 30)">
            <rect width="140" height="210" rx="4" fill="url(#rackGrad)" stroke="#38bdf8" stroke-width="2"/>
            <text x="70" y="25" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">BAIE 1 (42U)</text>
            <text x="70" y="45" fill="#ffffff" font-size="10" text-anchor="middle">800 × 1000 mm</text>
            <text x="70" y="70" fill="#94a3b8" font-size="9" text-anchor="middle">Réseau • Sécurité</text>
            <text x="70" y="86" fill="#94a3b8" font-size="9" text-anchor="middle">DMZ • Cœur SVL</text>
            <text x="70" y="102" fill="#94a3b8" font-size="9" text-anchor="middle">Distribution SVL</text>
            <text x="70" y="125" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">P_nom : 1 904 W</text>
            <rect x="10" y="145" width="120" height="22" rx="3" fill="#1e293b" stroke="#f59e0b"/>
            <text x="70" y="160" fill="#fbbf24" font-size="9" font-weight="bold" text-anchor="middle">ATS 1U Rackable</text>
            <rect x="10" y="175" width="120" height="25" rx="3" fill="#1e40af"/>
            <text x="70" y="191" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">Onduleur A (4U)</text>

            <!-- Portes perforées avant et arrière -->
            <rect x="135" y="10" width="5" height="190" fill="#38bdf8"/>
            <rect x="0" y="10" width="5" height="190" fill="#ef4444"/>
          </g>

          <!-- ALLÉE FROIDE CONFINÉE (CAC) : Entre Baie 1 et Baie 2 -->
          <g transform="translate(170, 30)">
            <!-- Sol perforé dalles 600x600 -->
            <rect width="110" height="210" fill="url(#perforatedFloor)" stroke="#38bdf8" stroke-width="2"/>
            <rect width="110" height="210" fill="url(#coldAisleGrad)"/>

            <!-- Toit vitré de confinement -->
            <rect x="0" y="0" width="110" height="210" fill="none" stroke="#38bdf8" stroke-width="2"/>

            <!-- Portes coulissantes vitrées étanches aux extrémités -->
            <rect x="0" y="-6" width="110" height="8" rx="2" fill="#38bdf8"/>
            <text x="55" y="-12" fill="#38bdf8" font-size="9" font-weight="bold" text-anchor="middle">Porte coulissante vitrée</text>
            <rect x="0" y="208" width="110" height="8" rx="2" fill="#38bdf8"/>
            <text x="55" y="228" fill="#38bdf8" font-size="9" font-weight="bold" text-anchor="middle">Porte coulissante vitrée</text>

            <!-- Flèches d'air froid soufflé -->
            <text x="55" y="45" fill="#0284c7" font-size="10" font-weight="bold" text-anchor="middle">ALLÉE FROIDE</text>
            <text x="55" y="60" fill="#0284c7" font-size="10" font-weight="bold" text-anchor="middle">CONFINÉE (CAC)</text>
            <text x="55" y="80" fill="#0369a1" font-size="12" font-weight="bold" text-anchor="middle">22°C ± 1°C</text>
            <text x="55" y="98" fill="#0369a1" font-size="9" text-anchor="middle">HR: 50% ± 5%</text>

            <path d="M 55 120 L 25 120" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>
            <path d="M 55 140 L 85 140" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>
            <path d="M 55 160 L 25 160" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>
            <path d="M 55 180 L 85 180" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>
          </g>

          <!-- BAIE 2 (Droite) - 800 mm x 1000 mm -> 120 x 150 px -->
          <g transform="translate(280, 30)">
            <rect width="140" height="210" rx="4" fill="url(#rackGrad)" stroke="#38bdf8" stroke-width="2"/>
            <text x="70" y="25" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">BAIE 2 (42U)</text>
            <text x="70" y="45" fill="#ffffff" font-size="10" text-anchor="middle">800 × 1000 mm</text>
            <text x="70" y="70" fill="#94a3b8" font-size="9" text-anchor="middle">Datacenter 25G</text>
            <text x="70" y="86" fill="#94a3b8" font-size="9" text-anchor="middle">Proxmox Ceph HA</text>
            <text x="70" y="102" fill="#94a3b8" font-size="9" text-anchor="middle">AD / RADIUS / PBS</text>
            <text x="70" y="125" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">P_nom : 1 920 W</text>
            <rect x="10" y="145" width="120" height="22" rx="3" fill="#1e293b" stroke="#10b981"/>
            <text x="70" y="160" fill="#34d399" font-size="9" font-weight="bold" text-anchor="middle">PBS Backup 2U</text>
            <rect x="10" y="175" width="120" height="25" rx="3" fill="#991b1b"/>
            <text x="70" y="191" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">Onduleur B (4U)</text>

            <!-- Portes perforées avant et arrière -->
            <rect x="0" y="10" width="5" height="190" fill="#38bdf8"/>
            <rect x="135" y="10" width="5" height="190" fill="#ef4444"/>
          </g>

          <!-- Flèches d'air chaud sortant des baies -->
          <path d="M 25 100 L -15 100" stroke="#f87171" stroke-width="2.5" marker-end="url(#hotArrow)"/>
          <path d="M 25 170 L -15 170" stroke="#f87171" stroke-width="2.5" marker-end="url(#hotArrow)"/>
          <path d="M 425 100 L 465 100" stroke="#f87171" stroke-width="2.5" marker-end="url(#hotArrow)"/>
          <path d="M 425 170 L 465 170" stroke="#f87171" stroke-width="2.5" marker-end="url(#hotArrow)"/>
        </g>
      </g>

      <!-- Cartouche descriptif bas de page 1 -->
      <g transform="translate(40, 680)">
        <rect width="820" height="310" rx="8" fill="#1e293b" stroke="#475569"/>
        <text x="20" y="28" fill="#38bdf8" font-size="13" font-weight="bold">RÈGLES D'URBANISATION &amp; SÉCURITÉ PHYSIQUE (DATACENTER J05 SUD)</text>

        <g transform="translate(20, 45)">
          <text x="0" y="0" fill="#f8fafc" font-size="11" font-weight="bold">• Confinement d'Allée Froide (Cold Aisle Containment - CAC) :</text>
          <text x="15" y="18" fill="#cbd5e1" font-size="10">Élimine totalement le mélange air chaud / air froid. Permet de maintenir l'air soufflé à 22°C (recommandations ASHRAE TC 9.9 Class A1).</text>
          <text x="15" y="34" fill="#cbd5e1" font-size="10">Chaque degré supplémentaire gagné sur la consigne de soufflage génère ~4% d'économie d'énergie sur le compresseur frigorifique.</text>

          <text x="0" y="62" fill="#f8fafc" font-size="11" font-weight="bold">• Redondance Climatisation N+1 &amp; Permutation Hebdomadaire :</text>
          <text x="15" y="80" fill="#cbd5e1" font-size="10">2 groupes de 7.2 kW froid sensible unitaire. En régime normal, 1 seul groupe suffit (taux de charge 60.6% inverter, optimal en rendement).</text>
          <text x="15" y="96" fill="#cbd5e1" font-size="10">L'automate inverse les rôles chaque dimanche à 03h00 pour équilibrer l'usure mécanique des compresseurs et des ventilateurs EC.</text>

          <text x="0" y="124" fill="#f8fafc" font-size="11" font-weight="bold">• Protection Incendie par Gaz Propre FK-5-1-12 (Novec 1230) :</text>
          <text x="15" y="142" fill="#cbd5e1" font-size="10">Extinction volumique totale en &lt; 10 secondes par inhibition chimique, sans eau, sans résidu, non conducteur, sans danger pour les personnes.</text>
          <text x="15" y="158" fill="#cbd5e1" font-size="10">Détection précoce par aspiration laser VESDA (alarme dès les premières micro-particules de surchauffe de composant ou câble).</text>

          <text x="0" y="186" fill="#f8fafc" font-size="11" font-weight="bold">• Contrôle d'Accès Physique &amp; Conformité ANSSI :</text>
          <text x="15" y="204" fill="#cbd5e1" font-size="10">Porte coupe-feu EI60 équipée de ventouse électromagnétique 300 kg, verrouillage automatique, déverrouillage par badge RFID MIFARE DESFire EV3.</text>
          <text x="15" y="220" fill="#cbd5e1" font-size="10">Bouton poussoir de sortie d'urgence sous bris de glace, contact d'ouverture surveillé et caméra IP dédiée filmant le sas d'accès.</text>
        </g>
      </g>
    </g>
    ''')

    # ==============================================================================
    # PARTIE DROITE : COUPE TRANSVERSALE AÉRAULIQUE (SIDE ELEVATION SECTION)
    # ==============================================================================
    svg.append('''
    <!-- COUPE ÉLÉVATION AÉRAULIQUE -->
    <g transform="translate(980, 110)" filter="url(#shadowAeraulic)">
      <rect width="660" height="1020" rx="12" fill="#0f172a" stroke="#334155" stroke-width="2"/>
      <rect x="0" y="0" width="660" height="34" rx="12" fill="#1e293b"/>
      <text x="330" y="23" fill="#f8fafc" font-size="14" font-weight="bold" text-anchor="middle">2. COUPE TRANSVERSALE AÉRAULIQUE &amp; FLUX THERMIQUES</text>

      <g transform="translate(40, 60)">
        <!-- Slab and ceiling references -->
        <!-- Plafond béton brut (H = 3.20 m) -->
        <rect x="0" y="0" width="580" height="18" fill="#334155"/>
        <text x="290" y="-8" fill="#94a3b8" font-size="11" font-weight="bold" text-anchor="middle">DALLE SUPÉRIEURE BÉTON BRUT (H = +3.20 m)</text>

        <!-- Faux-plafond plénum (H = 2.70 m) -->
        <line x1="0" y1="70" x2="580" y2="70" stroke="#64748b" stroke-width="3" stroke-dasharray="8,6"/>
        <text x="490" y="60" fill="#f87171" font-size="11" font-weight="bold">Plénum Chaud (+2.70 m)</text>

        <!-- Sol brut dalle basse (H = 0.00 m) -->
        <rect x="0" y="520" width="580" height="24" fill="#334155"/>
        <text x="290" y="560" fill="#94a3b8" font-size="11" font-weight="bold" text-anchor="middle">DALLE INFÉRIEURE BÉTON (H = 0.00 m)</text>

        <!-- Faux-plancher technique (H = +0.30 m) -->
        <line x1="0" y1="460" x2="580" y2="460" stroke="#0284c7" stroke-width="4"/>
        <text x="480" y="495" fill="#38bdf8" font-size="11" font-weight="bold">Plénum Froid (H: 30 cm)</text>

        <!-- Vérins réglables faux-plancher -->
        <g stroke="#64748b" stroke-width="2">
          <line x1="40" y1="460" x2="40" y2="520"/><line x1="120" y1="460" x2="120" y2="520"/>
          <line x1="200" y1="460" x2="200" y2="520"/><line x1="280" y1="460" x2="280" y2="520"/>
          <line x1="360" y1="460" x2="360" y2="520"/><line x1="440" y1="460" x2="440" y2="520"/>
          <line x1="520" y1="460" x2="520" y2="520"/>
        </g>

        <!-- Climatiseur en coupe (Gauche) -->
        <g transform="translate(20, 70)">
          <rect width="110" height="390" fill="url(#climGrad)" stroke="#38bdf8" stroke-width="2"/>
          <text x="55" y="40" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">ARMOIRE</text>
          <text x="55" y="58" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">CLIM DX</text>
          <text x="55" y="76" fill="#e0f2fe" font-size="10" text-anchor="middle">7.2 kW Sensible</text>

          <!-- Batterie froide -->
          <rect x="15" y="120" width="80" height="50" rx="3" fill="#0284c7" stroke="#38bdf8"/>
          <text x="55" y="150" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">Évaporateur DX</text>

          <!-- Ventilateur EC -->
          <circle cx="55" cy="240" r="28" fill="#1e293b" stroke="#38bdf8" stroke-width="2"/>
          <path d="M 40 240 Q 55 220 70 240 Q 55 260 40 240" fill="#38bdf8"/>
          <text x="55" y="285" fill="#bae6fd" font-size="9" text-anchor="middle">Ventilateur EC</text>

          <!-- Soufflage vers bas dans plénum -->
          <path d="M 55 370 L 55 410" stroke="#38bdf8" stroke-width="4" marker-end="url(#coldArrow)"/>
          <text x="55" y="380" fill="#bae6fd" font-size="9" text-anchor="middle">Soufflage</text>

          <!-- Reprise haute en plénum -->
          <path d="M 55 -25 L 55 10" stroke="#f87171" stroke-width="4" marker-end="url(#hotArrow)"/>
          <text x="55" y="-30" fill="#fca5a5" font-size="9" font-weight="bold" text-anchor="middle">Reprise 32-35°C</text>
        </g>

        <!-- BAIE 1 et BAIE 2 en coupe -->
        <!-- BAIE 1 -->
        <g transform="translate(180, 160)">
          <rect width="100" height="300" rx="2" fill="url(#rackGrad)" stroke="#64748b" stroke-width="2"/>
          <text x="50" y="30" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">BAIE 1 (42U)</text>
          <text x="50" y="50" fill="#cbd5e1" font-size="10" text-anchor="middle">P_nom: 1.9 kW</text>

          <!-- Serveurs U empilés -->
          <rect x="10" y="70" width="80" height="15" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="90" width="80" height="15" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="110" width="80" height="30" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="145" width="80" height="40" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="190" width="80" height="40" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="240" width="80" height="45" fill="#1e40af" stroke="#3b82f6"/>
          <text x="50" y="267" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">UPS A (4U)</text>

          <!-- Aspiration avant / Refoulement arrière -->
          <path d="M 105 130 L 15 130" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>
          <path d="M 0 130 L -30 130" stroke="#f87171" stroke-width="2.5" marker-end="url(#hotArrow)"/>
          <text x="-40" y="125" fill="#f87171" font-size="10" font-weight="bold" text-anchor="end">Air chaud 35°C</text>
        </g>

        <!-- ALLÉE FROIDE CONFINÉE (CAC) AU CENTRE -->
        <g transform="translate(280, 160)">
          <!-- Zone confinée étanche -->
          <rect width="110" height="300" fill="url(#coldAisleGrad)"/>

          <!-- Toit vitré de confinement -->
          <line x1="0" y1="0" x2="110" y2="0" stroke="#38bdf8" stroke-width="5"/>
          <text x="55" y="-10" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">Toit étanche vitré</text>

          <!-- Dalles perforées faux plancher (65% vide) -->
          <rect x="5" y="300" width="100" height="12" fill="url(#perforatedFloor)" stroke="#38bdf8" stroke-width="2"/>
          <text x="55" y="330" fill="#38bdf8" font-size="9" font-weight="bold" text-anchor="middle">Dalles perforées</text>

          <!-- Flux d'air montant du faux plancher -->
          <path d="M 55 350 L 55 240" stroke="#38bdf8" stroke-width="3" marker-end="url(#coldArrow)"/>
          <path d="M 35 240 L 15 240" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>
          <path d="M 75 240 L 95 240" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>

          <text x="55" y="100" fill="#0284c7" font-size="11" font-weight="bold" text-anchor="middle">ALLÉE FROIDE</text>
          <text x="55" y="120" fill="#0369a1" font-size="14" font-weight="bold" text-anchor="middle">22°C</text>
          <text x="55" y="140" fill="#0284c7" font-size="10" text-anchor="middle">Confinée</text>
        </g>

        <!-- BAIE 2 -->
        <g transform="translate(390, 160)">
          <rect width="100" height="300" rx="2" fill="url(#rackGrad)" stroke="#64748b" stroke-width="2"/>
          <text x="50" y="30" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">BAIE 2 (42U)</text>
          <text x="50" y="50" fill="#cbd5e1" font-size="10" text-anchor="middle">P_nom: 1.9 kW</text>

          <!-- Serveurs U empilés -->
          <rect x="10" y="70" width="80" height="30" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="105" width="80" height="30" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="140" width="80" height="40" fill="#1e293b" stroke="#475569"/>
          <rect x="10" y="185" width="80" height="45" fill="#1e293b" stroke="#10b981"/>
          <text x="50" y="212" fill="#34d399" font-size="9" font-weight="bold" text-anchor="middle">PBS (2U)</text>
          <rect x="10" y="240" width="80" height="45" fill="#991b1b" stroke="#ef4444"/>
          <text x="50" y="267" fill="#ffffff" font-size="9" font-weight="bold" text-anchor="middle">UPS B (4U)</text>

          <!-- Aspiration avant / Refoulement arrière -->
          <path d="M -5 130 L 85 130" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#coldArrow)"/>
          <path d="M 100 130 L 130 130" stroke="#f87171" stroke-width="2.5" marker-end="url(#hotArrow)"/>
          <text x="140" y="125" fill="#f87171" font-size="10" font-weight="bold">Air chaud 35°C</text>
        </g>

        <!-- Boucle d'air chaud montant vers le plénum -->
        <path d="M 525 110 L 525 40 L 145 40" stroke="#f87171" stroke-width="3" stroke-dasharray="6,4" fill="none" marker-end="url(#hotArrow)"/>
        <text x="350" y="28" fill="#f87171" font-size="10" font-weight="bold" text-anchor="middle">Convection naturelle &amp; extraction plénum 32°C - 35°C</text>

        <!-- Distribution d'air froid sous plancher -->
        <path d="M 90 490 L 335 490 L 335 470" stroke="#38bdf8" stroke-width="3" stroke-dasharray="6,4" fill="none" marker-end="url(#coldArrow)"/>
        <text x="210" y="510" fill="#38bdf8" font-size="10" font-weight="bold" text-anchor="middle">Surpression plénum froid 25 Pa • T = 20°C - 22°C</text>
      </g>

      <!-- Cartouche technique bas de page 2 -->
      <g transform="translate(30, 680)">
        <rect width="600" height="310" rx="8" fill="#1e293b" stroke="#475569"/>
        <text x="20" y="28" fill="#38bdf8" font-size="13" font-weight="bold">PARAMÈTRES THERMODYNAMIQUES &amp; AÉRAULIQUES</text>

        <g transform="translate(20, 45)">
          <text x="0" y="0" fill="#f8fafc" font-size="11" font-weight="bold">1. Bilan thermique à évacuer :</text>
          <text x="15" y="17" fill="#cbd5e1" font-size="10">• Charge nominale salle : <tspan fill="#38bdf8" font-weight="bold">4.37 kW</tspan> (14 899 BTU/h)</text>
          <text x="15" y="32" fill="#cbd5e1" font-size="10">• Charge crête maximale : <tspan fill="#f87171" font-weight="bold">7.12 kW</tspan> (24 291 BTU/h)</text>

          <text x="0" y="58" fill="#f8fafc" font-size="11" font-weight="bold">2. Dimensionnement aéraulique :</text>
          <text x="15" y="75" fill="#cbd5e1" font-size="10">• Débit d'air soufflé unitaire : 1 850 m³/h à 22°C</text>
          <text x="15" y="90" fill="#cbd5e1" font-size="10">• Échauffement moyen à travers les serveurs : ΔT = 9.8 K (22°C ➜ 31.8°C)</text>
          <text x="15" y="105" fill="#cbd5e1" font-size="10">• Vitesse d'air dans l'allée confinée : &lt; 1.2 m/s (confort acoustique &amp; zéro perturbation)</text>

          <text x="0" y="132" fill="#f8fafc" font-size="11" font-weight="bold">3. Recommandations ASHRAE TC 9.9 (Classe A1) :</text>
          <text x="15" y="149" fill="#cbd5e1" font-size="10">• Plage admissible température allée froide : 18°C à 27°C (consigne retenue: 22°C)</text>
          <text x="15" y="164" fill="#cbd5e1" font-size="10">• Plage d'humidité relative : 40% à 60% HR (point de rosée &lt; 15°C)</text>

          <text x="0" y="192" fill="#f8fafc" font-size="11" font-weight="bold">4. Métrologie continue &amp; Capteurs environnementaux :</text>
          <text x="15" y="209" fill="#cbd5e1" font-size="10">• 6 sondes de température / HR (3 par baie : haut U38, milieu U20, bas U5)</text>
          <text x="15" y="224" fill="#cbd5e1" font-size="10">• Câble senseur de détection de fuite d'eau sous les bacs à condensats et le faux-plancher</text>
        </g>
      </g>
    </g>
    ''')

    svg.append('</svg>')

    svg_path.write_text("\n".join(svg), encoding="utf-8")
    print(f"Schéma aéraulique généré : {svg_path.resolve()}")


if __name__ == "__main__":
    generer_synoptique_electrique()
    generer_aeraulique_salle_serveur()
