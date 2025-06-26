import streamlit as st
import pickle
import os
import random
from datetime import datetime, timedelta

# --------------------------
# KONSTANTE I POMOĆNE FUNKCIJE
# --------------------------

DAYS = ['Ponedjeljak', 'Utorak', 'Srijeda', 'Cetvrtak', 'Petak', 'Subota', 'Nedjelja']

PLAN_FILE = "plan_obroka.pkl"
BAZA_FILE = "baza_obroka.pkl"
POVIJEST_FILE = "povijest_planova.pkl"

def init_plan():
    return {day: {"rucak": None, "vecera": None} for day in DAYS}

def load_pickle(file, default):
    if os.path.exists(file):
        with open(file, "rb") as f:
            return pickle.load(f)
    return default

def save_pickle(data, file):
    with open(file, "wb") as f:
        pickle.dump(data, f)

def dodaj_u_bazu(obrok):
    baza = load_pickle(BAZA_FILE, [])
    baza.append(obrok)
    save_pickle(baza, BAZA_FILE)

def generiraj_tjedni_plan():
    baza = load_pickle(BAZA_FILE, [])
    baza_za_rucak = [m for m in baza if not m.get("samo_vecera", False)]
    baza_za_veceru = baza

    if len(baza_za_rucak) < len(DAYS) or len(baza_za_veceru) < len(DAYS):
        st.warning("Nema dovoljno jela u bazi za generiranje plana bez ponavljanja.")
        return None

    rucak_izbor = random.sample(baza_za_rucak, len(DAYS))
    vecera_izbor = random.sample(baza_za_veceru, len(DAYS))

    plan = {}
    for i, day in enumerate(DAYS):
        plan[day] = {
            "rucak": rucak_izbor[i],
            "vecera": vecera_izbor[i]
        }
    return plan

def spremi_u_povijest(plan):
    povijest = load_pickle(POVIJEST_FILE, [])
    danas = datetime.now().date()
    povijest.append({"datum": danas, "plan": plan})
    granica = danas - timedelta(days=14)
    povijest = [p for p in povijest if p["datum"] >= granica]
    save_pickle(povijest, POVIJEST_FILE)

def prikazi_povijest():
    povijest = load_pickle(POVIJEST_FILE, [])
    if not povijest:
        st.info("Nema zapisa u povijesti.")
        return
    st.header("\U0001F4D6 Povijest planova (zadnja 2 tjedna)")
    for zapis in sorted(povijest, key=lambda x: x["datum"], reverse=True):
        st.subheader(str(zapis["datum"]))
        for day in DAYS:
            st.markdown(f"**{day}:**")
            dnevni = zapis["plan"].get(day, {})
            for vrsta in ["rucak", "vecera"]:
                obrok = dnevni.get(vrsta)
                if obrok:
                    st.write(f"- {vrsta.capitalize()}: {obrok['naziv']}")
                else:
                    st.write(f"- {vrsta.capitalize()}: Nema obroka")

# --------------------------
# UI - APLIKACIJA
# --------------------------

st.set_page_config(page_title="Planer Obroka", layout="wide")
st.sidebar.header("➕ Dodaj novi obrok u bazu")

# Ucitavanje plana i baze
if "plan" not in st.session_state:
    st.session_state.plan = load_pickle(PLAN_FILE, init_plan())
plan = st.session_state.plan
baza = load_pickle(BAZA_FILE, [])

# Inicijalizacija baze ako ne postoji
if not os.path.exists(BAZA_FILE):
    meals_db = [
        {"naziv": "Junetina leso i povrce", "samo_vecera": False},
        {"naziv": "Tortilje s grahom i kukuruzom", "samo_vecera": False},
        {"naziv": "Varivo od lece i slanutka", "samo_vecera": False},
        {"naziv": "Namaz od slanutka", "samo_vecera": True},
        {"naziv": "Piletina s mahunama i povrcem", "samo_vecera": False},
        {"naziv": "Standardna salata", "samo_vecera": True},
    ]
    save_pickle(meals_db, BAZA_FILE)
    st.success("Baza jela je inicijalizirana!")
    st.stop()

# Dodavanje novog obroka
with st.sidebar.form("meal_form"):
    naziv = st.text_input("Naziv obroka")
    samo_vecera = st.checkbox("Samo vecera?", value=False)
    submitted = st.form_submit_button("Dodaj obrok u bazu")
    if submitted and naziv:
        dodaj_u_bazu({"naziv": naziv, "samo_vecera": samo_vecera})
        st.success(f"Obrok '{naziv}' dodan u bazu!")
        st.rerun()

st.sidebar.markdown("---")

# Generiranje plana
if st.sidebar.button("🎲 Generiraj tjedni plan (rucak + vecera)"):
    novi_plan = generiraj_tjedni_plan()
    if novi_plan:
        st.session_state.plan = novi_plan
        save_pickle(novi_plan, PLAN_FILE)
        spremi_u_povijest(novi_plan)
        st.success("Tjedni plan je generiran i spremljen!")
        st.rerun()

# Reset plana
if st.sidebar.button("🗑️ Resetiraj cijeli plan"):
    st.session_state.plan = init_plan()
    save_pickle(st.session_state.plan, PLAN_FILE)
    st.rerun()

# Prikaz tjednog plana
cols = st.columns(7)
for i, day in enumerate(DAYS):
    with cols[i]:
        st.markdown(f"### {day}")
        dnevni = plan.get(day, {})

        # Rucak
        rucak = dnevni.get("rucak")
        if st.button(rucak['naziv'] if rucak else "Dodaj rucak", key=f"rucak_{day}"):
            moguci = [m for m in baza if not m.get("samo_vecera", False) and m != rucak]
            if moguci:
                dnevni["rucak"] = random.choice(moguci)
                save_pickle(plan, PLAN_FILE)
                st.rerun()

        # Vecera
        vecera = dnevni.get("vecera")
        if st.button(vecera['naziv'] if vecera else "Dodaj veceru", key=f"vecera_{day}", type="secondary"):
            moguci = [m for m in baza if m != vecera]
            if moguci:
                dnevni["vecera"] = random.choice(moguci)
                save_pickle(plan, PLAN_FILE)
                st.rerun()

        # Ostaci od rucka (ikona)
        if st.button("🍛", key=f"ostaci_{day}", help="Postavi veceru kao ostatke od rucka"):
            dnevni["vecera"] = dnevni["rucak"]
            save_pickle(plan, PLAN_FILE)
            st.rerun()

st.markdown("---")

# Prikaz baze jela
with st.expander("📋 Prikazi sva jela u bazi"):
    for meal in baza:
        tag = " (samo vecera)" if meal.get("samo_vecera", False) else ""
        st.write(f"- {meal['naziv']}{tag}")

# Prikaz povijesti
prikazi_povijest()
