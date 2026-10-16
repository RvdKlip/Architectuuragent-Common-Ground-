"""Presentatie van de werkruimte; geen broninhoud of architectuurbesluiten."""
import base64
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parents[1]/'assets'


def apply_style():
    st.markdown('<style>' + (ASSETS/'workspace.css').read_text() + '</style>', unsafe_allow_html=True)


def render_hero():
    artwork = base64.b64encode((ASSETS/'architecture-hero.png').read_bytes()).decode('ascii')
    st.markdown(f'''
<section class="architecture-hero" aria-label="Architectuurwerkruimte">
  <img class="hero-art" src="data:image/png;base64,{artwork}" alt="Conceptvisual van vijf zwevende architectuurlagen met glazen bouwblokken en groene verbindingen">
  <div class="hero-shade"></div>
  <div class="hero-copy">
    <div class="eyebrow"><span class="live-dot"></span> COMMON GROUND · ARCHITECTUURAGENT</div>
    <h2>Een sterk begin.<br><span>Een helder ontwerp.</span></h2>
    <p>Van projectambitie naar een onderbouwde architectuur.<br>Kies je bronnen. Leg je fundament.</p>
    <a class="hero-action" href="#generate-psa" target="_self">Genereer PSA <span aria-hidden="true">↗</span></a>
  </div>
  <div class="hero-footer"><span><span class="live-dot"></span> Vijf lagen. Eén samenhangend fundament.</span><span class="concept-label">CONCEPTVISUAL</span></div>
</section>
''', unsafe_allow_html=True)


def render_steps():
    st.markdown('''<nav class="workflow-steps" aria-label="Werkwijze">
<a href="#project" target="_self"><span>01</span> Je project</a><i aria-hidden="true">/</i>
<a href="#bronnen" target="_self"><span>02</span> Je bronnen</a><i aria-hidden="true">/</i>
<a href="#concept" target="_self"><span>03</span> Je architectuur</a>
</nav>''', unsafe_allow_html=True)
