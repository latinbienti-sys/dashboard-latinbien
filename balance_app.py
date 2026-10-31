#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, shutil, json
from datetime import datetime
import pandas as pd
from openpyxl import load_workbook

EXCEL_FILE = 'BALANCE GRUPO DE EMPRESAS.xlsx'
SHEET_NAME = 'Copia de BALANCE 3'
BACKUP_DIR = 'backups_balance'
