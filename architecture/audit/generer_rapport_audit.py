#!/usr/bin/env python3
"""Générateur du Rapport d'Audit Multi-Agents de l'Infrastructure Réseau & Système.
Projet IUT Marseille – Luminy (SAÉ 5.02 / BUT3 R&T) · RudyLink Infrastructure.
Compile un rapport d'audit complet en HTML puis en PDF via Chromium sans interface.
"""
import subprocess
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PDF_OUT = HERE / "Rapport_Audit_Infrastructure_Marseille.pdf"
HTML_OUT = HERE / "Rapport_Audit_Infrastructure_Marseille.html"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport d'Audit Multi-Agents – Infrastructure Campus Marseille Luminy</title>
<style>
  @page {
    size: A4;
    margin: 14mm 14mm 16mm 14mm;
    @bottom-right {
      content: "Page " counter(page) " sur " counter(pages);
      font-size: 8pt;
      color: #64748B;
      font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif;
    }
    @bottom-left {
      content: "RudyLink Infrastructure · Audit Multi-Agents (Réseau, Sécurité, Infra) · Nov. 2026";
      font-size: 8pt;
      color: #64748B;
      font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif;
    }
  }

  * { box-sizing: border-box; }
  body {
    font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif;
    font-size: 8.8pt;
    line-height: 1.45;
    color: #1E293B;
    background: #FFFFFF;
    margin: 0;
  }

  /* Couvertures & Titres */
  .page-cover {
    page-break-after: always;
    padding-top: 25mm;
    text-align: center;
  }
  .cover-badge {
    display: inline-block;
    background: #0F172A;
    color: #38BDF8;
    padding: 3mm 7mm;
    border-radius: 4mm;
    font-size: 9pt;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8mm;
  }
  .cover-title {
    font-family: 'DejaVu Serif', Georgia, serif;
    font-size: 24pt;
    font-weight: bold;
    color: #0F2942;
    margin: 0 0 4mm;
    line-height: 1.2;
  }
  .cover-subtitle {
    font-size: 13pt;
    color: #475569;
    margin: 0 0 10mm;
  }
  .cover-card {
    background: #F8FAFC;
    border: 1.5px solid #CBD5E1;
    border-radius: 4mm;
    padding: 6mm 10mm;
    margin: 12mm auto;
    max-width: 150mm;
    text-align: left;
  }
  .cover-meta {
    font-size: 9.5pt;
    line-height: 1.8;
  }
  .cover-meta b { color: #0F2942; }

  /* Typographie de contenu */
  h1 {
    font-family: 'DejaVu Serif', Georgia, serif;
    font-size: 18pt;
    color: #0F2942;
    margin: 0 0 3mm;
    padding-bottom: 2mm;
    border-bottom: 2px solid #1F4E8C;
  }
  h2 {
    font-family: 'DejaVu Serif', Georgia, serif;
    font-size: 12.5pt;
    color: #1F4E8C;
    margin: 7mm 0 2.5mm;
    padding-bottom: 1.5mm;
    border-bottom: 1px solid #CBD5E1;
  }
  h3 {
    font-size: 10pt;
    color: #0F172A;
    margin: 4mm 0 1.5mm;
    font-weight: bold;
  }
  p { margin: 1.5mm 0 2.5mm; text-align: justify; }
  ul, ol { margin: 1.5mm 0 3mm 4mm; padding-left: 3mm; }
  li { margin-bottom: 1.2mm; }

  .saut { page-break-before: always; }
  .avoid-break { page-break-inside: avoid; }

  /* Tableaux */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 3mm 0 4mm;
    font-size: 8pt;
  }
  th {
    background: #E2E8F0;
    color: #0F172A;
    font-weight: bold;
    text-align: left;
    padding: 2mm 2.5mm;
    border-bottom: 1.5px solid #94A3B8;
  }
  td {
    padding: 1.8mm 2.5mm;
    border-bottom: 1px solid #E2E8F0;
    vertical-align: top;
  }
  tr:nth-child(even) td {
    background: #F8FAFC;
  }

  /* Cartes et Métriques */
  .grid-scores {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 3mm;
    margin: 4mm 0 6mm;
  }
  .card-score {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 2.5mm;
    padding: 3mm;
    text-align: center;
  }
  .card-score .num {
    font-size: 17pt;
    font-weight: bold;
    color: #1F4E8C;
    display: block;
    margin-bottom: 1mm;
  }
  .card-score .label {
    font-size: 7.8pt;
    font-weight: bold;
    color: #475569;
    text-transform: uppercase;
  }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 0.6mm 2mm;
    border-radius: 1mm;
    font-size: 7.2pt;
    font-weight: bold;
    text-transform: uppercase;
  }
  .badge-critique { background: #FEE2E2; color: #991B1B; border: 1px solid #F87171; }
  .badge-majeur { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
  .badge-mineur { background: #E0E7FF; color: #3730A3; border: 1px solid #A5B4FC; }
  .badge-conforme { background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
  .badge-reco { background: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; }

  /* Encadrés d'alerte et citations */
  .box-note {
    background: #F0FDF4;
    border-left: 3.5px solid #16A34A;
    padding: 2.5mm 3.5mm;
    margin: 3mm 0;
    border-radius: 0 2mm 2mm 0;
  }
  .box-warn {
    background: #FEFCE8;
    border-left: 3.5px solid #CA8A04;
    padding: 2.5mm 3.5mm;
    margin: 3mm 0;
    border-radius: 0 2mm 2mm 0;
  }
  .box-danger {
    background: #FEF2F2;
    border-left: 3.5px solid #DC2626;
    padding: 2.5mm 3.5mm;
    margin: 3mm 0;
    border-radius: 0 2mm 2mm 0;
  }

  /* Boîtes de questions soutenance */
  .qa-block {
    background: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 2.5mm;
    padding: 3mm 4mm;
    margin: 3.5mm 0;
    page-break-inside: avoid;
  }
  .qa-q {
    font-weight: bold;
    color: #0F2942;
    font-size: 9pt;
    margin-bottom: 1.5mm;
  }
  .qa-trap {
    font-size: 7.8pt;
    color: #991B1B;
    background: #FEE2E2;
    padding: 1mm 2.5mm;
    border-radius: 1mm;
    display: inline-block;
    margin-bottom: 2mm;
    font-weight: bold;
  }
  .qa-exp {
    font-size: 8.4pt;
    color: #1E293B;
    line-height: 1.45;
  }
  .qa-exp b { color: #1F4E8C; }

  code {
    font-family: 'DejaVu Sans Mono', Consolas, monospace;
    font-size: 7.6pt;
    background: #F1F5F9;
    padding: 0.2mm 1.5mm;
    border-radius: 0.8mm;
    color: #0F172A;
  }
</style>
</head>
<body>

<!-- PAGE DE GARDE -->
<div class="page-cover">
  <div class="cover-badge">Audit Technique & Architectural Indépendant</div>
  <div class="cover-title">RAPPORT D'AUDIT MULTI-AGENTS<br>DE L'INFRASTRUCTURE RÉSEAU & SYSTÈMES</div>
  <div class="cover-subtitle">Projet Campus Universitaire IUT Marseille – Luminy · RudyLink Infrastructure</div>

  <div class="cover-card">
    <div class="cover-meta">
      <b>Client / Établissement :</b> IUT d'Aix-Marseille (Département Réseaux & Télécoms)<br>
      <b>Société d'Ingénierie MOE :</b> RudyLink Infrastructure (BUT3 R&T Promotion 2026-2027)<br>
      <b>Date d'Audit :</b> 15 novembre 2026 · Audit en mode Lecture Seule (Read-Only)<br>
      <b>Collège d'Auditeurs Spécialisés :</b><br>
      &bull; <i>Agent 1 :</i> Architecture Réseau L2/L3, Protocoles & Sans-Fil (CCIE / Ingénierie)<br>
      &bull; <i>Agent 2 :</i> Cybersécurité, Filtrage Périmétrique & Conformité ANSSI (PASSI / RSSI)<br>
      &bull; <i>Agent 3 :</i> Infrastructure Physique, Virtualisation Proxmox, Stockage & Datacenter<br>
      <b>Référentiels appliqués :</b> ANSSI (PA-022, PA-044, BP-031, PA-043, PA-099, BP-100, PA-105), EBIOS RM v1.5, Directive NIS 2, Guides ASHRAE A1 & Normes NF C 15-100 / ISO 11801.
    </div>
  </div>

  <div style="margin-top: 15mm; font-size: 10pt; color: #475569;">
    <b>Verdict Global :</b> <span style="color: #059669; font-weight: bold; font-size: 13pt;">16.9 / 20</span> — Mention Très Bien<br>
    <i>Infrastructure d'une maturité technique remarquable, flirtant avec les standards industriels de production.</i>
  </div>
</div>

<!-- SECTION 1 : SYNTHÈSE EXÉCUTIVE ET TABLEAU DE BORD -->
<h1>1. Synthèse Exécutive & Évaluation Globale</h1>
<p>
À la demande de l'équipe projet, un audit approfondi en lecture seule de l'intégralité des dossiers d'architecture, plans d'adressage, scripts de modélisation et bilans financiers/énergétiques a été mené par trois agents spécialisés. L'objectif est d'évaluer la robustesse technique de la solution conçue pour le site universitaire de Marseille-Luminy (relié au site jumeau de Digne/Gap), d'identifier les vulnérabilités résiduelles et de préparer rigoureusement l'équipe aux exigences de la soutenance orale finale.
</p>

<div class="grid-scores">
  <div class="card-score">
    <span class="num">18.0 / 20</span>
    <span class="label">Architecture Réseau L2/L3</span>
  </div>
  <div class="card-score">
    <span class="num">17.0 / 20</span>
    <span class="label">Cybersécurité & ANSSI</span>
  </div>
  <div class="card-score">
    <span class="num">15.8 / 20</span>
    <span class="label">Systèmes & Datacenter</span>
  </div>
  <div class="card-score" style="border: 1.5px solid #1F4E8C; background: #EFF6FF;">
    <span class="num" style="color: #1F4E8C;">16.9 / 20</span>
    <span class="label">Score Global Pondéré</span>
  </div>
</div>

<div class="box-note">
  <b>Point Fort Global :</b> L'infrastructure témoigne d'une cohérence rare entre les différentes couches. L'intégration des guides ANSSI dès la conception (<i>Security by Design</i>), le partitionnement en 5 VRF hermétiques sans route-leaking, la suppression complète des boucles L2 actives via StackWise Virtual et MEC LACP, l'automatisation du plan d'adressage mnémonique et le bilan PUE calculé à 1,34 constituent des réalisations exemplaires.
</div>

<h2>Tableau de Synthèse des Constats Critiques Multi-Agents</h2>
<table>
  <tr>
    <th>Réf</th>
    <th>Domaine</th>
    <th>Constat / Risque Identifié</th>
    <th>Sévérité</th>
    <th>Impact Opérationnel</th>
  </tr>
  <tr>
    <td><b>NET-01</b></td>
    <td>Wi-Fi & Mobilité</td>
    <td>Rupture de session TCP/UDP lors du roaming Wi-Fi inter-étages (FlexConnect local switching VLAN 115 ↔ 215 sans tunnel de mobilité L3).</td>
    <td><span class="badge badge-critique">Critique</span></td>
    <td>Coupure brutale des appels VoIP/Teams et sessions SSH lors des déplacements usagers entre le RDC et le 1er étage.</td>
  </tr>
  <tr>
    <td><b>SEC-01</b></td>
    <td>Pare-feu & Débit</td>
    <td>Goulot d'étranglement de l'inspection UTM sur le Stormshield SN710 (plafond à ~2,5 Gbps face aux flux inter-VRF 10G/40G agrégés).</td>
    <td><span class="badge badge-critique">Critique</span></td>
    <td>Saturation CPU du moteur ASQ lors des sauvegardes ou transferts massifs de fichiers ; risque de déni de service interne.</td>
  </tr>
  <tr>
    <td><b>SYS-01</b></td>
    <td>Architecture Système</td>
    <td>Discordance documentaire majeure entre le chiffrage (Ceph 3 nœuds, 28,5 k€) et l'architecture L2 réelle (ZFS répliqué 2 nœuds + QDevice).</td>
    <td><span class="badge badge-majeur">Majeur</span></td>
    <td>Incohérence budgétaire de 9 500 € HT ; omission du chiffrage de l'appliance physique témoin NM-WITNESS.</td>
  </tr>
  <tr>
    <td><b>SYS-02</b></td>
    <td>Dimensionnement</td>
    <td>Hypertrophie anachronique de 16 serveurs physiques mono-rôles 1U en DMZ et Datacenter (37,8 k€ de serveurs + 6,6 k€ d'OS Windows).</td>
    <td><span class="badge badge-majeur">Majeur</span></td>
    <td>Surcoût budgétaire important, occupation inutile de 12U en baie, surconsommation thermique (~1 400 W constants).</td>
  </tr>
  <tr>
    <td><b>SEC-02</b></td>
    <td>Active Directory</td>
    <td>Contrôleurs de domaine DT-AD1/2 (Tier 0) mélangés dans le même VLAN 300 et domaine de broadcast que les serveurs DHCP et membres (Tier 1).</td>
    <td><span class="badge badge-majeur">Majeur</span></td>
    <td>Non-conformité au guide ANSSI PA-099 ; risque d'élévation de privilèges et mouvement latéral vers le Tier 0.</td>
  </tr>
  <tr>
    <td><b>SEC-03</b></td>
    <td>Sauvegarde & Ransomware</td>
    <td>Absence d'immuabilité formelle (S3 Object Lock en mode Compliance WORM) et d'Air-Gap physique sur les datastores PBS locaux/distants.</td>
    <td><span class="badge badge-majeur">Majeur</span></td>
    <td>Vulnérabilité totale des sauvegardes en cas de compromission des identifiants d'administration (chiffrement par ransomware).</td>
  </tr>
  <tr>
    <td><b>SYS-03</b></td>
    <td>Environnement Sous-Sol</td>
    <td>Implantation de la salle serveur en sous-sol (J05) à Luminy sans plancher surélevé étanche, sans batardeau ni extinction auto par gaz.</td>
    <td><span class="badge badge-majeur">Majeur</span></td>
    <td>Vulnérabilité critique aux inondations méditerranéennes et destruction totale du datacenter en cas d'incendie nocturne.</td>
  </tr>
  <tr>
    <td><b>NET-02</b></td>
    <td>Architecture Cœur/Distri</td>
    <td>4 switchs Cisco C9500-16X en distribution colocalisés dans la même baie que le cœur CL-SW au lieu d'un Cœur Replié (Collapsed Core).</td>
    <td><span class="badge badge-mineur">Mineur</span></td>
    <td>Surcoût d'investissement de 38 000 € HT et 640 W constants d'électricité non indispensables pour 15 switchs d'accès.</td>
  </tr>
  <tr>
    <td><b>SEC-04</b></td>
    <td>Traçabilité Légale</td>
    <td>Sous-dimensionnement de la chaîne de collecte des journaux sur une VM Docker unique pour la conservation obligatoire LCEN 1 an.</td>
    <td><span class="badge badge-mineur">Mineur</span></td>
    <td>Risque d'épuisement des ressources de journalisation et non-recevabilité juridique en cas de réquisition judiciaire.</td>
  </tr>
</table>

<!-- SECTION 2 : AUDIT RÉSEAU L2/L3 & SANS-FIL -->
<div class="saut"></div>
<h1>2. Audit Spécialisé – Architecture Réseau L2/L3 & Sans-Fil</h1>
<p class="cover-subtitle" style="margin-bottom: 3mm; font-size: 10pt;">Évalué par l'Agent Réseau · Note : <b>18.0 / 20</b> (Mention Très Bien)</p>

<h2>2.1. Analyse des Forces et Atouts Réseau</h2>
<ul>
  <li><b>Virtualisation de châssis & Suppression des boucles L2 :</b> Déploiement généralisé de <b>Cisco StackWise Virtual (SVL)</b> sur les Catalyst 9500 (2x40G SVL + 10G DAD dédié en Fast-Hello), et de piles matérielles <b>StackWise-80</b> (C9200L) et <b>StackWise-1T</b> (C9300X). L'accès s'interconnecte systématiquement via des agrégats <b>MEC LACP (802.3ad)</b> répartis sur les deux membres physiques : l'ensemble des liens transmet activement sans aucun blocage Spanning Tree en fonctionnement nominal.</li>
  <li><b>Spanning Tree Rapid-PVST+ maîtrisé en filet de sécurité :</b> Priorités rigoureusement configurées pour figer la racine (DL-B1 = 0 pour VLANs 1xx, DL-B2 = 0 pour VLANs 2xx, CL = 4096, switchs d'accès verrouillés à 61440). Déploiement systématique de <code>BPDU Guard</code> et <code>PortFast</code> sur les prises d'accès, <code>Root Guard</code> sur les descentes de distribution et <code>Loop Guard</code> sur les troncs.</li>
  <li><b>Cloisonnement L3 VRF-Lite & Routage OSPFv3 Multi-AF :</b> Isolation étanche de 5 VRF (<code>USR</code>, <code>IOT</code>, <code>GST</code>, <code>SRV</code>, <code>ADM</code>) sans aucun <i>route-leaking</i> sur le cœur. Routage interne dynamique unifié via <b>OSPFv3 multi-address-family (RFC 5838)</b> avec liens point-à-point en <code>/31</code> IPv4 et <code>/127</code> IPv6, couplé à <b>BFD (timers 300 ms × 3)</b> garantissant une détection de rupture et une convergence en moins de 900 ms.</li>
  <li><b>Plan d'adressage exemplaire & Résilience IPv6 (NPTv6) :</b> Correspondance mnémonique parfaite où le 4e hextet IPv6 reflète le VLAN (<code>2001:660:5402:4<vid>::/64</code>), avec conservation de la terminaison décimale identique entre IPv4 et IPv6 (ex: <code>.41</code> ↔ <code>::41</code>). En cas de rupture du lien primaire AMU/RENATER, le mécanisme sans état <b>NPTv6 (RFC 6296)</b> sur le FortiGate traduit le préfixe vers l'opérateur de secours sans casser la connectivité de bout en bout.</li>
  <li><b>Modélisation Wi-Fi 6E prédictive :</b> Étude de propagation radio multi-parois COST 231 basée sur l'extraction des plans d'architecte, garantissant un RSSI supérieur à −67 dBm à 5 GHz avec 38 bornes Cisco CW9164I exploitées en <b>FlexConnect commutation locale</b>.</li>
</ul>

<h2>2.2. Faiblesses et Risques Techniques Identifiés</h2>
<ul>
  <li><b>Rupture d'itinérance Wi-Fi L3 inter-étages :</b> En mode FlexConnect local, les clients du RDC sont rattachés au VLAN 115 (<code>10.13.20.0/22</code>) et ceux du 1er étage au VLAN 215 (<code>10.13.36.0/22</code>). Lors d'un déplacement dans les escaliers ou halls, le client change de borne et de VLAN sans tunnel de mobilité (Foreign-Anchor). Sa session TCP/UDP est immédiatement rompue (appels voix, visio, SSH).</li>
  <li><b>Surcoût topologique des 4x C9500 en Distribution :</b> Les switchs DL-SW sont physiquement installés dans la même armoire (Baie 1) que le cœur CL-SW. L'achat de 4 switchs C9500 (38 000 € HT) pour raccorder seulement 15 switchs d'accès engendre une surconsommation de 640 W et complexifie inutilement la topologie face à une solution <i>Collapsed Core</i> sur 2x C9500-48Y4C.</li>
  <li><b>Traversée inter-VRF asymétrique et goulot EL-SW :</b> Le transit inter-VRF (ex: usagers vers datacenter) traverse obligatoirement les switchs C9200L de la pile <code>EL-SW</code> dotés de petits buffers (6 Mo partagés) et le firewall Stormshield SN710 dont le débit d'inspection chute sous forte charge.</li>
  <li><b>Saturation critique du pool Wi-Fi Étudiants :</b> Le pool DHCP <code>WIFI-ETU-B1</code> (1022 adresses) présente un taux d'occupation nominal de <b>94 %</b> pour 960 clients calculés. Avec des baux usuels et les arrivées/départs d'étudiants, le risque d'épuisement de baux (starvation) est immédiat.</li>
</ul>

<!-- SECTION 3 : AUDIT CYBERSÉCURITÉ & ANSSI -->
<div class="saut"></div>
<h1>3. Audit Spécialisé – Cybersécurité & Conformité ANSSI</h1>
<p class="cover-subtitle" style="margin-bottom: 3mm; font-size: 10pt;">Évalué par l'Agent Sécurité · Note : <b>17.0 / 20</b> (Mention Très Bien)</p>

<h2>3.1. Analyse des Forces et Alignements ANSSI</h2>
<ul>
  <li><b>Double barrière pare-feu hétérogène (ANSSI PA-044) :</b> Architecture en cascade combinant un cluster de <b>FortiGate 120G</b> en périphérie (SD-WAN, NAT/PAT, terminaison VPN et DMZ publique) et un cluster de <b>Stormshield SN710 qualifié Standard ANSSI</b> en cœur interne pour le filtrage inter-VRF. Cette dissemblance protège le système contre l'exploitation d'une faille 0-day touchant un seul constructeur.</li>
  <li><b>Administration sécurisée Zero-Trust (ANSSI PA-022 v3) :</b> Création d'une zone <i>Net Management</i> hautement cloisonnée, accessible uniquement au travers du bastion <b>Teleport Community</b> (authentification MFA FIDO2/WebAuthn, certificats SSH/TLS éphémères, audit et réenregistrement vidéo des sessions). Implantation de postes d'administration dédiés (<b>PAW</b>) sur le VLAN 906 et isolation physique des IPMI/iDRAC sur le VLAN 901.</li>
  <li><b>Sécurité First-Hop L2 avancée (ANSSI PA-043) :</b> Authentification <b>802.1X multi-auth</b> avec bascule MAB et affectation dynamique de VLAN par RADIUS (DT-RAD1/2). Activation généralisée du <b>DHCP Snooping</b> avec option 82, <b>Dynamic ARP Inspection (DAI)</b> et <b>IP Source Guard (IPSG)</b>. En IPv6, filtrage strict par <b>RA Guard</b> (seules les SVI des DL peuvent annoncer des préfixes) et DHCPv6 Guard.</li>
  <li><b>Cloisonnement DMZ étagé (Passerelle Internet v3) :</b> Séparation en 3 sous-zones (DMZ-FRONT 400, DMZ-BACK 401, DMZ-GEST 402) avec terminaison applicative et rupture protocolaire sur cluster de reverse proxies Caddy (VIP 172.16.13.10), isolant totalement les serveurs applicatifs du réseau externe.</li>
</ul>

<h2>3.2. Faiblesses et Vulnérabilités Résiduelles Identifiées</h2>
<ul>
  <li><b>Goulet d'étranglement de l'UTM Stormshield SN710 :</b> Le débit du SN710 s'effondre à <b>2,5 à 3 Gbps</b> lorsque l'inspection applicative et l'IPS sont engagés. Faire passer l'intégralité du trafic inter-VRF par ce firewall unique expose l'infrastructure à une saturation complète lors de transferts de fichiers volumineux ou de sauvegardes massives vers PBS.</li>
  <li><b>Angle mort critique sur le trafic chiffré SSL/TLS :</b> Plus de 90 % du trafic usager vers Internet est chiffré en HTTPS. Aucun mécanisme d'inspection ou de déchiffrement SSL/TLS n'est prévu sur les pare-feux, rendant l'antivirus de flux et l'IPS aveugles face aux malwares et canaux C2 chiffrés.</li>
  <li><b>Mélange des Tiers Active Directory (ANSSI PA-099) :</b> Les contrôleurs de domaine <code>DT-AD1</code> et <code>DT-AD2</code> (Tier 0) résident dans le même VLAN 300 que les serveurs DHCP et membres (Tier 1), exposant le domaine à des attaques par rebond (NTLM relay, compromission d'applications).</li>
  <li><b>Absence d'immuabilité (WORM) sur les sauvegardes (ANSSI BP-100) :</b> Le serveur PBS local (<code>DT-BKP1</code>) et la copie Cloud ne disposent pas de verrouillage immuable (S3 Object Lock en mode Compliance). Un rançongiciel disposant de privilèges administrateur peut purger l'ensemble des datastores locaux et distants.</li>
  <li><b>Obligation de rétention légale LCEN 1 an non dimensionnée :</b> Une unique VM Docker standard hébergeant rsyslog est prévue. La loi imposant la conservation des logs de translation SNAT/PAT et baux DHCP pendant 365 jours, ce dispositif est insuffisant sans base de données colonnaire dédiée (OpenSearch/ClickHouse).</li>
</ul>

<!-- SECTION 4 : AUDIT INFRASTRUCTURE & SYSTÈMES -->
<div class="saut"></div>
<h1>4. Audit Spécialisé – Infrastructure Systèmes, Virtualisation & Datacenter</h1>
<p class="cover-subtitle" style="margin-bottom: 3mm; font-size: 10pt;">Évalué par l'Agent Infra · Note : <b>15.8 / 20</b> (Mention Très Bien)</p>

<h2>4.1. Analyse des Forces et Atouts Infrastructure</h2>
<ul>
  <li><b>Cluster Proxmox VE HA 2 nœuds + QDevice témoin :</b> Résolution exemplaire du quorum ($N/2 + 1 = 2$ voix sur 3) éliminant tout risque de <i>split-brain</i> en cas de perte d'un nœud. Réseau Corosync en double anneau (Ring 0 sur VLAN 903 dédié à très faible latence + Ring 1 de secours sur VLAN 902).</li>
  <li><b>Réplication ZFS en câble direct 25G DAC :</b> Liaison point-à-point dédiée 25 Gb/s sans switch (VLAN 905, MTU 9000), assurant un débit utile de 3 Go/s pour la synchronisation asynchrone des disques toutes les 5 minutes et la migration à chaud des VM sans impact sur le réseau.</li>
  <li><b>Chaîne de puissance électrique A/B secourue :</b> Deux onduleurs en ligne double conversion APC Smart-UPS SRT 6 kVA alimentant chacun une PDU métrée dédiée par baie. Présence de packs batteries externes étendant l'autonomie à **24 minutes** en cas de panne d'un onduleur portant 100% de la charge.</li>
  <li><b>Climatisation N+1, consigne 27 °C & PUE 1,34 :</b> Deux groupes froids de 7,1 kW fonctionnant en redondance N+1 avec permutation hebdomadaire. Confinement d'allée froide et consigne poussée à **27 °C** (norme ASHRAE A1), optimisant l'EER à 3,4 et assurant un PUE remarquable de 1,34. Coupure programmée du PoE Wi-Fi (103 h/semaine).</li>
  <li><b>Sauvegarde d'entreprise PBS (Proxmox Backup Server) :</b> Serveur dédié Dell R760xd2 (100 To bruts), déduplication native par blocs de 4 Mo, chiffrement AES-GCM-256 et externalisation Cloud de 20 To respectant la règle 3-2-1.</li>
</ul>

<h2>4.2. Faiblesses et Risques Techniques Identifiés</h2>
<ul>
  <li><b>Incohérence documentaire Ceph (Chiffrage) vs ZFS répliqué (L2) :</b> Le chiffrage budgète 3 serveurs Dell R660xs avec stockage Ceph (28 500 € HT), alors que l'architecture L2 modélise 2 nœuds avec ZFS répliqué en direct 25G. Cela génère un écart de 9 500 € HT non répercuté, et le matériel du témoin <code>NM-WITNESS</code> n'est pas chiffré.</li>
  <li><b>Sur-déploiement de 16 serveurs physiques mono-rôles :</b> Conserver 6 Dell R260 en DMZ et 6 Dell R360 en Datacenter pour héberger individuellement un DNS, un DHCP ou un RADIUS représente une anomalie économique (~37,8 k€ de serveurs + 6,6 k€ d'OS Windows). La virtualisation sur Proxmox aurait divisé les coûts par deux.</li>
  <li><b>RPO de 5 minutes sur incident Proxmox :</b> En cas de crash brutal du nœud maître <code>NM-PVE1</code>, les VM non redondées nativement (WLC Cisco 9800-CL et pile Docker de supervision) redémarrent sur le second nœud avec jusqu'à 5 minutes de perte de données.</li>
  <li><b>Vulnérabilités de la salle serveur au sous-sol (J05) :</b> Risque élevé d'inondation en sous-sol à Marseille sans plancher surélevé étanche ni batardeau. Absence d'extinction automatique par gaz inerte (seuls des extincteurs manuels $CO_2$ sont prévus) et absence de groupe électrogène.</li>
  <li><b>RTO Cloud prohibitif en cas de sinistre total :</b> Récupérer 20 To de sauvegardes depuis le Cloud sur le lien FTTO 1 Gb/s exige mathématiquement plus de **44 heures de téléchargement continu**, portant le délai de reprise d'activité (RTO) à plus de 72 heures.</li>
</ul>

<!-- SECTION 5 : PLAN D'ACTIONS ET RECOMMANDATIONS -->
<div class="saut"></div>
<h1>5. Plan d'Actions & Recommandations Priorisées</h1>
<p>
Afin d'élever l'infrastructure au rang de conformité maximale (standards industriels et référentiel ANSSI), les recommandations du collège d'auditeurs sont hiérarchisées en trois phases :
</p>

<h2>Priorité 1 : Immédiat / Arbitrages Critiques (Avant Soutenance)</h2>
<ol>
  <li><b>Résoudre l'itinérance Wi-Fi L3 inter-blocs :</b>
    <ul>
      <li>Configurer un groupe de mobilité FlexConnect avec ancrage centralisé pour le SSID usagers, ou élargir le scope VLAN usagers Wi-Fi à l'échelle du campus en centralisant les passerelles Wi-Fi sur le cœur CL-SW.</li>
      <li>Abaisser immédiatement la durée du bail DHCP du VLAN 115 à <b>2 heures</b> avec récupération agressive (scavenging) pour éviter la saturation du pool à 94%.</li>
    </ul>
  </li>
  <li><b>Harmoniser la documentation et le chiffrage Système :</b>
    <ul>
      <li>Ajuster le devis CAPEX pour refléter fidèlement l'architecture Proxmox 2 nœuds + QDevice ZFS (-9 500 € HT sur le 3e serveur R660xs, -1 100 €/an de souscription, et ajout d'une appliance témoin à ~1 200 € HT).</li>
    </ul>
  </li>
  <li><b>Isoler le Tier 0 Active Directory (ANSSI PA-099) :</b>
    <ul>
      <li>Extraire les contrôleurs de domaine <code>DT-AD1/2</code> du VLAN 300 pour créer un VLAN dédié Tier 0 (ex: VLAN 301), filtré par le pare-feu Stormshield avec interdiction formelle d'accès direct à Internet pour les DC.</li>
    </ul>
  </li>
  <li><b>Activer l'immuabilité des sauvegardes (ANSSI BP-100) :</b>
    <ul>
      <li>Configurer le verrouillage d'objet <b>S3 Object Lock en mode Compliance (WORM)</b> sur le stockage Cloud distant afin de prémunir les sauvegardes contre toute suppression par rançongiciel.</li>
    </ul>
  </li>
</ol>

<h2>Priorité 2 : Moyen Terme / Renforcement & Durcissement</h2>
<ol>
  <li><b>Optimiser le transit du pare-feu Stormshield SN710 :</b>
    <ul>
      <li>Raccorder directement le cluster SN710 sur les commutateurs de cœur CL-SW en agrégats 10G/40G dédiés, en supprimant le goulet d'étranglement de la pile C9200L EL-SW.</li>
      <li>Configurer une politique d'inspection asymétrique : inspection applicative L7 complète pour les flux usagers vers datacenter, et simple filtrage d'état L4 sans IPS pour les sauvegardes massives vers PBS.</li>
    </ul>
  </li>
  <li><b>Sécuriser la découverte du PMTUD & Convergence BGP :</b>
    <ul>
      <li>Autoriser explicitement les paquets ICMPv4 Type 3 Code 4 et ICMPv6 Type 2 (Packet Too Big) sur tous les pare-feux et activer <code>ip tcp adjust-mss 1460</code> pour éviter le blocage des flux en MTU 9198 vs 1500.</li>
      <li>Activer <b>BFD sur les sessions eBGP</b> avec les FAI pour ramener le temps de bascule WAN de 180 s à moins de 1,5 s en cas de panne opérateur.</li>
    </ul>
  </li>
  <li><b>Déployer une solution d'extinction propre orchestrée (NUT / PowerChute) :</b>
    <ul>
      <li>Connecter les cartes réseau de management des onduleurs au VLAN 900 et automatiser l'extinction en cascade des serveurs et VM à $T+12$ minutes de coupure secteur.</li>
    </ul>
  </li>
</ol>

<h2>Priorité 3 : Perspectives & Optimisations Futures</h2>
<ol>
  <li><b>Consolidation et Virtualisation complète de la DMZ et du Datacenter :</b>
    <ul>
      <li>Remplacer les 12 serveurs physiques 1U Dell R260 et R360 par deux clusters Proxmox VE virtualisés (gain net de 20 000 € HT de CAPEX, 12U libérés et -1 000 W constants d'électricité).</li>
    </ul>
  </li>
  <li><b>PRA inter-sites avec le campus jumeau de Digne/Gap :</b>
    <ul>
      <li>Installer un second serveur PBS sur le site de Digne via le lien WAN MPLS déjà chiffré (8 400 €/an) pour une synchronisation de datastore à datastore, éliminant la dépendance au téléchargement Cloud de 44h.</li>
    </ul>
  </li>
</ol>

<!-- SECTION 6 : PRÉPARATION SOUTENANCE ORALE -->
<div class="saut"></div>
<h1>6. Entraînement Soutenance : Questions Pièges & Défis du Jury</h1>
<p>
Cette section rassemble les <b>14 questions les plus pointues et exigeantes</b> susceptibles d'être posées par un jury d'experts (enseignants universitaires, ingénieurs réseaux CCIE, auditeurs cybersécurité ANSSI/PASSI). Chaque question est accompagnée du décryptage du piège et de la réponse argumentée attendue.
</p>

<h2>Thématique A : Architecture Réseau, Commutation & Routage L2/L3</h2>

<div class="qa-block">
  <div class="qa-q">1. Itinérance Wi-Fi et Rupture de Session L3 (FlexConnect)</div>
  <div class="qa-trap">PIÈGE JURY : Tester si vous comprenez les limites concrètes de votre découpage par bloc et de la commutation locale.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vous utilisez le mode FlexConnect en commutation locale pour vos 38 bornes Wi-Fi avec des VLANs strictement séparés par étage (VLAN 115 au RDC, VLAN 215 au 1er étage). Que se passe-t-il au niveau des couches OSI lorsqu'un utilisateur en appel Teams monte l'escalier en marchant ? Comment auriez-vous pu éviter la coupure ? »<br>
    <b>Réponse attendue :</b> Le terminal change de borne et est commuté localement sur un nouveau VLAN (115 ➔ 215). N'ayant plus la même passerelle ni le même sous-réseau, sa socket TCP/UDP liée à l'ancienne IP est brutalement rompue. Le client doit réémettre une requête DHCP. Pour garantir une mobilité sans coupure sans étendre les VLANs L2, il fallait activer l'<b>ancrage de mobilité L3 (Mobility Tunneling / Foreign-Anchor)</b> sur le contrôleur Cisco Catalyst 9800 : le trafic continue d'être encapsulé vers le sous-réseau d'origine jusqu'à la fin de la communication.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">2. Justification des 4 C9500 en Distribution vs Cœur Replié (Collapsed Core)</div>
  <div class="qa-trap">PIÈGE JURY : Vous pousser à admettre un surdimensionnement financier et électrique.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vos 4 commutateurs de distribution C9500-16X (38 000 € HT) sont physiquement dans la même baie au sous-sol que votre cœur de réseau. Pourquoi ne pas avoir fusionné Cœur et Distribution (Collapsed Core) sur 2 châssis Catalyst 9500-48Y4C ? »<br>
    <b>Réponse attendue :</b> Assumer que le réseau à trois couches a été retenu pour respecter scrupuleusement l'exigence formelle du cahier des charges client et pour confiner strictement les domaines de diffusion et de panne (blast radius). Cependant, prouver au jury que la variante <i>Collapsed Core</i> a été étudiée et chiffrée : elle aurait permis d'économiser 38 k€ HT, environ 640 W constants et de supprimer 4 instances OSPFv3, constituant l'optimisation industrielle naturelle du projet.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">3. Goulot d'Étranglement Inter-VRF et Matrice de Commutation</div>
  <div class="qa-trap">PIÈGE JURY : Vérifier que vous connaissez le chemin physique complet d'une trame inter-VRF.</div>
  <div class="qa-exp">
    <b>Question :</b> « Un étudiant (VLAN 111, VRF USR) transfère un fichier de 10 Go depuis le serveur de fichiers (VLAN 300, VRF SRV). Quel est le trajet exact de la trame Ethernet et quels composants matériels risquent de saturer ? »<br>
    <b>Réponse attendue :</b> Poste ➔ AL-SW ➔ DL-B1 (routage vers sous-interface Po101.10) ➔ CL-SW en VRF USR ➔ trunk Po4 ➔ pile C9200L EL-SW ➔ port 10G du Stormshield SN710 (inspection L4-L7) ➔ réinjection en VRF SRV via VLAN 1040 vers EL-SW ➔ CL-SW ➔ pile DT-SW ➔ Serveur. Les goulots sont : le CPU du Stormshield SN710 qui plafonne à 2,5 Gbps en inspection UTM, et les tampons mémoire très limités (6 Mo) des switchs C9200L EL-SW. Solution : raccorder le pare-feu directement sur le cœur et réaliser du <i>Route-Target Leaking</i> direct sur le cœur avec ACLs TCAM pour les transferts lourds autorisés.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">4. Asymétrie BGP et Défaillance de Session Multi-Opérateur</div>
  <div class="qa-trap">PIÈGE JURY : Tester vos connaissances sur l'algorithme de décision BGP et les pare-feux à état.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vous annoncez votre /24 public avec un AS-path prepending ×3 sur le FAI 2. Pourquoi cela ne garantit-il pas que le trafic retour ne rentrera pas par le FAI 2 ? Quel impact sur le pare-feu FortiGate ? »<br>
    <b>Réponse attendue :</b> L'attribut BGP <code>Local-Preference</code> prime toujours sur l'AS-Path. Si un opérateur sur Internet préfère ses liaisons avec le FAI 2, il ignorera le prepending et routera le retour par le FAI 2. Si le trafic sort par FAI 1 (SD-WAN FortiGate) et revient par FAI 2, le FortiGate en mode inspection d'état (stateful) rejettera le paquet retour car il ne correspond à aucune session ouverte sur cette interface WAN. Il est impératif d'activer <code>set asymroute enable</code> ou de synchroniser les tables d'état.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">5. Fonctionnement du NPTv6 (RFC 6296) vs NAT44 classique</div>
  <div class="qa-trap">PIÈGE JURY : Vérifier que vous ne confondez pas translation IPv6 sans état et PAT IPv4.</div>
  <div class="qa-exp">
    <b>Question :</b> « Pourquoi ne pouvez-vous pas annoncer votre /52 IPv6 au FAI 2 en BGP ? Expliquez le fonctionnement du NPTv6 sur le FortiGate et en quoi il diffère d'un NAT44. »<br>
    <b>Réponse attendue :</b> Le préfixe /52 est un préfixe PA (Provider-Aggregatable) appartenant à l'AMU ; les filtres RPKI mondiaux et la politique DFZ refusent d'agréger ou de router un sous-bloc PA via un AS tiers non propriétaire. Le <b>NPTv6</b> est une translation de préfixe sans état (stateless) 1:1 au niveau des 64 premiers bits du préfixe. Les 64 bits de l'hôte (Interface ID) restent strictement inchangés. Il n'y a aucune table de translation de ports en mémoire, la transparence de bout en bout est préservée et la somme de contrôle TCP/UDP est conservée par compensation mathématique dans le préfixe.
  </div>
</div>

<div class="saut"></div>
<h2>Thématique B : Cybersécurité, Conformité ANSSI & Filtrage</h2>

<div class="qa-block">
  <div class="qa-q">6. Dimensionnement UTM Stormshield SN710 vs Débit 10G/40G</div>
  <div class="qa-trap">PIÈGE JURY : Mettre en évidence un décalage entre les besoins de débit campus et les capacités UTM.</div>
  <div class="qa-exp">
    <b>Question :</b> « Le SN710 plafonne à ~2,5 Gbps en inspection UTM complète. Vos liens de cœur commutent à 10 et 40 Gbps. Comment évitez-vous qu'une sauvegarde nocturne ou une tempête de trafic ne paralyse le pare-feu ? »<br>
    <b>Réponse attendue :</b> Il est impératif de calibrer la politique de filtrage : les flux sensibles usagers vers serveurs sont soumis à l'inspection applicative et IPS complète, tandis que les flux massifs de confiance (sauvegardes PBS, flux vidéo caméras vers NVR) ne font l'objet que d'un filtrage d'état L4 haute performance sans passer par le moteur lourd d'inspection de contenu, ou de monter sur la gamme SN910.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">7. Angle Mort SSL/TLS et Détection des Menaces Chiffrées</div>
  <div class="qa-trap">PIÈGE JURY : Pointer du doigt l'inefficacité des antivirus et IPS périmétriques sur les flux modernes.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vos flux usagers sortent en HTTPS direct vers Internet. Sachant que 90% des malwares et canaux C2 utilisent TLS 1.3 chiffré, comment votre passerelle détecte-t-elle une exfiltration sans inspection SSL/TLS ? »<br>
    <b>Réponse attendue :</b> Sans inspection SSL Man-in-the-Middle, la passerelle ne peut inspecter le payload chiffré ; elle est réduite au filtrage DNS et SNI (qui devient lui-même chiffré avec ECH). Pour y remédier, il faut déployer une autorité de certification d'entreprise sur les postes du domaine pour déchiffrer le trafic sur le FortiGate, en définissant une liste d'exclusion stricte conforme au RGPD (banques, santé, services publics).
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">8. Modèle de Tiering Active Directory (ANSSI PA-099) et Faiblesse du VLAN 300</div>
  <div class="qa-trap">PIÈGE JURY : Vous coincer sur la ségrégation des privilèges au sein du Datacenter.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vos contrôleurs de domaine DT-AD1/2 sont dans le même VLAN 300 que les serveurs DHCP et d'infrastructure. Pourquoi cela enfreint-il le guide ANSSI PA-099 et quel est le risque d'attaque ? »<br>
    <b>Réponse attendue :</b> Le guide impose une étanchéité stricte entre le Tier 0 (Contrôleurs de domaine), le Tier 1 (Serveurs d'applications) et le Tier 2 (Postes usagers). Partager le même domaine de broadcast permet à un attaquant ayant compromis un serveur applicatif d'écouter les trames L2, de tenter des attaques NTLM relay ou d'exploiter des failles de coercition RPC (PetitPotam). Solution : déplacer immédiatement les DC dans un VLAN dédié Tier 0 filtré par pare-feu.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">9. Résilience aux Rançongiciels et Immuabilité des Sauvegardes (ANSSI BP-100)</div>
  <div class="qa-trap">PIÈGE JURY : Vérifier que vous avez anticipé le scénario du chiffrement total du SI.</div>
  <div class="qa-exp">
    <b>Question :</b> « Si un ransomware compromet le compte administrateur du domaine, comment empêchez-vous l'attaquant d'effacer vos sauvegardes locales sur DT-BKP1 et distantes sur le Cloud ? »<br>
    <b>Réponse attendue :</b> Le serveur PBS ne doit jamais être joint au domaine Active Directory et doit posséder des identifiants d'administration locaux uniques. Côté Cloud, il faut activer le mode <b>S3 Object Lock en mode Compliance (WORM)</b> : les blocs de données sont mathématiquement verrouillés contre toute suppression ou modification pendant une durée incompressible (ex: 60 jours), même avec les privilèges root du compte Cloud.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">10. Faiblesse de l'Authentification MAB sur les Caméras et Badgeuses IoT</div>
  <div class="qa-trap">PIÈGE JURY : Démontrer qu'une adresse MAC n'est pas un mécanisme de sécurité.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vos caméras et badgeuses utilisent le contrôle d'accès MAB avec port-security 1 MAC. Qu'est-ce qui empêche un attaquant de débrancher une caméra dans un couloir pour cloner sa MAC et pénétrer sur le réseau ? »<br>
    <b>Réponse attendue :</b> Rien ne l'empêche au niveau L2 pur puisque l'adresse MAC se lit en clair et se clone en une commande. Pour contrer cette faille, il faut : soit migrer vers du <b>802.1X EAP-TLS avec certificat machine</b> sur les équipements qui le supportent, soit appliquer sur le port du switch une <b>ACL L4 stricte</b> autorisant uniquement les flux HTTPS/RTSP vers l'adresse IP unique du serveur d'enregistrement, avec extinction immédiate du port sur toute tentative de scan ou paquet divergent.
  </div>
</div>

<div class="saut"></div>
<h2>Thématique C : Infrastructure Physique, Virtualisation & Continuité</h2>

<div class="qa-block">
  <div class="qa-q">11. Quorum Corosync, QDevice et Arbitrage Split-Brain sous Proxmox VE</div>
  <div class="qa-trap">PIÈGE JURY : Tester votre maîtrise fine des mécanismes de consensus distribué.</div>
  <div class="qa-exp">
    <b>Question :</b> « Dans votre cluster Proxmox à 2 nœuds, une coupure réseau isole NM-PVE1 de NM-PVE2. Comment le QDevice empêche-t-il le split-brain ? Que se passe-t-il si le QDevice lui-même tombe en panne ? »<br>
    <b>Réponse attendue :</b> Chaque nœud PVE possède 1 vote et le QDevice externe 1 vote (Total = 3 votes, majorité absolue requise = 2). En cas d'isolement entre les deux nœuds, le premier nœud parvenant à joindre le QDevice obtient 2 votes sur 3 : il conserve le quorum et maintient ses VM. Le second nœud isolé n'a qu'1 vote sur 3 : il perd le quorum et suspend ses opérations HA (fencing). Si le QDevice tombe seul en panne, le cluster conserve 2 votes sur 3 vivants ($2/3 \ge 2$), ce qui garantit le fonctionnement normal ininterrompu du cluster.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">12. RPO ZFS Asynchrone vs Ceph et Résilience des VM de Gestion</div>
  <div class="qa-trap">PIÈGE JURY : Vous faire expliciter les compromis entre stockage partagé et réplication locale.</div>
  <div class="qa-exp">
    <b>Question :</b> « Votre réplication ZFS sur DAC 25G s'exécute toutes les 5 minutes. Quel est l'impact concret sur le RPO et le RTO du contrôleur Wi-Fi 9800-CL et de la supervision lors d'un crash de la carte mère de NM-PVE1 ? Pourquoi avoir abandonné Ceph ? »<br>
    <b>Réponse attendue :</b> Le RPO est de 5 minutes (perte maximale des 5 dernières minutes de métriques et journaux de supervision). Le RTO est d'environ 3 minutes (temps de détection de panne, fencing et boot de la VM sur le second nœud). Pour le WLC Wi-Fi, les bornes en FlexConnect continuent de commuter le trafic local sans coupure pour les usagers déjà connectés. Ceph a été écarté car un cluster Ceph résilient exige au minimum 3 nœuds (surcoût matériel de 9 500 € HT) et des réseaux dédiés Ceph Public / Ceph Cluster à très haute performance.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">13. Cinématique d'Arrêt Électrique en Cascade (Sans Groupe Électrogène)</div>
  <div class="qa-trap">PIÈGE JURY : Vérifier que vous avez pensé au scénario réel d'une coupure électrique prolongée.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vos batteries offrent 24 minutes d'autonomie à pleine charge. Vous n'avez pas de groupe électrogène. Décrivez la séquence exacte d'extinction ordonnée de la salle serveur lors d'une panne Enedis. »<br>
    <b>Réponse attendue :</b> Orchestration via le protocole NUT ou APC PowerChute raccordé aux cartes NMC des onduleurs. Après une temporisation de sécurité de 5 min (élimination des micro-coupures) : à $T+10$ min, arrêt gracieux des conteneurs et VM non critiques (Docker supervision, web) ; à $T+15$ min, arrêt des VM d'infrastructure et des hôtes Proxmox ; à $T+18$ min, arrêt ordonné des 16 serveurs physiques Windows et du stockage PBS ; les commutateurs de cœur et de distribution sont éteints en dernier à $T+22$ min. Au retour du secteur, maintien de l'extinction jusqu'à ce que les batteries atteignent 40% de charge pour prévenir tout crash sur coupure immédiate en rebond.
  </div>
</div>

<div class="qa-block">
  <div class="qa-q">14. Consigne Thermique à 27 °C, Norme ASHRAE A1 et Hygrométrie au Sous-Sol</div>
  <div class="qa-trap">PIÈGE JURY : Vérifier votre culture Green IT et physique des datacenters.</div>
  <div class="qa-exp">
    <b>Question :</b> « Vous poussez la consigne de climatisation à 27 °C pour obtenir un PUE de 1,34. Quel impact cela a-t-il sur les serveurs, sur la compensation énergétique et sur la gestion de l'humidité au sous-sol ? »<br>
    <b>Réponse attendue :</b> Selon la norme ASHRAE A1 (plage recommandée jusqu'à 27 °C), élever la température d'allée froide améliore directement le coefficient d'efficacité énergétique de la climatisation (EER passe de 3,0 à 3,4, soit 10% d'économie sur le compresseur). La contrepartie est que les ventilateurs internes des serveurs Dell tournent plus vite (courbe PWM de l'iDRAC), consommant légèrement plus d'électricité (effet de compensation thermique). Enfin, au sous-sol, il est crucial de réguler l'humidité relative entre 40% et 60% pour éviter l'électricité statique (air trop sec) et la condensation sur les composants métalliques (air trop humide lors des épisodes marseillais).
  </div>
</div>

<div style="margin-top: 10mm; text-align: center; font-size: 8pt; color: #64748B; border-top: 1px solid #CBD5E1; padding-top: 3mm;">
  Rapport d'audit multi-agents généré automatiquement · RudyLink Infrastructure · Campus Universitaire de Marseille-Luminy
</div>

</body>
</html>
"""

def main():
    print("1. Écriture du fichier HTML source...")
    HTML_OUT.write_text(HTML_CONTENT, encoding="utf-8")
    print(f"   -> Fichier généré : {HTML_OUT}")

    print("2. Détection du moteur de rendu Chromium/Chrome...")
    chrome_bin = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome_bin:
        print("   ERREUR : Aucun binaire Chrome/Chromium détecté.")
        return 1

    print(f"   -> Utilisation de : {chrome_bin}")
    print("3. Compilation du rapport PDF en mode headless...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        cmd = [
            chrome_bin,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            f"--user-data-dir={tmp_dir}",
            "--no-pdf-header-footer",
            f"--print-to-pdf={PDF_OUT}",
            HTML_OUT.as_uri()
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            print(f"   ERREUR lors de la génération PDF : {res.stderr}")
            return res.returncode

    print(f"   -> PDF généré avec succès : {PDF_OUT}")
    print(f"   -> Taille : {PDF_OUT.stat().st_size} octets")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
