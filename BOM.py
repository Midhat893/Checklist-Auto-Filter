import streamlit as st
import pandas as pd
import re
from io import BytesIO
from main import main

def BOM():
   main("BOM", "bom_relay", "bom_checkbox","bom_na_checklist", "bom_download")