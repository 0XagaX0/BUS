import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkintermapview import TkinterMapView
from tkcalendar import DateEntry
from datetime import date
import threading
import asyncio
import websockets
import os

VILLES = ["Fès", "Casablanca", "Rabat", "Marrakech", "Tanger", "Meknès", "Agadir", "Oujda"]

FICHIER_RESERVATIONS = "reservation.json"
FICHIER_NOTIFICATIONS = "notifications.json"

# ========== UTILS JSON ==========
def charger_reservations():
    if not os.path.exists(FICHIER_RESERVATIONS):
        return []
    try:
        with open(FICHIER_RESERVATIONS, "r", encoding="utf-8") as f:
            contenu = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
    if isinstance(contenu, dict):
        return [contenu]
    return contenu

def sauvegarder_reservations(liste):
    with open(FICHIER_RESERVATIONS, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

def charger_notifications():
    if not os.path.exists(FICHIER_NOTIFICATIONS):
        return []
    try:
        with open(FICHIER_NOTIFICATIONS, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def sauvegarder_notification(notif):
    notifs = charger_notifications()
    notifs.append(notif)
    with open(FICHIER_NOTIFICATIONS, "w", encoding="utf-8") as f:
        json.dump(notifs, f, ensure_ascii=False, indent=4)

# ========== WINDOW UNIQUE ==========
window = tk.Tk()
window.title("Gestion de Réservations - BUS")
window.geometry("850x600")

menu = tk.Frame(window, width=150, bg="#f0f0f0")
menu.pack(side="left", fill="y")
conteneur = tk.Frame(window)
conteneur.pack(side="right", fill="both", expand=True)

accueil = tk.Frame(conteneur)
reservation = tk.Frame(conteneur)
prereservation = tk.Frame(conteneur)
suivi = tk.Frame(conteneur)
consultation = tk.Frame(conteneur)
notifications_page = tk.Frame(conteneur) # US9

for page in (accueil, reservation, prereservation, suivi, consultation, notifications_page):
    page.grid(row=0, column=0, sticky="nsew")

def afficher(page):
    page.tkraise()

# ========== US9 - LOGIQUE ANNULATION ==========
def demander_remboursement():
    messagebox.showinfo("Remboursement", "Demande de remboursement envoyée. Vous serez remboursé sous 48h.")
    # ici on pourrait changer statut
    afficher(consultation)

def choisir_autre_reservation():
    messagebox.showinfo("Nouvelle réservation", "Redirection vers la page réservation.")
    afficher(reservation)

def afficher_notifications_page():
    for ligne in tableau_notif.get_children():
        tableau_notif.delete(ligne)
    notifs = charger_notifications()
    for n in notifs:
        tableau_notif.insert("", "end", values=(n.get("date"), n.get("message"), n.get("statut")))
    nb_notifs.config(text=f"{len(notifs)} notification(s)")
    afficher(notifications_page)

def annuler_trajet_compagnie():
    # US9 - Simule que la compagnie annule le trajet sélectionné
    selection = tableau.selection()
    if not selection:
        messagebox.showwarning("Sélection", "Sélectionnez une réservation à annuler (simulation compagnie).")
        return
    
    item = tableau.item(selection[0])
    index = int(item["values"][0]) - 1
    
    reservations = charger_reservations()
    if index < 0 or index >= len(reservations):
        return
    
    trajet = reservations[index]
    trajet["statut"] = "Annulé par la compagnie"
    sauvegarder_reservations(reservations)

    # Créer notification US9
    notif = {
        "date": date.today().strftime("%d/%m/%Y"),
        "message": f"Trajet {trajet['depart']} -> {trajet['arriver']} du {trajet['date']} ANNULE par la compagnie",
        "statut": "Non lu"
    }
    sauvegarder_notification(notif)
    
    # Afficher la popup US9 - Le coeur de la story
    afficher_reservations() # rafraichir
    
    reponse = messagebox.askyesnocancel(
        "Trajet Annulé par la compagnie",
        f"⚠️ INFORMATION IMPORTANTE\n\nVotre trajet {trajet['depart']} → {trajet['arriver']} du {trajet['date']} a été annulé par la compagnie.\n\nVoulez-vous demander un remboursement ?\n\nOUI = Remboursement\nNON = Choisir autre réservation\nANNULER = Voir plus tard"
    )
    
    if reponse is True:
        demander_remboursement()
    elif reponse is False:
        choisir_autre_reservation()
    else:
        afficher_notifications_page()

def afficher_reservations():
    for ligne in tableau.get_children():
        tableau.delete(ligne)
    reservations = charger_reservations()
    for i, r in enumerate(reservations, start=1):
        statut = r.get("statut", "Confirmé")
        tableau.insert("", "end", values=(i, r.get("depart",""), r.get("arriver",""), r.get("date",""), r.get("places",""), statut))
    nb_reservations.config(text=f"{len(reservations)} réservation(s)")

def ouvrir_consultation():
    afficher_reservations()
    afficher(consultation)

# ========== PAGES ==========
# Accueil
tk.Label(accueil, text="Bienvenue sur l'application", font=("Arial", 25)).pack(pady=100)
tk.Label(accueil, text="Sélectionnez une option dans le menu à gauche.", font=("Arial", 12)).pack()

# Réservation
tk.Label(reservation, text="Nouvelle Réservation", font=("Arial", 18)).pack(pady=10)
formulaire = tk.Frame(reservation)
formulaire.pack(pady=10)

tk.Label(formulaire, text="Départ", bg="green", fg="white", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=10)
depart = ttk.Combobox(formulaire, values=VILLES, state="readonly", width=18)
depart.grid(row=1, column=0, padx=10, pady=(0, 15))

def inverser():
    d, a = depart.get(), arrivee.get()
    depart.set(a)
    arrivee.set(d)

tk.Button(formulaire, text="⇄", command=inverser).grid(row=1, column=1, pady=(0, 15))

tk.Label(formulaire, text="Arrivée", bg="green", fg="white", font=("Arial", 11)).grid(row=0, column=2, sticky="w", padx=10)
arrivee = ttk.Combobox(formulaire, values=VILLES, state="readonly", width=18)
arrivee.grid(row=1, column=2, padx=10, pady=(0, 15))

tk.Label(formulaire, text="Date du voyage", bg="green", fg="white", font=("Arial", 11)).grid(row=2, column=0, sticky="w", padx=10)
date_entry = DateEntry(formulaire, date_pattern="dd/mm/yyyy", mindate=date.today(), width=17)
date_entry.grid(row=3, column=0, padx=10, pady=(0, 15))

tk.Label(formulaire, text="Nombre de places", bg="green", fg="white", font=("Arial", 11)).grid(row=2, column=2, sticky="w", padx=10)
places = ttk.Spinbox(formulaire, from_=1, to=10, width=17, state="readonly")
places.set(1)
places.grid(row=3, column=2, padx=10, pady=(0, 15))

resultat = tk.Label(reservation, text="", bg="green", fg="white", font=("Arial", 12))
resultat.pack(pady=5)

def valider():
    d, a = depart.get(), arrivee.get()
    if not d or not a:
        messagebox.showwarning("Champs manquants", "Choisissez un départ et une arrivée.")
        return
    if d == a:
        messagebox.showwarning("Trajet invalide", "Le départ et l'arrivée doivent être différents.")
        return
    donnees = {"depart": d, "arriver": a, "date": date_entry.get(), "places": int(places.get()), "statut": "Confirmé"}
    reservations = charger_reservations()
    reservations.append(donnees)
    sauvegarder_reservations(reservations)
    resultat.config(text=f"Réservation enregistrée :\n{d} → {a}\nLe {date_entry.get()} • {places.get()} place(s)")

tk.Button(reservation, text="Valider la réservation", width=20, command=valider).pack(pady=5)

# Pré-réservation
tk.Label(prereservation, text="Nouvelle Pré-réservation", font=("Arial", 18)).pack(pady=10)
form_pre = tk.Frame(prereservation)
form_pre.pack(pady=10)
tk.Label(form_pre, text="Nom du client", bg="orange", fg="white", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=10)
nom_client = tk.Entry(form_pre, width=20)
nom_client.grid(row=1, column=0, padx=10, pady=(0, 15))
tk.Label(form_pre, text="Départ", bg="orange", fg="white", font=("Arial", 11)).grid(row=2, column=0, sticky="w", padx=10)
depart_pre = ttk.Combobox(form_pre, values=VILLES, state="readonly", width=18)
depart_pre.grid(row=3, column=0, padx=10, pady=(0, 15))
tk.Label(form_pre, text="Arrivée", bg="orange", fg="white", font=("Arial", 11)).grid(row=2, column=1, sticky="w", padx=10)
arrivee_pre = ttk.Combobox(form_pre, values=VILLES, state="readonly", width=18)
arrivee_pre.grid(row=3, column=1, padx=10, pady=(0, 15))
tk.Label(form_pre, text="Date", bg="orange", fg="white", font=("Arial", 11)).grid(row=4, column=0, sticky="w", padx=10)
date_pre = DateEntry(form_pre, date_pattern="dd/mm/yyyy", mindate=date.today(), width=17)
date_pre.grid(row=5, column=0, padx=10, pady=(0, 15))
tk.Label(form_pre, text="Places", bg="orange", fg="white", font=("Arial", 11)).grid(row=4, column=1, sticky="w", padx=10)
places_pre = ttk.Spinbox(form_pre, from_=1, to=10, width=17, state="readonly")
places_pre.set(1)
places_pre.grid(row=5, column=1, padx=10, pady=(0, 15))
resultat_pre = tk.Label(prereservation, text="", bg="orange", fg="white", font=("Arial", 12))
resultat_pre.pack(pady=5)

def valider_prereservation():
    n = nom_client.get()
    d, a = depart_pre.get(), arrivee_pre.get()
    if not d or not a or not n:
        messagebox.showwarning("Champs manquants", "Veuillez remplir le nom, le départ et l'arrivée.")
        return
    if d == a:
        messagebox.showwarning("Trajet invalide", "Le départ et l'arrivée doivent être différents.")
        return
    donnees_pre = {"client": n, "depart": d, "arriver": a, "date": date_pre.get(), "places": int(places_pre.get()), "statut": "En attente"}
    with open("prereservations.json", "w", encoding="utf-8") as f:
        json.dump(donnees_pre, f, ensure_ascii=False, indent=4)
    resultat_pre.config(text=f"Pré-réservation bloquée pour {n} :\n{d} → {a} le {date_pre.get()}")

tk.Button(prereservation, text="Mettre en attente", width=20, command=valider_prereservation).pack(pady=5)

# Consultation
tk.Label(consultation, text="Mes réservations", font=("Arial", 18)).pack(pady=10)
colonnes = ("n", "depart", "arrivee", "date", "places", "statut")
tableau = ttk.Treeview(consultation, columns=colonnes, show="headings", height=10)
for c, t, w in [("n","N°",40),("depart","Départ",100),("arrivee","Arrivée",100),("date","Date",90),("places","Places",60),("statut","Statut",150)]:
    tableau.heading(c, text=t)
    tableau.column(c, width=w, anchor="center")
tableau.pack(fill="both", expand=True, padx=10, pady=5)
nb_reservations = tk.Label(consultation, text="", font=("Arial", 11))
nb_reservations.pack(pady=5)
# BOUTON US9 ICI
tk.Button(consultation, text=" Simuler Annulation Compagnie ", bg="red", fg="white", command=annuler_trajet_compagnie).pack(pady=10)

# Notifications 
tk.Label(notifications_page, text="Notifications - Annulations", font=("Arial", 18)).pack(pady=10)
colonnes_n = ("date", "message", "statut")
tableau_notif = ttk.Treeview(notifications_page, columns=colonnes_n, show="headings", height=10)
tableau_notif.heading("date", text="Date")
tableau_notif.heading("message", text="Message")
tableau_notif.heading("statut", text="Statut")
tableau_notif.column("date", width=100)
tableau_notif.column("message", width=400)
tableau_notif.column("statut", width=80)
tableau_notif.pack(fill="both", expand=True, padx=10, pady=5)
nb_notifs = tk.Label(notifications_page, text="", font=("Arial", 11))
nb_notifs.pack(pady=5)
frame_actions = tk.Frame(notifications_page)
frame_actions.pack(pady=10)
tk.Button(frame_actions, text="Demander Remboursement", bg="#0078D7", fg="white", width=20, command=demander_remboursement).grid(row=0, column=0, padx=10)
tk.Button(frame_actions, text="Nouvelle Réservation", bg="green", fg="white", width=20, command=choisir_autre_reservation).grid(row=0, column=1, padx=10)

# Suivi Bus
tk.Label(suivi, text="🚌 Suivi du bus en temps réel", font=("Arial", 20, "bold")).pack(pady=10)
map_widget = TkinterMapView(suivi, width=600, height=350)
map_widget.pack(fill="both", expand=True, padx=10, pady=10)
map_widget.set_position(34.0333, -5.0000)
map_widget.set_zoom(13)
bus_marker = map_widget.set_marker(34.0333, -5.0000, text="🚌 BUS-001")
def mettre_a_jour_bus(lat, lon):
    bus_marker.set_position(lat, lon)
    map_widget.set_position(lat, lon)

# Menu
tk.Button(menu, text="Accueil", width=15, height=2, command=lambda: afficher(accueil)).pack(pady=5)
tk.Button(menu, text="Reservation", width=15, height=2, command=lambda: afficher(reservation)).pack(pady=5)
tk.Button(menu, text="Prereservation", width=15, height=2, command=lambda: afficher(prereservation)).pack(pady=5)
tk.Button(menu, text="Consulter", width=15, height=2, command=ouvrir_consultation).pack(pady=5)
tk.Button(menu, text="Suivi du bus", width=15, height=2, command=lambda: afficher(suivi)).pack(pady=5)
tk.Button(menu, text=" Notifications ", width=15, height=2, bg="#ffcccc", command=afficher_notifications_page).pack(pady=20)

afficher(accueil)
window.mainloop()