import streamlit as st
import pandas as pd
import re
from io import BytesIO
from main import main

def Schematic():
   main("SCHEMATIC","Sch_relay", "sch_checkbox","sch_na_checkbox", "sch_download" )