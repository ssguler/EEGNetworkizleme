import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import subprocess
import threading
import time
import json
import os
from datetime import datetime
import platform
import re
import sys
import base64
from PIL import Image, ImageTk
import io
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
import requests
from io import BytesIO
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import language system
from languages import lang_manager

# Logging ayarları
log_dosyasi = "ag_izleme.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_dosyasi, maxBytes=1048576, backupCount=5, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Gömülü Icon (Base64 - Dünya ikonu)
WORLD_ICON_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwYAAADfElEQVR4nO2bP2hTURTGv0Q6+AdEKAiC4iKKgxQcdNChgoN0EiqpNbFqKaKiONRBsIMPTRxsGycdKhRcOli1uDiVNoo4GQTBQXQQKSjiIHQQ6SA6KNL3vdzHu+WVl/fy/kkMfHDDy31/vu+773DvPQIAAAAA/jYmkwm5+rsCAChNIpGgCxcuaDweK5FIKJPJ0Gw2EwBINptVMplUJpNROBzW1NPTU6B9jEYjHR4eEgDwemJIDx8+VC6XUzweL1Aul9Pb21sCAAxDs9lMNzc3BAD/lYGBARUKeTHau6iurg6HwwIAcEcikYhyuZwAgKzy+byi0agAgKzy+bxCoZAAgKzy+TzF43EBAFk1NjZSJpMRAJBVsVhUJpMRAJBVoVCgSCQiACCrYrFIqVRKAEBWTU1NZCkIywpSMGzP1UyqTCbDYRiez+cLAGD7AqFQSHV1daqsrKREIsF9R0dH7DvDMOyHhwefnx+NRiP7DqQNQ7AvLy/cd3Z2Zt/BeHd3l/t+dHTE9YbjkUjEvoPxYrGofD4vACCr/HxeAEBW+XxeoVBIAEBWmUxGAEBWhUJBAEBWjY2NAgCySiaTAgCyKpVKAgCyKpVKAgCyKi4V0eY1Ea1fItq+JaI3jynGqKmpEQDw7TKfF9FVnYje3hVxPpNJMI8vyQMAwF/k7l0R5wHsEqytrVUoFOJ6IpFgAAD/NvX19VpYWAjfFxcX9f37d8YdHR3h++Li4uYPxV8iGo3yPZzPZgUAYFlaCgLAM9RUEACeoa6CAAD8gzUUBIDnqKsgALxDXQUB4FnsqyAAvIu9FQSAh7GzggDwNnZWEAAex44KAsAD2d2CWTAyMgKAQLhGpbwiIeD5lEpFjY6OahQKMSMjI5wPBoP0+PFjAQB3n1gsRomEHR+De/4wDKVSKT0+PvJ3mUyGouOjT77Ozs6yv/HxcfY3NjaGTqdTr6+vBQB8W3R3d9PZ2Rm9vb2pv7+fdnZ2tLW1pXQ6zev39/ecn56eZi4vL+Xo8vJSwFczFotxPpvNyjAMff/+XQ8PD/r5+alMJiOjWFtbYz6fn4nH44zLywu4w2QyGc7n83nO+/1+NTU1KRwOi2M+PtD9/b1OTk705eWFy+VyWcaXlxfOl8tlBmw0Gk2FQkFAXZ1MJsP5YrHIVS6XKxwOy+fzBfgPm5ub/Ts7O/yOzWYj39/flU6nbcsEg8EAgFpnsxn/tLCwIMMwmPv7+2E1NzdXwJ21ubmZgVun1WoV4H9vNpsF/CuCIIgRQRBGAAAAAIA/z1/8k5zGDwqh5AAAAABJRU5ErkJggg==
"""

# Modern Cyber Tema renkleri
TEMALAR = {
    "Cyber Neon": {
        "bg": "#0a0a0f",
        "frame": "#111118",
        "card_bg": "#1a1a2e",
        "card_online": "#0a2a1a",
        "card_offline": "#2a1a1a",
        "border_online": "#00ffcc",
        "border_offline": "#ff3366",
        "text": "#00ffcc",
        "text_secondary": "#8888aa",
        "button": "#00ffcc",
        "button_hover": "#00ccaa",
        "success": "#00ff88",
        "warning": "#ffaa00",
        "danger": "#ff3366"
    }
}

# Aktif tema
AKTIF_TEMA = "Cyber Neon"
RENKLER = TEMALAR[AKTIF_TEMA]

# Sistem ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
IS_WINDOWS = platform.system() == "Windows"

class Database:
    """SQLite veritabanı sınıfı"""
    def __init__(self):
        self.db_file = "cihazlar.db"
        self.init_db()
        logger.info("Veritabanı başlatıldı")
    
    def init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cihazlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                ip TEXT NOT NULL UNIQUE,
                mac TEXT,
                son_durum INTEGER DEFAULT 0,
                son_kontrol TEXT,
                eklenme_tarihi TEXT,
                guncellenme_tarihi TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cihaz_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cihaz_id INTEGER,
                cihaz_ad TEXT,
                eski_durum TEXT,
                yeni_durum TEXT,
                ip TEXT,
                timestamp TEXT,
                FOREIGN KEY (cihaz_id) REFERENCES cihazlar (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def cihaz_ekle(self, ad, ip, mac):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO cihazlar (ad, ip, mac, eklenme_tarihi, guncellenme_tarihi)
                VALUES (?, ?, ?, ?, ?)
            ''', (ad, ip, mac, datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            cihaz_id = cursor.lastrowid
            self.log_ekle(cihaz_id, ad, "CIHAZ_EKLENDI", "", "", ip)
            logger.info(f"Cihaz eklendi: {ad} - {ip}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Cihaz eklenemedi, IP zaten var: {ip}")
            return False
        finally:
            conn.close()
    
    def cihaz_guncelle(self, cihaz_id, ad, ip, mac):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cihazlar SET ad=?, ip=?, mac=?, guncellenme_tarihi=?
            WHERE id=?
        ''', (ad, ip, mac, datetime.now().isoformat(), cihaz_id))
        conn.commit()
        conn.close()
        logger.info(f"Cihaz güncellendi: {ad}")
    
    def cihaz_sil(self, cihaz_id, ad):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cihazlar WHERE id=?', (cihaz_id,))
        cursor.execute('DELETE FROM cihaz_log WHERE cihaz_id=?', (cihaz_id,))
        conn.commit()
        conn.close()
        logger.info(f"Cihaz silindi: {ad}")
    
    def durum_guncelle(self, cihaz_id, ad, durum, ip):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT son_durum FROM cihazlar WHERE id=?', (cihaz_id,))
        row = cursor.fetchone()
        eski_durum = row[0] if row else -1
        
        cursor.execute('''
            UPDATE cihazlar SET son_durum=?, son_kontrol=?, guncellenme_tarihi=?
            WHERE id=?
        ''', (1 if durum else 0, datetime.now().strftime("%H:%M:%S"), datetime.now().isoformat(), cihaz_id))
        conn.commit()
        
        if eski_durum != (1 if durum else 0) and eski_durum != -1:
            eski_str = "ONLINE" if eski_durum == 1 else "OFFLINE"
            yeni_str = "ONLINE" if durum else "OFFLINE"
            self.log_ekle(cihaz_id, ad, "DURUM_DEGISTI", eski_str, yeni_str, ip)
            logger.info(f"Durum değişti: {ad} - {eski_str} -> {yeni_str}")
        conn.close()
    
    def log_ekle(self, cihaz_id, cihaz_ad, olay_tipi, eski_durum, yeni_durum, ip):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cihaz_log (cihaz_id, cihaz_ad, eski_durum, yeni_durum, ip, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cihaz_id, cihaz_ad, eski_durum, yeni_durum, ip, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def tum_cihazlari_al(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT id, ad, ip, mac, son_durum, son_kontrol, eklenme_tarihi FROM cihazlar')
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def loglari_al(self, limit=100):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, cihaz_ad, eski_durum, yeni_durum, ip 
            FROM cihaz_log 
            ORDER BY id DESC LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def cihaz_var_mi(self, ip):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM cihazlar WHERE ip=?', (ip,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

class NetworkScanner:
    """Ağ tarama sınıfı"""
    def __init__(self, callback, progress_callback=None):
        self.callback = callback
        self.progress_callback = progress_callback
        self.duruyor = False
    
    def durdur(self):
        self.duruyor = True
    
    def ping_host(self, ip):
        """Tek bir hosta ping at"""
        try:
            if IS_WINDOWS:
                komut = ["ping", "-n", "1", "-w", "500", ip]
            else:
                komut = ["ping", "-c", "1", "-W", "1", ip]
            result = subprocess.run(komut, capture_output=True, timeout=1)
            return result.returncode == 0
        except:
            return False
    
    def get_hostname(self, ip):
        """IP'den hostname al"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname.split('.')[0]
        except:
            return None
    
    def tarama_yap(self, subnet="192.168.1"):
        """Ağı tara"""
        self.duruyor = False
        aktif_cihazlar = []
        
        # Tarama aralığı
        ips = [f"{subnet}.{i}" for i in range(1, 255)]
        toplam = len(ips)
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            gelecekler = {executor.submit(self.ping_host, ip): ip for ip in ips}
            
            for i, gelecek in enumerate(as_completed(gelecekler)):
                if self.duruyor:
                    executor.shutdown(wait=False, cancel_futures=True)
                    return []
                
                ip = gelecekler[gelecek]
                if gelecek.result():
                    hostname = self.get_hostname(ip)
                    aktif_cihazlar.append({
                        'ip': ip,
                        'ad': hostname or f"Bilinmeyen_{ip.split('.')[-1]}",
                        'mac': "Taranıyor..."
                    })
                
                if self.progress_callback:
                    self.progress_callback(int((i + 1) / toplam * 100), ip)
        
        return aktif_cihazlar

