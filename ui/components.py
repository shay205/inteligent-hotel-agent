"""Reusable UI building blocks."""
from html import escape
from typing import Optional

import pandas as pd
import streamlit as st

from hotel_agent.ai.recommender import Recommendation
from hotel_agent.config import format_money


def rerun() -> None:
    """Works on old and new Streamlit versions."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:  # pragma: no cover
        st.experimental_rerun()


def hero(title: str, subtitle: str = "") -> None:
    st.markdown(f"<div class='page-hero'><p class='eyebrow'>Luxury Grand Hotel</p>"
                f"<h1>{escape(title)}</h1><p>{escape(subtitle)}</p></div>",
                unsafe_allow_html=True)


def metric_card(label: str, value, caption: str = "") -> None:
    st.markdown(
        f"<div class='metric'><div class='label'>{escape(str(label))}</div>"
        f"<div class='value'>{escape(str(value))}</div>"
        f"<div class='caption'>{escape(caption)}</div></div>", unsafe_allow_html=True)


def show_table(df: pd.DataFrame) -> None:
    """Full-width table that works across Streamlit versions."""
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except Exception:
        st.dataframe(df, use_container_width=True, hide_index=True)


def room_card(rec: Recommendation) -> None:
    r = rec.room
    css = "room-card" + ("" if rec.available else " unavailable")
    reasons = "".join(f"<li>{escape(x)}</li>" for x in rec.reasons)
    warnings = "".join(f"<li class='warn'>{escape(x)}</li>" for x in rec.warnings)
    status = "" if rec.available else "<span class='badge'>Not available</span>"
    room_images = {
        "Standard": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?auto=format&fit=crop&w=1200&q=92",
        "Deluxe": "https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1200&q=92",
        "Family": "https://images.unsplash.com/photo-1590490360182-c33d57733427?auto=format&fit=crop&w=1200&q=92",
        "Executive": "https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=1200&q=92",
        "Suite": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1200&q=92",
    }
    room_image = room_images.get(r.accommodation_type, room_images["Standard"])
    st.markdown(
        f"""<div class='{css}'>
        <div class='room-card-image' style="background-image:url('{escape(room_image)}')"></div>
        <div style='display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap'>
          <div><div class='title'>Room {escape(r.room_number)} - {escape(r.name)}</div>
          <div class='meta'><span class='badge'>{escape(r.accommodation_type)}</span>
          <span class='badge'>{escape(r.location)}</span><span class='badge'>Sleeps {r.capacity}</span>{status}</div></div>
          <div style='text-align:right'><div class='price'>{format_money(r.price_per_night)}<span class='meta'> /night</span></div>
          <div>Match <span class='score-num'>{rec.score:.0f}/100</span></div></div>
        </div>
        <div class='score-wrap'><div class='score-bar' style='width:{max(0, min(100, rec.score)):.0f}%'></div></div>
        <div class='meta' style='margin-top:8px'>{escape(r.amenities_text)}</div>
        <ul>{reasons}{warnings}</ul></div>""", unsafe_allow_html=True)


def navigate(page: str, **prefill) -> None:
    """Jump to another page (optionally passing values for its form)."""
    st.session_state["_goto"] = page
    if prefill:
        st.session_state["booking_prefill"] = prefill
    rerun()


def flash(kind: str, message: str) -> None:
    """Remember a message so it survives the next rerun."""
    st.session_state.setdefault("_flash", []).append((kind, message))


def show_flash() -> None:
    for kind, message in st.session_state.pop("_flash", []):
        getattr(st, kind, st.info)(message)


def money_df(df: pd.DataFrame, columns) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = out[col].apply(format_money)
    return out


def optional(value, empty_values=("Any", "", None)) -> Optional[str]:
    return None if value in empty_values else value