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
from datetime import datetime, timedelta, date


VILLES = ["Fès", "Casablanca", "Rabat", "Marrakech", "Tanger", "Meknès", "Agadir", "Oujda"]

FICHIER_RESERVATIONS = "reservation.json"
FICHIER_NOTIFICATIONS = "notifications.json"
FICHIER_ABONNEMENTS = "abonnements.json" # US7
CAPACITE_BUS = 50 # US7 : nombre de places d'un bus
SEUIL_DERNIERES_PLACES = 5

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
    verifier_alertes()

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

def charger_abonnements():
    if not os.path.exists(FICHIER_ABONNEMENTS):
        return []
    try:
        with open(FICHIER_ABONNEMENTS, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

def sauvegarder_abonnements(liste):
    with open(FICHIER_ABONNEMENTS, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=4)

def places_disponibles(depart_v, arrivee_v, date_v):
    # Places libres d'un trajet = capacité du bus - places des réservations non annulées
    total = 0
    for r in charger_reservations():
        if r.get("depart") == depart_v and r.get("arriver") == arrivee_v and r.get("date") == date_v:
            if not str(r.get("statut", "Confirmé")).startswith("Annulé"):
                total += int(r.get("places", 0))
    return max(0, CAPACITE_BUS - total)

def ajouter_abonnement(client, depart_v, arrivee_v, date_v):
    # Retourne "ok", "deja" (déjà abonné) ou "complet" (trajet plein : aucune baisse possible)
    abonnements = charger_abonnements()
    for a in abonnements:
        if a["client"].lower() == client.lower() and a["depart"] == depart_v and a["arriver"] == arrivee_v and a["date"] == date_v:
            return "deja"
    dispo = places_disponibles(depart_v, arrivee_v, date_v)
    if dispo <= 0:
        return "complet"
    abonnements.append({"client": client, "depart": depart_v, "arriver": arrivee_v, "date": date_v, "places_connues": dispo})
    sauvegarder_abonnements(abonnements)
    return "ok"

def message_alerte(a, restantes):
    trajet = f"{a['depart']} → {a['arriver']} du {a['date']}"
    if restantes <= 0:
        return f"Alerte places : le trajet {trajet} est désormais COMPLET."
    if restantes <= SEUIL_DERNIERES_PLACES:
        return f"Alerte places : plus que {restantes} place(s) sur le trajet {trajet}. Dépêchez-vous, dernières places !"
    return f"Alerte places : il reste {restantes} place(s) sur le trajet {trajet}."

def verifier_alertes():
    # À appeler après chaque changement de réservation (nouvelle réservation, annulation...)
    # Compare les places actuelles à celles que chaque abonné connaît :
    #   baisse -> notification + popup ; hausse (annulation) -> simple mise à jour
    abonnements = charger_abonnements()
    nouvelles = []
    modifie = False

    for a in abonnements:
        actuel = places_disponibles(a["depart"], a["arriver"], a["date"])
        connu = a.get("places_connues", actuel)
        if actuel == connu:
            continue
        a["places_connues"] = actuel
        modifie = True
        if actuel < connu:
            notif = {
                "date": date.today().strftime("%d/%m/%Y"),
                "message": message_alerte(a, actuel),
                "statut": "Non lu",
                "client": a["client"]
            }
            sauvegarder_notification(notif)
            nouvelles.append(notif)

    if modifie:
        sauvegarder_abonnements(abonnements)

    if nouvelles:
        texte = "\n\n".join(f"{n['client']} : {n['message']}" for n in nouvelles)
        reponse = messagebox.askyesno("⚠️ Alerte places", texte + "\n\nVoir les notifications ?")
        if reponse:
            afficher_notifications_page()
    return nouvelles

def verifier_alertes_manuel():
    nouvelles = verifier_alertes()
    if not nouvelles:
        messagebox.showinfo("Alertes places", "Aucune baisse du nombre de places détectée.")
    afficher_abonnements()

def maj_info_places(event=None):
    d, a, j = depart_alerte.get(), arrivee_alerte.get(), date_alerte.get()
    if not d or not a or d == a:
        info_places.config(text="Choisissez un trajet pour voir les places disponibles.", fg="black")
        return
    dispo = places_disponibles(d, a, j)
    couleur = "red" if dispo <= SEUIL_DERNIERES_PLACES else "green"
    info_places.config(text=f"Places disponibles : {dispo} / {CAPACITE_BUS}", fg=couleur)

def afficher_abonnements():
    for ligne in tableau_alertes.get_children():
        tableau_alertes.delete(ligne)
    abonnements = charger_abonnements()
    for i, a in enumerate(abonnements, start=1):
        restantes = places_disponibles(a["depart"], a["arriver"], a["date"])
        tableau_alertes.insert("", "end", values=(i, a["client"], a["depart"], a["arriver"], a["date"], restantes))
    nb_abonnements.config(text=f"{len(abonnements)} abonnement(s)")
    maj_info_places()

def ouvrir_alertes():
    afficher_abonnements()   # relit les fichiers à chaque ouverture
    afficher(alertes_page)

def s_abonner_alertes():
    nom = nom_alerte.get().strip()
    d, a, j = depart_alerte.get(), arrivee_alerte.get(), date_alerte.get()
    if not nom or not d or not a:
        messagebox.showwarning("Champs manquants", "Veuillez remplir le nom, le départ et l'arrivée.")
        return
    if d == a:
        messagebox.showwarning("Trajet invalide", "Le départ et l'arrivée doivent être différents.")
        return
    etat = ajouter_abonnement(nom, d, a, j)
    if etat == "complet":
        messagebox.showwarning("Trajet complet", "Ce trajet est déjà complet : aucune baisse possible, alerte inutile.")
        return
    if etat == "deja":
        messagebox.showinfo("Déjà abonné", "Vous êtes déjà abonné aux alertes de ce trajet.")
        return
    resultat_alerte.config(text=f"Alertes activées pour {nom} :\n{d} → {a} • {j}")
    afficher_abonnements()

def se_desabonner_alertes():
    selection = tableau_alertes.selection()
    if not selection:
        messagebox.showwarning("Sélection", "Sélectionnez un abonnement à supprimer.")
        return
    index = int(tableau_alertes.item(selection[0])["values"][0]) - 1
    abonnements = charger_abonnements()
    if index < 0 or index >= len(abonnements):
        return
    a = abonnements.pop(index)
    sauvegarder_abonnements(abonnements)
    resultat_alerte.config(text=f"Alertes désactivées :\n{a['depart']} → {a['arriver']} • {a['date']}")
    afficher_abonnements()

def simuler_reservation_alertes():
    # Simule une réservation sur le trajet choisi pour tester les alertes (comme le bouton US9)
    d, a, j = depart_alerte.get(), arrivee_alerte.get(), date_alerte.get()
    if not d or not a:
        messagebox.showwarning("Champs manquants", "Choisissez un départ et une arrivée.")
        return
    if d == a:
        messagebox.showwarning("Trajet invalide", "Le départ et l'arrivée doivent être différents.")
        return
    nb = int(places_sim.get())
    dispo = places_disponibles(d, a, j)
    if nb > dispo:
        messagebox.showwarning("Plus de places", f"Seulement {dispo} place(s) disponible(s) sur ce trajet.")
        return
    reservations = charger_reservations()
    reservations.append({"depart": d, "arriver": a, "date": j, "places": nb, "statut": "Confirmé"})
    sauvegarder_reservations(reservations)
    nouvelles = verifier_alertes()
    afficher_abonnements()
    if not nouvelles:
        messagebox.showinfo("Simulation", "Réservation simulée. Aucun abonné à alerter.")



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
alertes_page = tk.Frame(conteneur)

for page in (accueil, reservation, prereservation, suivi, consultation, notifications_page,alertes_page):
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
    verifier_alertes()

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




tk.Label(alertes_page, text="Alertes - Places disponibles", font=("Arial", 18)).pack(pady=10)

form_alerte = tk.Frame(alertes_page)
form_alerte.pack(pady=5)

tk.Label(form_alerte, text="Nom du client", bg="#0078D7", fg="white", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=10)
nom_alerte = tk.Entry(form_alerte, width=20)
nom_alerte.grid(row=1, column=0, padx=10, pady=(0, 10))

tk.Label(form_alerte, text="Date du voyage", bg="#0078D7", fg="white", font=("Arial", 11)).grid(row=0, column=1, sticky="w", padx=10)
date_alerte = DateEntry(form_alerte, date_pattern="dd/mm/yyyy", mindate=date.today(), width=17)
date_alerte.grid(row=1, column=1, padx=10, pady=(0, 10))

tk.Label(form_alerte, text="Départ", bg="#0078D7", fg="white", font=("Arial", 11)).grid(row=2, column=0, sticky="w", padx=10)
depart_alerte = ttk.Combobox(form_alerte, values=VILLES, state="readonly", width=18)
depart_alerte.grid(row=3, column=0, padx=10, pady=(0, 10))

tk.Label(form_alerte, text="Arrivée", bg="#0078D7", fg="white", font=("Arial", 11)).grid(row=2, column=1, sticky="w", padx=10)
arrivee_alerte = ttk.Combobox(form_alerte, values=VILLES, state="readonly", width=18)
arrivee_alerte.grid(row=3, column=1, padx=10, pady=(0, 10))

depart_alerte.bind("<<ComboboxSelected>>", maj_info_places)
arrivee_alerte.bind("<<ComboboxSelected>>", maj_info_places)
date_alerte.bind("<<DateEntrySelected>>", maj_info_places)

info_places = tk.Label(alertes_page, text="Choisissez un trajet pour voir les places disponibles.", font=("Arial", 11))
info_places.pack(pady=2)

resultat_alerte = tk.Label(alertes_page, text="", bg="#0078D7", fg="white", font=("Arial", 11))
resultat_alerte.pack(pady=2)

actions_alerte = tk.Frame(alertes_page)
actions_alerte.pack(pady=5)
tk.Button(actions_alerte, text="M'alerter quand les places diminuent", bg="#0078D7", fg="white", command=s_abonner_alertes).grid(row=0, column=0, padx=10)
tk.Button(actions_alerte, text="Vérifier les alertes", command=verifier_alertes_manuel).grid(row=0, column=1, padx=10)

colonnes_a = ("n", "client", "depart", "arrivee", "date", "places")
tableau_alertes = ttk.Treeview(alertes_page, columns=colonnes_a, show="headings", height=5)
for c, t, w in [("n","N°",40),("client","Client",100),("depart","Départ",90),("arrivee","Arrivée",90),("date","Date",90),("places","Places restantes",130)]:
    tableau_alertes.heading(c, text=t)
    tableau_alertes.column(c, width=w, anchor="center")
tableau_alertes.pack(fill="both", expand=True, padx=10, pady=5)

nb_abonnements = tk.Label(alertes_page, text="", font=("Arial", 11))
nb_abonnements.pack(pady=2)

tk.Button(alertes_page, text="Ne plus m'alerter (abonnement sélectionné)", command=se_desabonner_alertes).pack(pady=2)

# BOUTON DE TEST US7 ICI
simulation_alerte = tk.Frame(alertes_page)
simulation_alerte.pack(pady=8)
tk.Label(simulation_alerte, text="Test : réserver").grid(row=0, column=0, padx=5)
places_sim = ttk.Spinbox(simulation_alerte, from_=1, to=10, width=5, state="readonly")
places_sim.set(1)
places_sim.grid(row=0, column=1, padx=5)
tk.Label(simulation_alerte, text="place(s)").grid(row=0, column=2, padx=5)
tk.Button(simulation_alerte, text=" Simuler une réservation ", bg="red", fg="white", command=simuler_reservation_alertes).grid(row=0, column=3, padx=10)

# ---------- 7) Menu : à coller juste avant le bouton " Notifications " ----------








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
    ajouter_abonnement(n, d, a, date_pre.get())

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
map_widget.set_tile_server(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    max_zoom=19
)
map_widget.pack(fill="both", expand=True, padx=10, pady=10)
map_widget.set_position(34.0333, -5.0000)
map_widget.set_zoom(15)

map_widget.set_position(34.0333, -5.0000)
map_widget.set_zoom(13)
bus_marker = map_widget.set_marker(34.0333, -5.0000, text="🚌 BUS-001")
tk.Label(
    suivi,
    text="© OpenStreetMap contributors © CARTO",
    font=("Arial", 8)
).pack()


# Trajet virtuel du bus
trajet = [
    (34.0333, -5.0000),
    (34.0340, -4.9995),
    (34.0348, -4.9988),
    (34.0355, -4.9980),
    (34.0362, -4.9970),
    (34.0370, -4.9960),
    (34.0380, -4.9950),
    (34.0390, -4.9940),
    (34.0400, -4.9930)
]

indice = 0


def simuler_deplacement():

    global indice

    lat, lon = trajet[indice]

    bus_marker.set_position(lat, lon)
    map_widget.set_position(lat, lon)

    print(f"Bus position : {lat}, {lon}")

    # Passer à la prochaine position
    indice = (indice + 1) % len(trajet)

    # Attendre 2 secondes avant le prochain déplacement
    suivi.after(2000, simuler_deplacement)

simuler_deplacement()

def mettre_a_jour_bus(lat, lon):
    bus_marker.set_position(lat, lon)
    map_widget.set_position(lat, lon)

async def recevoir_positions():
    uri = "ws://localhost:8000/ws"

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connecté au serveur WebSocket")

            while True:
                message = await websocket.recv()
                donnees = json.loads(message)

                lat = float(donnees["latitude"])
                lon = float(donnees["longitude"])

                print(f"📍 Position reçue : {lat}, {lon}")

                # Mise à jour de Tkinter depuis son thread principal
                window.after(
                    0,
                    mettre_a_jour_bus,
                    lat,
                    lon
                )

    except Exception as e:
        print(f"❌ Erreur WebSocket : {e}")


def lancer_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(recevoir_positions())


thread_ws = threading.Thread(
    target=lancer_websocket,
    daemon=True
)
thread_ws.start()

# Menu
tk.Button(menu, text="Accueil", width=15, height=2, command=lambda: afficher(accueil)).pack(pady=5)
tk.Button(menu, text="Reservation", width=15, height=2, command=lambda: afficher(reservation)).pack(pady=5)
tk.Button(menu, text="Prereservation", width=15, height=2, command=lambda: afficher(prereservation)).pack(pady=5)
tk.Button(menu, text="Consulter", width=15, height=2, command=ouvrir_consultation).pack(pady=5)
tk.Button(menu, text="Suivi du bus", width=15, height=2, command=lambda: afficher(suivi)).pack(pady=5)
tk.Button(menu, text="Alertes places", width=15, height=2, command=ouvrir_alertes).pack(pady=5)
tk.Button(menu, text=" Notifications ", width=15, height=2, bg="#ffcccc", command=afficher_notifications_page).pack(pady=20)

afficher(accueil)
window.mainloop()