class Cihaz:
    def __init__(self, cihaz_id, ad, ip, mac, son_durum, son_kontrol, eklenme_tarihi):
        self.id = cihaz_id
        self.ad = ad
        self.ip = ip
        self.mac = mac if mac else "Bilinmiyor"
        self.online = son_durum == 1
        self.son_kontrol = son_kontrol
        self.eklenme_tarihi = eklenme_tarihi

class OvalButton(ctk.CTkButton):
    def __init__(self, master, **kwargs):
        if 'corner_radius' not in kwargs:
            kwargs['corner_radius'] = 25
        if 'height' not in kwargs:
            kwargs['height'] = 45
        super().__init__(master, **kwargs)

class AgIzlemeUygulamasi:
    def __init__(self):
        self.pencere = ctk.CTk()
        self.pencere.title(lang_manager.get_text('app_title'))
        self.pencere.geometry("1600x950")
        self.pencere.minsize(1200, 700)
        self.pencere.configure(fg_color=RENKLER["bg"])
        
        self.db = Database()
        self.cihazlar = []
        self.izleme_aktif = True
        self.izleme_thread = None
        self.arkaplan_resmi = None
        self.scanner = None
        self.local_subnet = self.detect_default_subnet()
        self.network_mode_var = ctk.StringVar(value='auto')
        self.manual_subnet_var = ctk.StringVar(value=self.local_subnet)
        
        self.load_background()
        self.ui_olustur()
        self.verileri_yukle()
        self.saat_guncelle()
        self.izleme_baslat()
        self.pencere.protocol("WM_DELETE_WINDOW", self.kapat)
        logger.info("Uygulama başlatıldı")
    
    def dil_degistir(self, selection):
        """Dil değiştirme işlemi"""
        lang_code = selection.split(':')[0].lower()
        if lang_manager.set_language(lang_code):
            self.pencere.title(lang_manager.get_text('app_title'))
            self.ui_guncelle_dil()
            logger.info(f"Dil değiştirildi: {lang_code}")
    
    def ui_guncelle_dil(self):
        """UI'yi yeni dile göre güncelle"""
        # Update window title
        self.pencere.title(lang_manager.get_text('app_title'))
        
        # Update main UI elements
        self.baslik_label.configure(text=lang_manager.get_text('title'))
        self.alt_baslik_label.configure(text=lang_manager.get_text('subtitle'))
        self.durum.configure(text=lang_manager.get_text('status_active'))
        
        # Update button texts
        self.tara_ag_btn.configure(text=lang_manager.get_text('scan_network'))
        self.ekle_btn.configure(text=lang_manager.get_text('add_device'))
        self.tara_btn.configure(text=lang_manager.get_text('scan_now'))
        self.log_btn.configure(text=lang_manager.get_text('logs'))
        self.yedekle_btn.configure(text=lang_manager.get_text('backup'))
        self.export_btn.configure(text=lang_manager.get_text('export'))
        self.hakkinda_btn.configure(text=lang_manager.get_text('about'))
        self.tara_ag_large_btn.configure(text=lang_manager.get_text('start_scan'))
        self.ekle_large_btn.configure(text=lang_manager.get_text('add_device'))
        self.dil_label.configure(text=lang_manager.get_text('language'))
        self.settings_title_label.configure(text=lang_manager.get_text('settings_title'))
        self.settings_info_label.configure(text=lang_manager.get_text('settings_info'))
        self.auto_radio.configure(text=lang_manager.get_text('mode_auto'))
        self.manual_radio.configure(text=lang_manager.get_text('mode_manual'))
        self.auto_note_label.configure(text=lang_manager.get_text('auto_subnet_desc', subnet=self.local_subnet) if self.network_mode_var.get() == 'auto' else lang_manager.get_text('manual_subnet_hint'))
        self.manual_label.configure(text=lang_manager.get_text('manual_subnet'))
        self.manual_subnet_entry.configure(placeholder_text=lang_manager.get_text('manual_subnet_hint'))
        
        # Update statistics
        self.istatistikleri_guncelle()
        
        # Update device cards
        self.kartlari_guncelle()
        
        logger.info(f"UI dil güncellendi: {lang_manager.current_lang}")
    
    def load_background(self):
        def yukle():
            self.arkaplan_resmi = None
        threading.Thread(target=yukle, daemon=True).start()

    def detect_default_subnet(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return ".".join(local_ip.split(".")[:-1])
        except:
            return "192.168.1"

    def update_network_mode(self):
        if self.network_mode_var.get() == 'manual':
            self.manual_frame.pack(fill="x", padx=20, pady=(5, 10))
            self.auto_note_label.configure(text=lang_manager.get_text('manual_subnet_hint'))
        else:
            self.manual_frame.pack_forget()
            self.auto_note_label.configure(text=lang_manager.get_text('auto_subnet_desc', subnet=self.local_subnet))

    def ui_olustur(self):
        # Ana frame
        ana_frame = ctk.CTkFrame(self.pencere, fg_color="#0a0a0f", corner_radius=0)
        ana_frame.pack(fill="both", expand=True)
        
        # ÜST BAR
        ust_bar = ctk.CTkFrame(ana_frame, fg_color=RENKLER["card_bg"], height=130, corner_radius=25)
        ust_bar.pack(fill="x", pady=(20, 10), padx=20)
        ust_bar.pack_propagate(False)
        
        sol_frame = ctk.CTkFrame(ust_bar, fg_color="transparent")
        sol_frame.pack(side="left", padx=20, pady=15)
        
        logo_label = ctk.CTkLabel(sol_frame, text="🌐", font=ctk.CTkFont(size=40))
        logo_label.pack(side="left", padx=(0, 10))
        
        baslik_frame = ctk.CTkFrame(sol_frame, fg_color="transparent")
        baslik_frame.pack(side="left")
        
        self.baslik_label = ctk.CTkLabel(baslik_frame, text=lang_manager.get_text('title'), font=ctk.CTkFont(size=24, weight="bold"), text_color=RENKLER["text"])
        self.baslik_label.pack(anchor="w")
        
        self.alt_baslik_label = ctk.CTkLabel(baslik_frame, text=lang_manager.get_text('subtitle'), font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"])
        self.alt_baslik_label.pack(anchor="w")
        
        sag_frame = ctk.CTkFrame(ust_bar, fg_color="transparent")
        sag_frame.pack(side="right", padx=20, pady=15)
        
        # Language selector
        self.lang_var = ctk.StringVar(value=lang_manager.current_lang)
        lang_names = lang_manager.get_language_names()
        lang_options = [f"{code.upper()}: {name}" for code, name in lang_names.items()]
        
        self.dil_label = ctk.CTkLabel(sag_frame, text=lang_manager.get_text('language'), font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"])
        self.dil_label.pack(anchor="e", pady=(0, 4))

        self.lang_combo = ctk.CTkComboBox(
            sag_frame, 
            values=lang_options,
            variable=self.lang_var,
            command=self.dil_degistir,
            width=140,
            height=30,
            font=ctk.CTkFont(size=11)
        )
        self.lang_combo.pack(anchor="e", pady=(0, 8))
        
        self.tarih_label = ctk.CTkLabel(sag_frame, text="📅 --.--.----", font=ctk.CTkFont(size=14, weight="bold"), text_color=RENKLER["text_secondary"])
        self.tarih_label.pack(anchor="e", pady=(0, 2))
        
        self.saat_label = ctk.CTkLabel(sag_frame, text="�️ --:--:--", font=ctk.CTkFont(size=22, weight="bold"), text_color=RENKLER["success"])
        self.saat_label.pack(anchor="e", pady=(8, 0))
        
        # KONTROL PANELİ
        kontrol_frame = ctk.CTkFrame(ana_frame, fg_color=RENKLER["frame"], corner_radius=15)
        kontrol_frame.pack(fill="x", pady=(0, 15), padx=20)
        
        istatistik_frame = ctk.CTkFrame(kontrol_frame, fg_color="transparent")
        istatistik_frame.pack(side="left", padx=20, pady=12)
        
        self.toplam_cihaz_label = ctk.CTkLabel(istatistik_frame, text=lang_manager.get_text('total_devices', count=0), font=ctk.CTkFont(size=14, weight="bold"), text_color=RENKLER["text"])
        self.toplam_cihaz_label.pack(side="left", padx=15)
        
        self.online_sayisi_label = ctk.CTkLabel(istatistik_frame, text=lang_manager.get_text('online_devices', count=0), font=ctk.CTkFont(size=14, weight="bold"), text_color=RENKLER["success"])
        self.online_sayisi_label.pack(side="left", padx=15)
        
        self.offline_sayisi_label = ctk.CTkLabel(istatistik_frame, text=lang_manager.get_text('offline_devices', count=0), font=ctk.CTkFont(size=14, weight="bold"), text_color=RENKLER["danger"])
        self.offline_sayisi_label.pack(side="left", padx=15)
        
        button_frame = ctk.CTkFrame(kontrol_frame, fg_color="transparent")
        button_frame.pack(side="right", padx=20, pady=12)
        
        self.tara_ag_btn = OvalButton(button_frame, text=lang_manager.get_text('scan_network'), command=self.ag_tarama_baslat, width=120, font=ctk.CTkFont(size=13, weight="bold"), fg_color="#9b59b6", hover_color="#8e44ad", text_color="#ffffff")
        self.tara_ag_btn.pack(side="left", padx=5)
        
        self.ekle_btn = OvalButton(button_frame, text=lang_manager.get_text('add_device'), command=self.cihaz_ekle_dialog, width=120, font=ctk.CTkFont(size=13, weight="bold"), fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f")
        self.ekle_btn.pack(side="left", padx=5)
        
        self.tara_btn = OvalButton(button_frame, text=lang_manager.get_text('scan_now'), command=self.ani_kontrol_baslat, width=110, font=ctk.CTkFont(size=13, weight="bold"), fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f")
        self.tara_btn.pack(side="left", padx=5)
        
        self.log_btn = OvalButton(button_frame, text=lang_manager.get_text('logs'), command=self.loglari_goster, width=90, font=ctk.CTkFont(size=13), fg_color=RENKLER["text_secondary"], hover_color="#666688", text_color="#ffffff")
        self.log_btn.pack(side="left", padx=5)
        
        self.yedekle_btn = OvalButton(button_frame, text=lang_manager.get_text('backup'), command=self.yedek_al, width=80, font=ctk.CTkFont(size=13), fg_color=RENKLER["text_secondary"], hover_color="#666688", text_color="#ffffff")
        self.yedekle_btn.pack(side="left", padx=5)
        
        self.export_btn = OvalButton(button_frame, text=lang_manager.get_text('export'), command=self.verileri_export_et, width=80, font=ctk.CTkFont(size=13), fg_color=RENKLER["text_secondary"], hover_color="#666688", text_color="#ffffff")
        self.export_btn.pack(side="left", padx=5)
        
        self.hakkinda_btn = OvalButton(button_frame, text=lang_manager.get_text('about'), command=self.hakkinda_goster, width=45, font=ctk.CTkFont(size=16), fg_color=RENKLER["frame"], hover_color=RENKLER["card_bg"], text_color=RENKLER["text"])
        self.hakkinda_btn.pack(side="left", padx=5)
        
        self.tara_ag_btn._lang_key = 'scan_network'
        self.ekle_btn._lang_key = 'add_device'
        self.tara_btn._lang_key = 'scan_now'
        self.log_btn._lang_key = 'logs'
        self.yedekle_btn._lang_key = 'backup'
        self.export_btn._lang_key = 'export'
        self.hakkinda_btn._lang_key = 'about'
        
        # KEŞİF PANELİ
        discover_frame = ctk.CTkFrame(ana_frame, fg_color=RENKLER["card_bg"], corner_radius=20)
        discover_frame.pack(fill="x", padx=20, pady=(0, 15))
        discover_frame.grid_columnconfigure(0, weight=3)
        discover_frame.grid_columnconfigure(1, weight=1)
        
        info_frame = ctk.CTkFrame(discover_frame, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        ctk.CTkLabel(info_frame, text=lang_manager.get_text('network_scan_title'), font=ctk.CTkFont(size=18, weight="bold"), text_color=RENKLER["text"]).pack(anchor="w")
        ctk.CTkLabel(info_frame, text=lang_manager.get_text('network_scan_desc'), font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"]).pack(anchor="w", pady=(8, 0))
        
        button_panel = ctk.CTkFrame(discover_frame, fg_color="transparent")
        button_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        button_panel.grid_rowconfigure(0, weight=1)
        button_panel.grid_rowconfigure(1, weight=1)
        button_panel.grid_columnconfigure(0, weight=1)
        self.tara_ag_large_btn = OvalButton(button_panel, text=lang_manager.get_text('start_scan'), command=self.ag_tarama_baslat, width=180, font=ctk.CTkFont(size=13, weight="bold"), fg_color=RENKLER["success"], hover_color="#00cc66", text_color="#0a0a0f")
        self.tara_ag_large_btn.pack(side="top", padx=5, pady=(0, 10), fill="x")
        self.ekle_large_btn = OvalButton(button_panel, text=lang_manager.get_text('add_device'), command=self.cihaz_ekle_dialog, width=180, font=ctk.CTkFont(size=13, weight="bold"), fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f")
        self.ekle_large_btn.pack(side="top", padx=5, fill="x")

        # AYGARLAR PANELİ
        settings_frame = ctk.CTkFrame(ana_frame, fg_color=RENKLER["card_bg"], corner_radius=20)
        settings_frame.pack(fill="x", padx=20, pady=(0, 15))
        settings_frame.grid_columnconfigure(0, weight=1)
        settings_frame.grid_columnconfigure(1, weight=1)

        settings_left = ctk.CTkFrame(settings_frame, fg_color="transparent")
        settings_left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.settings_title_label = ctk.CTkLabel(settings_left, text=lang_manager.get_text('settings_title'), font=ctk.CTkFont(size=16, weight="bold"), text_color=RENKLER["text"])
        self.settings_title_label.pack(anchor="w")
        self.settings_info_label = ctk.CTkLabel(settings_left, text=lang_manager.get_text('settings_info'), font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"])
        self.settings_info_label.pack(anchor="w", pady=(8, 0))

        network_settings = ctk.CTkFrame(settings_frame, fg_color="transparent")
        network_settings.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        self.auto_radio = ctk.CTkRadioButton(network_settings, text=lang_manager.get_text('mode_auto'), variable=self.network_mode_var, value='auto', command=self.update_network_mode)
        self.auto_radio.pack(anchor="e", pady=(0, 5))
        self.manual_radio = ctk.CTkRadioButton(network_settings, text=lang_manager.get_text('mode_manual'), variable=self.network_mode_var, value='manual', command=self.update_network_mode)
        self.manual_radio.pack(anchor="e", pady=(0, 10))
        self.auto_note_label = ctk.CTkLabel(network_settings, text=lang_manager.get_text('auto_subnet_desc', subnet=self.local_subnet), font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"], wraplength=280, justify="right")
        self.auto_note_label.pack(anchor="e", pady=(0, 10))

        self.manual_frame = ctk.CTkFrame(network_settings, fg_color=RENKLER["frame"], corner_radius=12)
        self.manual_frame.pack(fill="x", pady=(0, 0))
        self.manual_label = ctk.CTkLabel(self.manual_frame, text=lang_manager.get_text('manual_subnet'), font=ctk.CTkFont(size=12), text_color=RENKLER["text"])
        self.manual_label.pack(anchor="w", padx=12, pady=(12, 5))
        self.manual_subnet_entry = ctk.CTkEntry(self.manual_frame, textvariable=self.manual_subnet_var, width=200, font=ctk.CTkFont(size=12))
        self.manual_subnet_entry.pack(anchor="w", padx=12, pady=(0, 10))
        ctk.CTkLabel(self.manual_frame, text=lang_manager.get_text('manual_subnet_hint'), font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"]).pack(anchor="w", padx=12, pady=(0, 12))
        self.manual_frame.pack_forget()
        self.update_network_mode()

        # CİHAZ KARTLARI
        kart_frame = ctk.CTkFrame(ana_frame, fg_color="transparent")
        kart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        
        self.scrollable_frame = ctk.CTkScrollableFrame(kart_frame, fg_color="transparent", corner_radius=15)
        self.scrollable_frame.pack(fill="both", expand=True)
        
        # ALT ÇUBUK
        alt_bar = ctk.CTkFrame(ana_frame, fg_color=RENKLER["frame"], height=35, corner_radius=10)
        alt_bar.pack(fill="x", pady=(0, 10), padx=20)
        
        self.durum = ctk.CTkLabel(alt_bar, text=lang_manager.get_text('status_active'), font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"])
        self.durum.pack(side="left", padx=15, pady=8)
        
        iletisim_label = ctk.CTkLabel(alt_bar, text=lang_manager.get_text('contact'), font=ctk.CTkFont(size=10), text_color=RENKLER["text_secondary"])
        iletisim_label.pack(side="right", padx=15, pady=8)
    
    def ag_tarama_baslat(self):
        """Ağ tarama penceresini aç"""
        tarama_window = ctk.CTkToplevel(self.pencere)
        tarama_window.title(lang_manager.get_text('network_scan_title'))
        tarama_window.geometry("600x500")
        tarama_window.grab_set()
        
        main_frame = ctk.CTkFrame(tarama_window, fg_color=RENKLER["bg"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(main_frame, text=f"📡 {lang_manager.get_text('network_scan_title')}", font=ctk.CTkFont(size=20, weight="bold"), text_color=RENKLER["success"]).pack(pady=(0, 10))
        ctk.CTkLabel(main_frame, text=lang_manager.get_text('network_scan_desc'), font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"]).pack(pady=(0, 10))
        ctk.CTkLabel(main_frame, text=lang_manager.get_text('scan_window_settings'), font=ctk.CTkFont(size=12, weight="bold"), text_color=RENKLER["text"]).pack(anchor="w", pady=(0, 5))
        
        # Alt ağ seçimi
        subnet_frame = ctk.CTkFrame(main_frame, fg_color=RENKLER["frame"], corner_radius=10)
        subnet_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(subnet_frame, text=lang_manager.get_text('subnet_label'), font=ctk.CTkFont(size=13, weight="bold"), text_color=RENKLER["text"]).pack(side="left", padx=15, pady=10)
        
        # Mevcut IP'yi al
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            default_subnet = ".".join(local_ip.split(".")[:-1])
        except:
            default_subnet = "192.168.1"
        
        subnet_value = self.manual_subnet_var.get() if self.network_mode_var.get() == 'manual' else self.local_subnet
        subnet_var = ctk.StringVar(value=subnet_value)
        subnet_entry = ctk.CTkEntry(subnet_frame, textvariable=subnet_var, width=150, font=ctk.CTkFont(size=13))
        subnet_entry.pack(side="left", padx=10, pady=10)
        if self.network_mode_var.get() == 'auto':
            subnet_entry.configure(state='disabled')
        
        ctk.CTkLabel(subnet_frame, text=lang_manager.get_text('subnet_hint'), font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"]).pack(side="left", padx=5, pady=10)
        
        # İlerleme çubuğu
        progress_frame = ctk.CTkFrame(main_frame, fg_color=RENKLER["frame"], corner_radius=10)
        progress_frame.pack(fill="x", pady=15)
        
        self.tarama_progress = ctk.CTkProgressBar(progress_frame, height=15, corner_radius=10)
        self.tarama_progress.pack(fill="x", padx=15, pady=(15, 5))
        self.tarama_progress.set(0)
        
        self.tarama_durum_label = ctk.CTkLabel(progress_frame, text=lang_manager.get_text('scan_ready'), font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"])
        self.tarama_durum_label.pack(pady=(5, 15))
        
        # Bulunan cihazlar listesi
        ctk.CTkLabel(main_frame, text=lang_manager.get_text('scanned_devices'), font=ctk.CTkFont(size=14, weight="bold"), text_color=RENKLER["text"]).pack(anchor="w", pady=(10, 5))
        
        list_frame = ctk.CTkScrollableFrame(main_frame, fg_color=RENKLER["frame"], corner_radius=10, height=200)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        self.tarama_listesi = []
        self.tarama_list_widgets = []
        
        # Butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)
        
        def tarama_baslat():
            self.tarama_listesi.clear()
            for widget in list_frame.winfo_children():
                widget.destroy()
            self.tarama_list_widgets.clear()
            
            subnet = subnet_var.get().strip()
            self.tarama_progress.set(0)
            
            def progress_callback(progress, ip):
                self.tarama_progress.set(progress / 100)
                self.tarama_durum_label.configure(text=lang_manager.get_text('scanning', ip=ip, progress=int(progress)))
                self.tarama_progress.update()
            
            def tamamlandi(cihazlar):
                self.tarama_durum_label.configure(text=lang_manager.get_text('scan_completed', count=len(cihazlar)))
                self.tarama_progress.set(1.0)
                
                for cihaz in cihazlar:
                    frame = ctk.CTkFrame(list_frame, fg_color=RENKLER["card_bg"], corner_radius=8)
                    frame.pack(fill="x", pady=3, padx=5)
                    
                    ctk.CTkLabel(frame, text=f"� {cihaz['ad']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=RENKLER["text"]).pack(side="left", padx=10, pady=8)
                    ctk.CTkLabel(frame, text=f"📶 {cihaz['ip']}", font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"]).pack(side="left", padx=10, pady=8)
                    
                    zaten_var = self.db.cihaz_var_mi(cihaz['ip'])
                    
                    if zaten_var:
                        durum_label = ctk.CTkLabel(frame, text=lang_manager.get_text('already_registered'), font=ctk.CTkFont(size=10), text_color=RENKLER["success"])
                        durum_label.pack(side="right", padx=10, pady=8)
                    else:
                        ekle_btn = OvalButton(frame, text=lang_manager.get_text('add'), width=60, height=28, font=ctk.CTkFont(size=11),
                            command=lambda c=cihaz, f=frame: self.tarama_cihaz_ekle(c, f),
                            fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f")
                        ekle_btn.pack(side="right", padx=10, pady=8)
                    
                    self.tarama_list_widgets.append(frame)
            
            self.scanner = NetworkScanner(tamamlandi, progress_callback)
            threading.Thread(target=lambda: self.scanner.tarama_yap(subnet), daemon=True).start()
        
        def tarama_durdur():
            if self.scanner:
                self.scanner.durdur()
                self.tarama_durum_label.configure(text=lang_manager.get_text('scan_stopped'), text_color=RENKLER["warning"])
        
        def tumunu_ekle():
            for widget in self.tarama_list_widgets:
                for child in widget.winfo_children():
                    if isinstance(child, OvalButton) and child.cget("text") == lang_manager.get_text('add'):
                        child.invoke()
        
        baslat_btn = OvalButton(button_frame, text=lang_manager.get_text('start_scan'), command=tarama_baslat, width=180, height=50, fg_color=RENKLER["success"], hover_color="#00cc66", text_color="#0a0a0f", font=ctk.CTkFont(size=14, weight="bold"))
        baslat_btn.pack(side="left", padx=5)
        
        durdur_btn = OvalButton(button_frame, text=lang_manager.get_text('stop_scan'), command=tarama_durdur, width=100, fg_color=RENKLER["danger"], hover_color="#ff3366", text_color="#ffffff")
        durdur_btn.pack(side="left", padx=5)
        
        tumunu_ekle_btn = OvalButton(button_frame, text=lang_manager.get_text('add_all'), command=tumunu_ekle, width=120, fg_color="#9b59b6", hover_color="#8e44ad", text_color="#ffffff")
        tumunu_ekle_btn.pack(side="left", padx=5)
        
        kapat_btn = OvalButton(button_frame, text=lang_manager.get_text('close'), command=tarama_window.destroy, width=100, fg_color="transparent", hover_color=RENKLER["card_bg"], text_color=RENKLER["text"])
        kapat_btn.pack(side="right", padx=5)
    
    def tarama_cihaz_ekle(self, cihaz, frame):
        """Tarama sonucu bulunan cihazı ekle"""
        if self.db.cihaz_ekle(cihaz['ad'], cihaz['ip'], cihaz.get('mac', 'Bilinmiyor')):
            self.verileri_yukle()
            self.kartlari_guncelle()
            self.istatistikleri_guncelle()
            
            # Butonu güncelle
            for child in frame.winfo_children():
                if isinstance(child, OvalButton):
                    child.destroy()
            durum_label = ctk.CTkLabel(frame, text="✅ Eklendi", font=ctk.CTkFont(size=10), text_color=RENKLER["success"])
            durum_label.pack(side="right", padx=10, pady=8)
            
            self.durum.configure(text=lang_manager.get_text('device_added', name=cihaz['ad']), text_color=RENKLER["success"])
            logger.info(f"Tarama ile cihaz eklendi: {cihaz['ad']} - {cihaz['ip']}")
    
    def loglari_goster(self):
        log_window = ctk.CTkToplevel(self.pencere)
        log_window.title(lang_manager.get_text('logs'))
        log_window.geometry("800x500")
        log_window.grab_set()
        
        loglar = self.db.loglari_al(200)
        
        main_frame = ctk.CTkFrame(log_window, fg_color=RENKLER["bg"])
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(main_frame, text=lang_manager.get_text('logs_title'), font=ctk.CTkFont(size=18, weight="bold"), text_color=RENKLER["text"]).pack(pady=(0, 15))
        
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color=RENKLER["frame"])
        scroll_frame.pack(fill="both", expand=True)
        
        if not loglar:
            ctk.CTkLabel(scroll_frame, text=lang_manager.get_text('no_logs'), text_color=RENKLER["text_secondary"]).pack(pady=20)
        else:
            for log in loglar:
                log_frame = ctk.CTkFrame(scroll_frame, fg_color=RENKLER["card_bg"], corner_radius=8)
                log_frame.pack(fill="x", pady=3, padx=5)
                
                text = f"{log[0][:16]} | {log[1]} | {log[2]} → {log[3]} | IP: {log[4]}"
                ctk.CTkLabel(log_frame, text=text, font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"]).pack(padx=10, pady=5, anchor="w")
        
        OvalButton(main_frame, text=lang_manager.get_text('close'), command=log_window.destroy, width=100, font=ctk.CTkFont(size=12), fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f").pack(pady=(15, 0))
    
    def verileri_yukle(self):
        self.cihazlar.clear()
        rows = self.db.tum_cihazlari_al()
        for row in rows:
            cihaz = Cihaz(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            self.cihazlar.append(cihaz)
        self.kartlari_guncelle()
        self.istatistikleri_guncelle()
        logger.info(f"{len(self.cihazlar)} cihaz yüklendi")
    
    def saat_guncelle(self):
        now = datetime.now()
        self.saat_label.configure(text=f"�️ {now.strftime('%H:%M:%S')}")
        self.tarih_label.configure(text=f"📅 {now.strftime('%d.%m.%Y')}")
        self.pencere.after(1000, self.saat_guncelle)
    
    def validate_ip(self, ip):
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip):
            parts = ip.split('.')
            for part in parts:
                if int(part) < 0 or int(part) > 255:
                    return False
            return True
        return False
    
    def validate_mac(self, mac):
        if not mac or mac == "Bilinmiyor":
            return True
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return re.match(pattern, mac) is not None
    
    def format_mac(self, mac):
        if mac and mac != "Bilinmiyor":
            return mac.upper()
        return "Bilinmiyor"
    
    def ping_cihaz(self, ip):
        try:
            if IS_WINDOWS:
                komut = ["ping", "-n", "1", "-w", "1000", ip]
            else:
                komut = ["ping", "-c", "1", "-W", "1", ip]
            result = subprocess.run(komut, capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False
    
    def cihaz_kontrol(self, cihaz):
        online = self.ping_cihaz(cihaz.ip)
        self.db.durum_guncelle(cihaz.id, cihaz.ad, online, cihaz.ip)
        if online != cihaz.online:
            cihaz.online = online
            cihaz.son_kontrol = datetime.now().strftime("%H:%M:%S")
            self.kartlari_guncelle()
            self.istatistikleri_guncelle()
            durum_str = "ONLINE" if online else "OFFLINE"
            logger.info(f"{cihaz.ad} ({cihaz.ip}) -> {durum_str}")
    
    def izleme_dongusu(self):
        while self.izleme_aktif:
            for cihaz in self.cihazlar:
                if not self.izleme_aktif:
                    break
                self.cihaz_kontrol(cihaz)
                time.sleep(1)
            for _ in range(60):
                if not self.izleme_aktif:
                    break
                time.sleep(1)
    
    def izleme_baslat(self):
        self.izleme_aktif = True
        self.izleme_thread = threading.Thread(target=self.izleme_dongusu, daemon=True)
        self.izleme_thread.start()
    
    def ani_kontrol_baslat(self):
        self.durum.configure(text=lang_manager.get_text('scanning_all'), text_color=RENKLER["warning"])
        threading.Thread(target=self.ani_kontrol_yap, daemon=True).start()
    
    def ani_kontrol_yap(self):
        for cihaz in self.cihazlar:
            self.cihaz_kontrol(cihaz)
            time.sleep(0.3)
        self.kartlari_guncelle()
        self.istatistikleri_guncelle()
        self.durum.configure(text=lang_manager.get_text('scan_complete'), text_color=RENKLER["success"])
    
    def cihaz_ekle_dialog(self):
        dialog = ctk.CTkToplevel(self.pencere)
        dialog.title(lang_manager.get_text('add_device_title'))
        dialog.geometry("500x550")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=25)
        
        ctk.CTkLabel(main_frame, text=lang_manager.get_text('add_device_title'), font=ctk.CTkFont(size=22, weight="bold"), text_color=RENKLER["text"]).pack(pady=(0, 5))
        
        form_frame = ctk.CTkFrame(main_frame, fg_color=RENKLER["frame"], corner_radius=10)
        form_frame.pack(fill="both", expand=True, padx=10, pady=15)
        
        ctk.CTkLabel(form_frame, text=lang_manager.get_text('device_name'), anchor="w", font=ctk.CTkFont(size=13, weight="bold"), text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(20, 5))
        ad_entry = ctk.CTkEntry(form_frame, placeholder_text=lang_manager.get_text('device_name_placeholder'), height=40)
        ad_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text=lang_manager.get_text('ip_address'), anchor="w", font=ctk.CTkFont(size=13, weight="bold"), text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(5, 5))
        ip_entry = ctk.CTkEntry(form_frame, placeholder_text=lang_manager.get_text('ip_placeholder'), height=40)
        ip_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text=lang_manager.get_text('mac_address'), anchor="w", font=ctk.CTkFont(size=13, weight="bold"), text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(5, 5))
        mac_entry = ctk.CTkEntry(form_frame, placeholder_text=lang_manager.get_text('mac_placeholder'), height=40)
        mac_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        def ekle():
            ad = ad_entry.get().strip()
            ip = ip_entry.get().strip()
            mac = mac_entry.get().strip()
            
            if not ad:
                messagebox.showwarning(lang_manager.get_text('name_required').split('!')[0], lang_manager.get_text('name_required'))
                return
            if not ip:
                messagebox.showwarning(lang_manager.get_text('ip_required').split('!')[0], lang_manager.get_text('ip_required'))
                return
            if not self.validate_ip(ip):
                messagebox.showwarning(lang_manager.get_text('invalid_ip').split('!')[0], lang_manager.get_text('invalid_ip'))
                return
            if mac and not self.validate_mac(mac):
                messagebox.showwarning(lang_manager.get_text('invalid_mac').split('!')[0], lang_manager.get_text('invalid_mac'))
                return
            
            mac = self.format_mac(mac)
            
            if self.db.cihaz_ekle(ad, ip, mac):
                self.verileri_yukle()
                self.kartlari_guncelle()
                self.istatistikleri_guncelle()
                dialog.destroy()
                self.durum.configure(text=lang_manager.get_text('device_added', name=ad), text_color=RENKLER["success"])
            else:
                messagebox.showerror(lang_manager.get_text('ip_exists').split('!')[0], lang_manager.get_text('ip_exists'))
        
        OvalButton(form_frame, text=lang_manager.get_text('save'), command=ekle, height=45, font=ctk.CTkFont(size=14, weight="bold"), fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f").pack(fill="x", padx=20, pady=(10, 10))
        OvalButton(form_frame, text=lang_manager.get_text('cancel'), command=dialog.destroy, height=40, fg_color="transparent", hover_color=RENKLER["card_bg"], text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(0, 20))
    
    def cihaz_duzenle_dialog(self, cihaz):
        dialog = ctk.CTkToplevel(self.pencere)
        dialog.title(lang_manager.get_text('edit_device_title'))
        dialog.geometry("500x520")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (520 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=25)
        
        ctk.CTkLabel(main_frame, text=lang_manager.get_text('edit_device_title'), font=ctk.CTkFont(size=22, weight="bold"), text_color=RENKLER["text"]).pack(pady=(0, 5))
        
        form_frame = ctk.CTkFrame(main_frame, fg_color=RENKLER["frame"], corner_radius=10)
        form_frame.pack(fill="both", expand=True, padx=10, pady=15)
        
        ctk.CTkLabel(form_frame, text=lang_manager.get_text('device_name'), anchor="w", font=ctk.CTkFont(size=13, weight="bold"), text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(20, 5))
        ad_entry = ctk.CTkEntry(form_frame, height=40)
        ad_entry.insert(0, cihaz.ad)
        ad_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text=lang_manager.get_text('ip_address'), anchor="w", font=ctk.CTkFont(size=13, weight="bold"), text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(5, 5))
        ip_entry = ctk.CTkEntry(form_frame, height=40)
        ip_entry.insert(0, cihaz.ip)
        ip_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text=lang_manager.get_text('mac_address'), anchor="w", font=ctk.CTkFont(size=13, weight="bold"), text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(5, 5))
        mac_entry = ctk.CTkEntry(form_frame, height=40)
        mac_display = cihaz.mac if cihaz.mac != "Bilinmiyor" else ""
        mac_entry.insert(0, mac_display)
        mac_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        def kaydet():
            yeni_ad = ad_entry.get().strip()
            yeni_ip = ip_entry.get().strip()
            yeni_mac = mac_entry.get().strip()
            
            if not yeni_ad or not yeni_ip:
                messagebox.showwarning(lang_manager.get_text('name_ip_required').split('!')[0], lang_manager.get_text('name_ip_required'))
                return
            if not self.validate_ip(yeni_ip):
                messagebox.showwarning(lang_manager.get_text('invalid_ip').split('!')[0], lang_manager.get_text('invalid_ip'))
                return
            if yeni_mac and not self.validate_mac(yeni_mac):
                messagebox.showwarning(lang_manager.get_text('invalid_mac').split('!')[0], lang_manager.get_text('invalid_mac'))
                return
            
            yeni_mac = self.format_mac(yeni_mac) if yeni_mac else "Bilinmiyor"
            self.db.cihaz_guncelle(cihaz.id, yeni_ad, yeni_ip, yeni_mac)
            self.verileri_yukle()
            self.kartlari_guncelle()
            self.istatistikleri_guncelle()
            dialog.destroy()
            self.durum.configure(text=lang_manager.get_text('device_updated', name=yeni_ad), text_color=RENKLER["warning"])
        
        OvalButton(form_frame, text=lang_manager.get_text('save'), command=kaydet, height=45, font=ctk.CTkFont(size=14, weight="bold"), fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f").pack(fill="x", padx=20, pady=(10, 10))
        OvalButton(form_frame, text=lang_manager.get_text('cancel'), command=dialog.destroy, height=40, fg_color="transparent", hover_color=RENKLER["card_bg"], text_color=RENKLER["text"]).pack(fill="x", padx=20, pady=(0, 20))
    
    def cihaz_sil(self, cihaz):
        if messagebox.askyesno(lang_manager.get_text('delete_confirm', name=cihaz.ad).split('?')[0], lang_manager.get_text('delete_confirm', name=cihaz.ad)):
            self.db.cihaz_sil(cihaz.id, cihaz.ad)
            self.verileri_yukle()
            self.kartlari_guncelle()
            self.istatistikleri_guncelle()
            self.durum.configure(text=lang_manager.get_text('device_deleted', name=cihaz.ad), text_color=RENKLER["danger"])
    
    def cihaz_detay_goster(self, cihaz):
        detay_pencere = ctk.CTkToplevel(self.pencere)
        detay_pencere.title(lang_manager.get_text('detail'))
        detay_pencere.geometry("420x340")
        detay_pencere.resizable(False, False)
        detay_pencere.grab_set()
        
        detay_frame = ctk.CTkFrame(detay_pencere, fg_color=RENKLER["bg"])
        detay_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(detay_frame, text=lang_manager.get_text('detail'), font=ctk.CTkFont(size=20, weight="bold"), text_color=RENKLER["text"]).pack(pady=(0, 10))
        detay_metni = (
            f"{lang_manager.get_text('device_name')} {cihaz.ad}\n"
            f"{lang_manager.get_text('ip_address')} {cihaz.ip}\n"
            f"{lang_manager.get_text('mac_address')} {cihaz.mac}\n"
            f"{lang_manager.get_text('online') if cihaz.online else lang_manager.get_text('offline')}\n"
            f"{lang_manager.get_text('last_check', time=cihaz.son_kontrol or '-') }"
        )
        ctk.CTkLabel(detay_frame, text=detay_metni, font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"], justify="left").pack(fill="x", pady=(0, 15))
        OvalButton(detay_frame, text=lang_manager.get_text('close'), command=detay_pencere.destroy, width=120, fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f").pack(pady=(10, 0))
    
    def kartlari_guncelle(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        if not self.cihazlar:
            bos_label = ctk.CTkLabel(self.scrollable_frame, text=lang_manager.get_text('no_devices'), font=ctk.CTkFont(size=16), text_color=RENKLER["text_secondary"], justify="center")
            bos_label.pack(pady=50)
            return
        
        satir, sutun = 0, 0
        max_sutun = 4
        
        for cihaz in self.cihazlar:
            kart_rengi = RENKLER["card_online"] if cihaz.online else RENKLER["card_offline"]
            border_rengi = RENKLER["border_online"] if cihaz.online else RENKLER["border_offline"]
            
            kart = ctk.CTkFrame(self.scrollable_frame, fg_color=kart_rengi, corner_radius=15, border_width=2, border_color=border_rengi)
            kart.grid(row=satir, column=sutun, padx=10, pady=10, sticky="nsew")
            
            icerik = ctk.CTkFrame(kart, fg_color="transparent")
            icerik.pack(fill="both", expand=True, padx=15, pady=15)
            
            durum_rengi = RENKLER["success"] if cihaz.online else RENKLER["danger"]
            durum_text = lang_manager.get_text('online') if cihaz.online else lang_manager.get_text('offline')
            durum_label = ctk.CTkLabel(icerik, text=f"{'🟢' if cihaz.online else '🔴'} {durum_text}", font=ctk.CTkFont(size=12, weight="bold"), text_color=durum_rengi)
            durum_label.pack(anchor="ne")
            
            ctk.CTkLabel(icerik, text="💻" if cihaz.online else "📴", font=ctk.CTkFont(size=42)).pack(pady=(5, 0))
            ctk.CTkLabel(icerik, text=cihaz.ad, font=ctk.CTkFont(size=15, weight="bold"), text_color=RENKLER["text"]).pack(pady=(5, 0))
            ctk.CTkLabel(icerik, text=f"🌐 {cihaz.ip}", font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"]).pack()
            ctk.CTkLabel(icerik, text=f"🔌 {cihaz.mac}", font=ctk.CTkFont(size=9), text_color=RENKLER["text_secondary"]).pack(pady=(2, 0))
            
            if cihaz.son_kontrol:
                ctk.CTkLabel(icerik, text=f"⏱️ {cihaz.son_kontrol}", font=ctk.CTkFont(size=9), text_color=RENKLER["text_secondary"]).pack(pady=(5, 0))
            
            btn_frame = ctk.CTkFrame(icerik, fg_color="transparent")
            btn_frame.pack(fill="x", pady=(10, 0))
            
            OvalButton(btn_frame, text=lang_manager.get_text('edit'), width=90, height=32, command=lambda c=cihaz: self.cihaz_duzenle_dialog(c), fg_color=RENKLER["button_hover"], hover_color=RENKLER["button"], text_color="#0a0a0f", font=ctk.CTkFont(size=12)).pack(side="left", padx=3)
            OvalButton(btn_frame, text=lang_manager.get_text('refresh'), width=110, height=32, command=lambda c=cihaz: threading.Thread(target=self.cihaz_kontrol, args=(c,), daemon=True).start(), fg_color=RENKLER["button_hover"], hover_color=RENKLER["button"], text_color="#0a0a0f", font=ctk.CTkFont(size=12)).pack(side="left", padx=3)
            OvalButton(btn_frame, text=lang_manager.get_text('detail'), width=100, height=32, command=lambda c=cihaz: self.cihaz_detay_goster(c), fg_color=RENKLER["text_secondary"], hover_color=RENKLER["card_bg"], text_color=RENKLER["text"], font=ctk.CTkFont(size=12)).pack(side="left", padx=3)
            OvalButton(btn_frame, text=lang_manager.get_text('delete'), width=90, height=32, command=lambda c=cihaz: self.cihaz_sil(c), fg_color=RENKLER["danger"], hover_color=RENKLER["danger"], text_color="#ffffff", font=ctk.CTkFont(size=12)).pack(side="left", padx=3)
            
            sutun += 1
            if sutun >= max_sutun:
                sutun = 0
                satir += 1
        
        for i in range(max_sutun):
            self.scrollable_frame.grid_columnconfigure(i, weight=1)
    
    def istatistikleri_guncelle(self):
        toplam = len(self.cihazlar)
        online = sum(1 for c in self.cihazlar if c.online)
        self.toplam_cihaz_label.configure(text=lang_manager.get_text('total_devices', count=toplam))
        self.online_sayisi_label.configure(text=lang_manager.get_text('online_devices', count=online))
        self.offline_sayisi_label.configure(text=lang_manager.get_text('offline_devices', count=toplam - online))
    
    def yedek_al(self):
        if not self.cihazlar:
            messagebox.showwarning(lang_manager.get_text('no_devices_backup').split('!')[0], lang_manager.get_text('no_devices_backup'))
            return
        dosya = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("SQLite DB", "*.db")], initialfile=f"cihaz_yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        if dosya:
            import shutil
            shutil.copy2(self.db.db_file, dosya)
            self.durum.configure(text=lang_manager.get_text('backup_success'), text_color=RENKLER["success"])
            messagebox.showinfo(lang_manager.get_text('backup_saved').split('!')[0], lang_manager.get_text('backup_saved'))
    
    def verileri_export_et(self):
        if not self.cihazlar:
            messagebox.showwarning(lang_manager.get_text('no_devices_export').split('!')[0], lang_manager.get_text('no_devices_export'))
            return
        dosya = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV dosyası", "*.csv")], initialfile=f"ag_cihazlari_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if dosya:
            with open(dosya, 'w', encoding='utf-8-sig') as f:
                f.write(f"Ağ Cihazları Raporu,{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("Cihaz Adı,IP Adresi,MAC Adresi,Durum,Son Kontrol\n")
                for c in self.cihazlar:
                    f.write(f"{c.ad},{c.ip},{c.mac},{'Online' if c.online else 'Offline'},{c.son_kontrol or '-'}\n")
            self.durum.configure(text=lang_manager.get_text('export_success'), text_color=RENKLER["success"])
            messagebox.showinfo(lang_manager.get_text('file_saved').split('!')[0], lang_manager.get_text('file_saved'))
    
    def hakkinda_goster(self):
        about = ctk.CTkToplevel(self.pencere)
        about.title(lang_manager.get_text('about'))
        about.geometry("500x400")
        about.resizable(False, False)
        about.grab_set()
        
        about.update_idletasks()
        x = (about.winfo_screenwidth() // 2) - (500 // 2)
        y = (about.winfo_screenheight() // 2) - (400 // 2)
        about.geometry(f"+{x}+{y}")
        
        main = ctk.CTkFrame(about, fg_color=RENKLER["bg"])
        main.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(main, text=lang_manager.get_text('about_title'), font=ctk.CTkFont(size=24, weight="bold"), text_color=RENKLER["text"]).pack(pady=(0, 5))
        ctk.CTkLabel(main, text=lang_manager.get_text('about_subtitle'), font=ctk.CTkFont(size=12), text_color=RENKLER["text_secondary"]).pack()
        ctk.CTkLabel(main, text=lang_manager.get_text('about_version'), font=ctk.CTkFont(size=12), text_color=RENKLER["text"], justify="center").pack()
        
        ctk.CTkLabel(main, text=lang_manager.get_text('about_contact'), font=ctk.CTkFont(size=11), text_color=RENKLER["text_secondary"]).pack()
        OvalButton(main, text=lang_manager.get_text('close'), command=about.destroy, width=120, fg_color=RENKLER["button"], hover_color=RENKLER["button_hover"], text_color="#0a0a0f").pack(pady=(20, 0))
    
    def kapat(self):
        self.izleme_aktif = False
        if self.izleme_thread and self.izleme_thread.is_alive():
            self.izleme_thread.join(timeout=3)
        logger.info("Uygulama kapatıldı")
        self.pencere.destroy()
    
    def calistir(self):
        self.pencere.mainloop()

if __name__ == "__main__":
    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
    
    logger.info("=" * 50)
    logger.info("UYGULAMA BAŞLATILDI")
    logger.info("=" * 50)
    
    app = AgIzlemeUygulamasi()
    app.calistir()
