import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import date

VILLES = ["Fès", "Casablanca", "Rabat", "Marrakech", "Tanger", "Meknès", "Agadir", "Oujda"]


window = tk.Tk()
window.title("Gestion de Réservations")
window.geometry("750x550")


menu = tk.Frame(window, width=120, bg="#f0f0f0")
menu.pack(side="left", fill="y")

conteneur = tk.Frame(window)
conteneur.pack(side="right", fill="both", expand=True)


accueil = tk.Frame(conteneur)
reservation = tk.Frame(conteneur)
prereservation = tk.Frame(conteneur)
modification = tk.Frame(conteneur)


for page in (accueil, reservation, prereservation, modification):
    page.grid(row=0, column=0, sticky="nsew")

def afficher(page):
    page.tkraise()


tk.Label(accueil, text="Bienvenue sur l'application", font=("Arial", 25)).pack(pady=100)
tk.Label(accueil, text="Sélectionnez une option dans le menu à gauche.", font=("Arial", 12)).pack()



tk.Label(reservation, text="Nouvelle Réservation", font=("Arial", 18)).pack(pady=10)

formulaire = tk.Frame(reservation)
formulaire.pack(pady=10)

# Départ
tk.Label(formulaire, text="Départ", bg="green", fg="white", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=10)
depart = ttk.Combobox(formulaire, values=VILLES, state="readonly", width=18)
depart.grid(row=1, column=0, padx=10, pady=(0, 15))

# Bouton inverser
def inverser():
    d, a = depart.get(), arrivee.get()
    depart.set(a)
    arrivee.set(d)

tk.Button(formulaire, text="⇄", command=inverser).grid(row=1, column=1, pady=(0, 15))

# Arrivée
tk.Label(formulaire, text="Arrivée", bg="green", fg="white", font=("Arial", 11)).grid(row=0, column=2, sticky="w", padx=10)
arrivee = ttk.Combobox(formulaire, values=VILLES, state="readonly", width=18)
arrivee.grid(row=1, column=2, padx=10, pady=(0, 15))

# Date
tk.Label(formulaire, text="Date du voyage", bg="green", fg="white", font=("Arial", 11)).grid(row=2, column=0, sticky="w", padx=10)
date_entry = DateEntry(formulaire, date_pattern="dd/mm/yyyy", mindate=date.today(), width=17)
date_entry.grid(row=3, column=0, padx=10, pady=(0, 15))

# Nombre de places
tk.Label(formulaire, text="Nombre de places", bg="green", fg="white", font=("Arial", 11)).grid(row=2, column=2, sticky="w", padx=10)
places = ttk.Spinbox(formulaire, from_=1, to=10, width=17, state="readonly")
places.set(1)
places.grid(row=3, column=2, padx=10, pady=(0, 15))

# Résultat Réservation
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
    
    donnees = {
        "depart": d,
        "arriver": a,
        "date": date_entry.get(),
        "places": int(places.get())
    }

    with open("reservation.json", "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=4)
        
    resultat.config(text=f"Réservation enregistrée :\n{d} → {a}\nLe {date_entry.get()} • {places.get()} place(s)")

tk.Button(reservation, text="Valider la réservation", width=20, command=valider).pack(pady=5)



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
        
    donnees_pre = {
        "client": n,
        "depart": d,
        "arriver": a,
        "date": date_pre.get(),
        "places": int(places_pre.get()),
        "statut": "En attente de confirmation"
    }

    with open("prereservations.json", "w", encoding="utf-8") as f:
        json.dump(donnees_pre, f, ensure_ascii=False, indent=4)
        
    resultat_pre.config(text=f"Pré-réservation bloquée pour {n} :\n{d} → {a} le {date_pre.get()}")

tk.Button(prereservation, text="Mettre en attente", width=20, command=valider_prereservation).pack(pady=5)



tk.Label(modification, text="Modifier une date de réservation", font=("Arial", 18)).pack(pady=10)

details_actuels = tk.Label(modification, text="Cliquez sur 'Charger' pour voir votre réservation.", bg="#0078D7", fg="white", font=("Arial", 11), width=45, height=3)
details_actuels.pack(pady=10)

form_mod = tk.Frame(modification)
form_mod.pack(pady=10)

tk.Label(form_mod, text="Nouvelle date :", font=("Arial", 11)).grid(row=0, column=0, padx=10)
nouvelle_date = DateEntry(form_mod, date_pattern="dd/mm/yyyy", mindate=date.today(), width=15)
nouvelle_date.grid(row=0, column=1, padx=10)

def charger_reservation():
    try:
        with open("reservation.json", "r", encoding="utf-8") as f:
            donnees = json.load(f)
        details_actuels.config(
            text=f"Trajet : {donnees['depart']} → {donnees['arriver']}\n"
                 f"Date actuelle : {donnees['date']} | {donnees['places']} place(s)"
        )
    except FileNotFoundError:
        messagebox.showerror("Erreur", "Aucune réservation trouvée. Veuillez d'abord réserver.")

def enregistrer_modification():
    try:
        with open("reservation.json", "r", encoding="utf-8") as f:
            donnees = json.load(f)
            
        donnees["date"] = nouvelle_date.get()
        
        with open("reservation.json", "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=4)
            
        messagebox.showinfo("Succès", f"Date modifiée avec succès pour le {donnees['date']}.")
        charger_reservation() 
    except FileNotFoundError:
        messagebox.showerror("Erreur", "Impossible de modifier : aucune réservation existante.")

tk.Button(modification, text="1. Charger la réservation", width=25, command=charger_reservation).pack(pady=5)
tk.Button(modification, text="2. Enregistrer la nouvelle date", width=25, command=enregistrer_modification).pack(pady=5)



tk.Label(menu, text="Menu", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=20)

tk.Button(menu, text="Accueil", width=13, command=lambda: afficher(accueil)).pack(pady=5)
tk.Button(menu, text="Réservation", width=13, command=lambda: afficher(reservation)).pack(pady=5)
tk.Button(menu, text="Pré-réservation", width=13, command=lambda: afficher(prereservation)).pack(pady=5)
tk.Button(menu, text="Modifier Date", width=13, command=lambda: afficher(modification)).pack(pady=5)



afficher(accueil)


window.mainloop()