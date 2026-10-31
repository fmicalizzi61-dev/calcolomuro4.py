import json
import math
import ssl
import urllib.request
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Configurazione della pagina Streamlit
st.set_page_config(
    page_title="Muro C.A. NTC 2018 - Genio Civile",
    page_icon="🧱",
    layout="wide",
)

st.title(
    "🧱 Progetto Esecutivo Muro in C.A. (Tab. 08 & 09 Complete - NTC 2018)"
)
st.write(
    "Calcolo ufficiale geotecnico e strutturale (Approccio 2 - M2+R2) con"
    " pre-dimensionamento armature ed elaborato grafico."
)

# --- SEZIONE INPUT UTENTE (Sidebar per Desktop / Sottomenu per iPhone) ---
st.sidebar.header("⚙️ Dati di Progetto & Localizzazione")

with st.sidebar.expander("📍 Localizzazione & Sisma", expanded=True):
  lat_val = st.number_input(
      "Latitudine (deg)", value=38.1157, format="%.4f", step=0.0001
  )
  lon_val = st.number_input(
      "Longitudine (deg)", value=15.5534, format="%.4f", step=0.0001
  )
  St = st.number_input(
      "Coeff. topografico St", value=1.20, step=0.05, format="%.2f"
  )
  beta_deg = st.number_input(
      "Inclinazione terrapieno β (°)", value=0.0, step=0.5
  )

with st.sidebar.expander("📐 Geometria Muro", expanded=False):
  H = st.number_input("Altezza totale H (m)", value=5.00, step=0.10)
  B = st.number_input("Larghezza fondazione B (m)", value=3.60, step=0.10)
  t_piede = st.number_input("Mensola di piede (m)", value=1.10, step=0.10)
  s_testa = st.number_input("Spessore testa paramento (m)", value=0.40, step=0.05)
  s_base = st.number_input("Spessore base paramento (m)", value=0.60, step=0.05)
  s_fond = st.number_input("Spessore suola/fondazione (m)", value=0.60, step=0.05)

with st.sidebar.expander("🧱 Materiali", expanded=False):
  Rck = st.number_input("Resistenza cubica Rck (N/mm²)", value=30.0, step=5.0)
  fyk = st.number_input("Tensione snervamento fyk (N/mm²)", value=450.0, step=10.0)
  gamma_cls = st.number_input("Peso spec. cls (kN/m³)", value=25.0, step=0.5)

with st.sidebar.expander("🌱 Terreno & Sovraccarico", expanded=False):
  gamma_t = st.number_input("Peso terreno γ (kN/m³)", value=18.0, step=0.5)
  phi_deg = st.number_input("Attrito interno φ' (°)", value=30.0, step=0.5)
  delta_deg = st.number_input("Attrito terra-muro δ (°)", value=20.0, step=0.5)
  c = st.number_input("Coesione c' (kPa)", value=0.0, step=0.5)
  q = st.number_input("Sovraccarico q (kN/m²)", value=10.0, step=1.0)
  q_amm = st.number_input(
      "Tensione ammissibile q_amm (kPa)", value=300.0, step=10.0
  )


# --- FUNZIONI DI SUPPORTO ---
def ottieni_localita_online(lat, lon):
  url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
  req = urllib.request.Request(
      url, headers={"User-Agent": "MuroCalculatorNTC/1.0"}
  )
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  try:
    with urllib.request.urlopen(req, context=ctx, timeout=3) as response:
      data = json.loads(response.read().decode())
      if "display_name" in data:
        return data["display_name"]
  except Exception:
    pass
  return f"Lat: {lat:.4f}, Lon: {lon:.4f}"


