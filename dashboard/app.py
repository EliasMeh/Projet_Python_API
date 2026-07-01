from __future__ import annotations

import os
from datetime import datetime

import httpx
import pandas as pd
import streamlit as st


st.set_page_config(page_title="DevOps Monitoring Dashboard", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_KEY = os.getenv("API_KEY", "")


@st.cache_data(ttl=1)
def fetch_metrics() -> dict:
    response = httpx.get(f"{API_BASE_URL}/metrics", timeout=5)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=1)
def fetch_servers() -> list[dict]:
    response = httpx.get(f"{API_BASE_URL}/servers", timeout=5)
    response.raise_for_status()
    return response.json()


def append_metric_snapshot(snapshot: dict) -> None:
    history = st.session_state.setdefault("metrics_history", [])
    history.append(
        {
            "timestamp": datetime.utcnow(),
            "cpu_percent": snapshot["cpu_percent"],
            "memory_percent": snapshot["memory_percent"],
            "disk_percent": snapshot["disk_percent"],
        }
    )
    st.session_state["metrics_history"] = history[-60:]


def status_style(value: str) -> str:
    palette = {
        "UP": "background-color: #d1e7dd; color: #0f5132;",
        "DEGRADED": "background-color: #fff3cd; color: #664d03;",
        "DOWN": "background-color: #f8d7da; color: #842029;",
        "unknown": "background-color: #e2e3e5; color: #41464b;",
    }
    return palette.get(str(value), "")


st.title("DevOps Monitoring Dashboard")
st.caption("Monitoring temps réel des métriques système et des serveurs enregistrés.")

metrics_tab, servers_tab = st.tabs(["Métriques", "Serveurs"])

with metrics_tab:
    refresh = st.button("Rafraîchir les métriques")
    if refresh or "metrics_history" not in st.session_state:
        snapshot = fetch_metrics()
        append_metric_snapshot(snapshot)
        st.rerun()

    snapshot = fetch_metrics()
    append_metric_snapshot(snapshot)

    col1, col2, col3 = st.columns(3)
    col1.metric("CPU", f"{snapshot['cpu_percent']:.1f}%")
    col2.metric("Mémoire", f"{snapshot['memory_percent']:.1f}%")
    col3.metric("Disque", f"{snapshot['disk_percent']:.1f}%")

    history = pd.DataFrame(st.session_state.get("metrics_history", []))
    if not history.empty:
        history = history.set_index("timestamp")
        st.line_chart(history[["cpu_percent", "memory_percent", "disk_percent"]])

with servers_tab:
    st.subheader("Serveurs enregistrés")
    server_rows = fetch_servers()
    server_df = pd.DataFrame(server_rows)

    if server_df.empty:
        st.info("Aucun serveur enregistré pour le moment.")
    else:
        styled = server_df.style.map(status_style, subset=["status"])
        st.dataframe(styled, use_container_width=True)

    st.subheader("Enregistrer un serveur")
    with st.form("register_server_form"):
        name = st.text_input("Nom")
        host = st.text_input("Hôte", value="httpbin.org")
        port = st.number_input("Port", min_value=1, max_value=65535, value=443)
        tags = st.text_input("Tags (séparés par des virgules)")
        submitted = st.form_submit_button("Enregistrer")

    if submitted:
        payload = {
            "name": name,
            "host": host,
            "port": int(port),
            "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
        }
        headers = {"X-API-Key": API_KEY} if API_KEY else {}
        response = httpx.post(f"{API_BASE_URL}/servers", json=payload, headers=headers, timeout=10)
        if response.status_code == 201:
            st.success("Serveur enregistré.")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"Erreur lors de l'enregistrement: {response.status_code} - {response.text}")
