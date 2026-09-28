import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import date

VILLES = ["Fès", "Casablanca", "Rabat", "Marrakech","Tanger",
           "Meknès", "Agadir", "Oujda"]

window = tk.Tk()
window.title("Ma Fenetre")
window.geometry("700x450")


menu = tk.Frame(window,width=120)
menu.pack(side="left", fill ="y")

conteneur = tk.Frame(window)
conteneur.pack(side="right",fill="both",expand=True)

accueil = tk.Frame(conteneur)
reservation = tk.Frame(conteneur)
prereservation = tk.Frame(conteneur)

formulaire = tk.Frame(reservation)
formulaire.pack(pady=10)

tk.Label(formulaire, text="Départ", bg="green", fg="white",
         font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=10)
depart = ttk.Combobox(formulaire, values=VILLES, state="readonly", width=18)
depart.grid(row=1, column=0, padx=10, pady=(0, 15))

# Arrivée
tk.Label(formulaire, text="Arrivée", bg="green", fg="white",
         font=("Arial", 11)).grid(row=0, column=2, sticky="w", padx=10)
arrivee = ttk.Combobox(formulaire, values=VILLES, state="readonly", width=18)
arrivee.grid(row=1, column=2, padx=10, pady=(0, 15))

def inverser():
    d, a = depart.get(), arrivee.get()
    depart.set(a)
    arrivee.set(d)

tk.Button(formulaire, text="⇄", command=inverser).grid(row=1, column=1, pady=(0, 15))

# Date
tk.Label(formulaire, text="Date du voyage", bg="green", fg="white",
         font=("Arial", 11)).grid(row=2, column=0, sticky="w", padx=10)
date_entry = DateEntry(formulaire, date_pattern="dd/mm/yyyy",
                       mindate=date.today(), width=17)
date_entry.grid(row=3, column=0, padx=10, pady=(0, 15))

# Nombre de places
tk.Label(formulaire, text="Nombre de places", bg="green", fg="white",
         font=("Arial", 11)).grid(row=2, column=2, sticky="w", padx=10)
places = ttk.Spinbox(formulaire, from_=1, to=10, width=17, state="readonly")
places.set(1)
places.grid(row=3, column=2, padx=10, pady=(0, 15))

# Message de résultat
resultat = tk.Label(reservation, text="", bg="green", fg="white",
                    font=("Arial", 12))
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
        "depart" : d,
        "arriver" : a,
        "date" : date_entry.get(),
        "places": int(places.get())
    }

    with open("reservation.json","w",encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=4)
        
    resultat.config(
        text=f"Réservation enregistrée :\n{d} → {a}\n"
             f"Le {date_entry.get()} • {places.get()} place(s)"
    )

    

tk.Button(reservation, text="Valider", width=15, command=valider).pack(pady=5)


for page in (accueil, reservation, prereservation):
    page.grid(row=0, column=0, sticky="nsew")

def afficher(page):
    page.tkraise()

bonton1 = tk.Button(
    menu,
    text="Acceuil",
    width=10,command=lambda: afficher(accueil)
)

bonton2 = tk.Button(
    menu,
    text="Reservation",
    width=10,command=lambda: afficher(reservation)
)
bonton3 = tk.Button(
    menu,
    text="Prereservation",
    width=10,command=lambda: afficher(prereservation)
)


bonton1.pack(pady=5)
bonton2.pack(pady=5)
bonton3.pack(pady=5)

tk.Label(
    accueil,
    text="Bienvenue sur l'accueil",
    font=("Arial", 25)
).pack(pady=100)

tk.Label(
    reservation,
    text="ma reservation",
    font=("Arial", 25)
).pack(pady=100)

tk.Label(
    prereservation,
    text="prereservation",
    font=("Arial", 25)
).pack(pady=100)


afficher(accueil)

window.mainloop()