def seleziona_armatura(As_richiesto):
  diametri_test = [12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
  interassi_test = [10, 12.5, 15, 20, 25]
  migliore_phi, migliore_passo, min_diff = 16, 20, 999999.0
  for phi in diametri_test:
    area_singola = math.pi * ((phi / 10.0) ** 2) / 4.0
    for passo in interassi_test:
      As_off = area_singola * (100.0 / passo)
      if As_off >= As_richiesto and (As_off - As_richiesto) < min_diff:
        min_diff = As_off - As_richiesto
        migliore_phi, migliore_passo = phi, int(passo)
  As_eff = (math.pi * ((migliore_phi / 10.0) ** 2) / 4.0) * (
      100.0 / migliore_passo
  )
  return migliore_phi, migliore_passo, As_eff


def disegna_sezione_matplotlib(
    H,
    B,
    t_piede,
    s_testa,
    s_base,
    s_fond,
    p_par,
    pas_par,
    p_comp,
    pas_comp,
    p_tac,
    pas_tac,
    p_pie,
    pas_pie,
    p_rip,
    pas_rip,
):
  t_tacco = B - t_piede - s_base
  fig, ax = plt.subplots(figsize=(6, 9))

  poly_fond = [(0, 0), (B, 0), (B, s_fond), (0, s_fond)]
  poly_par = [
      (t_piede, s_fond),
      (t_piede + s_base, s_fond),
      (t_piede + s_base, H),
      (t_piede + s_base - s_testa, H),
  ]

  ax.add_patch(
      plt.Polygon(
          poly_fond,
          closed=True,
          facecolor="#e9ecef",
          edgecolor="black",
          lw=1.5,
          label="Fondazione",
      )
  )
  ax.add_patch(
      plt.Polygon(
          poly_par,
          closed=True,
          facecolor="#dee2e6",
          edgecolor="black",
          lw=1.5,
          label="Paramento",
      )
  )

  ax.fill_between(
      [t_piede + s_base, B + 1],
      [s_fond, s_fond],
      [H, H],
      color="#f8f9fa",
      hatch="//",
      edgecolor="#adb5bd",
      alpha=0.5,
  )

  cp = 0.05
  ax.plot(
      [t_piede + s_base - cp, t_piede + s_base - cp],
      [s_fond + cp, H - cp],
      color="red",
      lw=2.5,
      label=f"Paramento Teso (Φ{p_par}/{pas_par}cm)",
  )
  ax.plot(
      [t_piede + cp, t_piede + s_base - s_testa + cp],
      [s_fond + cp, H - cp],
      color="blue",
      lw=1.8,
      label=f"Paramento Compresso (Φ{p_comp}/{pas_comp}cm)",
  )
  ax.plot(
      [t_piede + s_base, B - cp],
      [s_fond - cp, s_fond - cp],
      color="red",
      lw=2.5,
      label=f"Tacco (Φ{p_tac}/{pas_tac}cm)",
  )
  ax.plot(
      [cp, t_piede],
      [cp, cp],
      color="red",
      lw=2.5,
      label=f"Piede (Φ{p_pie}/{pas_pie}cm)",
  )

  ax.set_aspect("equal")
  ax.set_xlim(-0.5, B + 1.2)
  ax.set_ylim(-0.5, H + 0.5)
  ax.set_title(
      "Sezione Esecutiva e Disposizione Armature", fontsize=10, fontweight="bold"
  )
  ax.grid(True, linestyle=":", alpha=0.6)
  ax.legend(loc="upper left", fontsize=7)

  return fig


# --- ESECUZIONE DEL CALCOLO ---
sit_str = ottieni_localita_online(lat_val, lon_val)

ag_slo, ag_sld, ag_slv, ag_slc = 0.055, 0.078, 0.235, 0.315
f0_slo, f0_sld, f0_slv, f0_slc = 2.414, 2.371, 2.440, 2.467
tc_slo, tc_sld, tc_slv, tc_slc = 0.274, 0.291, 0.351, 0.376
ss_slo, ss_sld, ss_slv, ss_slc = 1.200, 1.200, 1.170, 1.080

ag_max = ss_slv * St * ag_slv

gamma_phi = 1.2
phi_k = math.radians(phi_deg)
phi_d = math.atan(math.tan(phi_k) / gamma_phi)
delta_k = math.radians(delta_deg)
delta_d = math.atan(math.tan(delta_k) / gamma_phi)

gamma_G2 = 1.3
gamma_G_terreno = 1.0
gamma_Q = 1.3
beta = math.radians(beta_deg)
fyd = fyk / 1.15
gamma_F = 1.3

t_tacco = B - t_piede - s_base
H_terreno = H - s_fond

beta_s = 0.28
kh = beta_s * ag_max
kv = 0.5 * kh
theta = math.atan(kh / (1.0 - kv))

num_arg = math.sin(phi_d + delta_d) * math.sin(phi_d - beta - theta)
den_arg = math.cos(delta_d + beta) * math.cos(theta)
sq_term = math.sqrt(max(0.0, num_arg / den_arg))
Kae = (math.cos(phi_d - theta) ** 2) / (
    (math.cos(theta) ** 2)
    * math.cos(delta_d)
    * (1.0 + sq_term * math.sin(phi_d + delta_d + beta)) ** 2
)

E_terreno = 0.5 * gamma_t * (H**2) * Kae * (1.0 - kv) * gamma_G_terreno
E_q = q * H * Kae * gamma_Q
E_tot = E_terreno + E_q
braccio_E = ((0.5 * gamma_t * (H**2) * (H / 3.0)) + (q * H * (H / 2.0))) / E_tot
M_rib = E_tot * braccio_E

area_par = ((s_testa + s_base) / 2.0) * H_terreno
W_par = area_par * gamma_cls
bar_par = t_piede + s_base - (s_base - s_testa) / 3.0
W_fond = B * s_fond * gamma_cls
bar_fond = B / 2.0
W_terr = t_tacco * H_terreno * gamma_t
bar_terr = t_piede + s_base + (t_tacco / 2.0)
W_q_tacco = t_tacco * q

M_stab = (
    (W_par * gamma_G2 * bar_par)
    + (W_fond * gamma_G2 * bar_fond)
    + ((W_terr * gamma_G2 + W_q_tacco * gamma_Q) * bar_terr)
)

R_rib = M_stab / M_rib if M_rib > 0 else 999.0

N_ed = (
    W_par * gamma_G2 + W_fond * gamma_G2 + W_terr * gamma_G2 + W_q_tacco * gamma_Q
) * (1.0 - kv)
F_orizz = E_tot + (N_ed * kh)
gamma_R_scor = 1.1
R_scor = (N_ed * math.tan(phi_d)) / gamma_R_scor
rapporto_scor = R_scor / F_orizz if F_orizz > 0 else 999.0

x_0 = (M_stab - M_rib) / N_ed if N_ed > 0 else 0.0
e = (B / 2.0) - x_0
if abs(e) <= (B / 6.0):
  sigma_1 = (N_ed / B) * (1.0 + (6.0 * e / B))
  sigma_2 = (N_ed / B) * (1.0 - (6.0 * e / B))
  q_max, q_min = max(sigma_1, sigma_2), min(sigma_1, sigma_2)
else:
  q_max = (2.0 * N_ed) / (3.0 * x_0) if x_0 > 0 else 999.0
  q_min = 0.0

gamma_R_portanza = 1.4
q_lim_progetto = q_amm / gamma_R_portanza
verificata_portanza = q_max <= q_lim_progetto

# Calcolo Armature
M_ed_par = E_tot * (H / 3.0) * gamma_F
d_par = s_base - 0.05
As_par_req = ((M_ed_par * 1000.0) / (0.9 * (d_par * 100.0) * (fyd / 10.0))) * 10.0
phi_par, passo_par, As_par_eff = seleziona_armatura(As_par_req)

As_comp_req = max(As_par_eff * 0.3, 4.0)
phi_comp, passo_comp, As_comp_eff = seleziona_armatura(As_comp_req)

q_tacco_1 = (
    q_max if x_0 > B - t_tacco else q_min + (q_max - q_min) * (t_tacco / B)
)
p_netto_tacco_medio = ((q_tacco_1 + q_max) / 2.0) - (
    s_fond * gamma_cls + H_terreno * gamma_t + q
)
M_ed_tacco = abs(p_netto_tacco_medio) * (t_tacco**2) / 2.0 * gamma_F
d_fond = s_fond - 0.05
As_tacco_req = (
    (M_ed_tacco * 1000.0) / (0.9 * (d_fond * 100.0) * (fyd / 10.0))
) * 10.0
phi_tac, passo_tac, As_tac_eff = seleziona_armatura(As_tacco_req)

q_piede_2 = (
    q_max - (q_max - q_min) * (t_piede / B) if abs(e) <= B / 6.0 else q_max
)
p_netto_piede_medio = ((q_max + q_piede_2) / 2.0) - (s_fond * gamma_cls)
M_ed_piede = abs(p_netto_piede_medio) * (t_piede**2) / 2.0 * gamma_F
As_piede_req = (
    (M_ed_piede * 1000.0) / (0.9 * (d_fond * 100.0) * (fyd / 10.0))
) * 10.0
phi_pie, passo_pie, As_pie_eff = seleziona_armatura(As_piede_req)

As_rip = max(As_par_eff * 0.25, 3.5)
phi_rip, passo_rip, _ = seleziona_armatura(As_rip)

# --- VISUALIZZAZIONE RISULTATI ---
col1, col2 = st.columns([1.1, 0.9])

with col1:
  st.subheader("📋 Esito Verifiche SLU (NTC 2018)")

  m1, m2, m3 = st.columns(3)
  m1.metric(
      "Ribaltamento (Rd/Ed)",
      f"{R_rib:.2f}",
      "OK" if R_rib >= 1.0 else "NON OK",
      delta_color="normal" if R_rib >= 1.0 else "inverse",
  )
  m2.metric(
      "Scorrimento (Rd/Ed)",
      f"{rapporto_scor:.2f}",
      "OK" if rapporto_scor >= 1.0 else "NON OK",
      delta_color="normal" if rapporto_scor >= 1.0 else "inverse",
  )
  m3.metric(
      "Tensione Suolo (kPa)",
      f"{q_max:.1f}",
      f"Amms: {q_lim_progetto:.1f}",
      delta_color="normal"
      if verificata_portanza and abs(e) <= B / 6
      else "inverse",
  )

  st.write("**Tabella 08 - Parametri Sismici di Base**")
  df_tab8 = pd.DataFrame({
      "Stato Limite": ["SLO", "SLD", "SLV", "SLC"],
      "Tr [anni]": [45, 50, 475, 975],
      "ag [g]": [ag_slo, ag_sld, ag_slv, ag_slc],
      "ST": [St, St, St, St],
      "F0*": [f0_slo, f0_sld, f0_slv, f0_slc],
      "Tc* [s]": [tc_slo, tc_sld, tc_slv, tc_slc],
  })
  st.dataframe(df_tab8, use_container_width=True, hide_index=True)

  st.write("**Armature Esecutive Calcolate**")
  df_arm = pd.DataFrame({
      "Elemento": [
          "Paramento Teso (Monte)",
          "Paramento Compresso (Valle)",
          "Mensola Tacco",
          "Mensola Piede",
          "Ripartitori Longitudinali",
      ],
      "Diametro": [
          f"Φ{phi_par}",
          f"Φ{phi_comp}",
          f"Φ{phi_tac}",
          f"Φ{phi_pie}",
          f"Φ{phi_rip}",
      ],
      "Passo": [
          f"{passo_par} cm",
          f"{passo_comp} cm",
          f"{passo_tac} cm",
          f"{passo_pie} cm",
          f"{passo_rip} cm",
      ],
      "As Effettiva": [
          f"{As_par_eff:.2f} cm²/m",
          f"{As_comp_eff:.2f} cm²/m",
          f"{As_tac_eff:.2f} cm²/m",
          f"{As_pie_eff:.2f} cm²/m",
          "-",
      ],
  })
  st.dataframe(df_arm, use_container_width=True, hide_index=True)

with col2:
  st.subheader("📐 Grafico Sezione Esecutiva")
  fig_muro = disegna_sezione_matplotlib(
      H,
      B,
      t_piede,
      s_testa,
      s_base,
      s_fond,
      phi_par,
      passo_par,
      phi_comp,
      passo_comp,
      phi_tac,
      passo_tac,
      phi_pie,
      passo_pie,
      phi_rip,
      passo_rip,
  )
  st.pyplot(fig_muro)

# --- DEFINIZIONE VARIABILI TESTUALI PER LA RELAZIONE (RISOLUZIONE ERRORE SINTASSI) ---
res_rib = "VERIFICATO" if R_rib >= 1.0 else "NON VERIFICATO"
res_scor = "VERIFICATO" if rapporto_scor >= 1.0 else "NON VERIFICATO"
res_port = (
    "VERIFICATO" if verificata_portanza and abs(e) <= B / 6 else "NON VERIFICATO"
)

report_text = f"""========================================================================================
   RELAZIONE DI CALCOLO NTC 2018 (APPROCCIO 2: M2 + R2)
   Verifiche SLU Geotecniche e Strutturali & Tabelle Sismiche Ufficiali
   Ubicazione Opera: {sit_str} [Lat: {lat_val:.4f}, Lon: {lon_val:.4f}]
========================================================================================

TAB. 08 - VALORI DEI PARAMETRI SISMICI DI BASE (DB INGV / NTC 2018):
--------------------------------------------------------------------
 Stati Limite |  Tr (anni) |   ag (g)   |   ST   |   F0*  |   Tc* (s) |
--------------------------------------------------------------------
     SLO      |     45     |   {ag_slo:.3f}    |  {St:.2f}  |  {f0_slo:.3f} |   {tc_slo:.3f}   |
     SLD      |     50     |   {ag_sld:.3f}    |  {St:.2f}  |  {f0_sld:.3f} |   {tc_sld:.3f}   |
     SLV      |    475     |   {ag_slv:.3f}    |  {St:.2f}  |  {f0_slv:.3f} |   {tc_slv:.3f}   |
     SLC      |    975     |   {ag_slc:.3f}    |  {St:.2f}  |  {f0_slc:.3f} |   {tc_slc:.3f}   |
--------------------------------------------------------------------

1. DATI GEOMETRICI E PARAMETRI DI PROGETTO (SLU):
 - H = {H} m | B = {B} m | Piede = {t_piede} m | Tacco = {t_tacco:.2f} m
 - Spessore testa = {s_testa} m | Spessore base = {s_base} m | Spessore fondazione = {s_fond} m
 - Rck = {Rck} N/mm2 | fyk = {fyk} N/mm2 | Gamma cls = {gamma_cls} kN/m3
 - Terreno caratteristico: gamma = {gamma_t} kN/m3, phi'k = {phi_deg}°
 - Terreno di progetto (M2, gamma_phi={gamma_phi}): phi'_d = {math.degrees(phi_d):.2f}° | tan(phi'_d) = {math.tan(phi_d):.4f}

2. VERIFICHE GEOTECNICHE SLU (NTC 2018 - Rd / Ed >= 1.0):
 - Spinta sismica di progetto (Mononobe-Okabe): E_tot = {E_tot:.2f} kN/m
 - Ribaltamento (Rd/Ed = M_stab / M_rib): {R_rib:.2f} >= 1.00 --> {res_rib}
 - Scorrimento (Rd/Ed = R_scor / F_orizz): {rapporto_scor:.2f} >= 1.00 (F_orizz={F_orizz:.2f} kN, R_scor={R_scor:.2f} kN) --> {res_scor}
 - Portanza (q_max <= q_lim_d): q_max = {q_max:.2f} kPa <= {q_lim_progetto:.2f} kPa (Ecc. e = {e:.3f}m) --> {res_port}

3. PROGETTO ESECUTIVO DELLE ARMATURE COMPLETE (SLU STR):
 - Paramento Teso (Dorso Monte):     PHI {phi_par} / {passo_par} cm (As_eff = {As_par_eff:.2f} cm2/m)
 - Paramento Compresso (Fronte Valle): PHI {phi_comp} / {passo_comp} cm
 - Ferri Ripartitori Longitudinali:    PHI {phi_rip} / {passo_rip} cm
 - Mensola di Tacco (Dorso Fondaz.):   PHI {phi_tac} / {passo_tac} cm
 - Mensola di Piede (Estrad. Fondaz.): PHI {phi_pie} / {passo_pie} cm
========================================================================================
"""

st.download_button(
    label="📥 Scarica Relazione Ufficiale (.txt)",
    data=report_text,
    file_name=f"Relazione_NTC2018_Lat_{lat_val:.4f}_Lon_{lon_val:.4f}.txt",
    mime="text/plain",
    type="primary",
)