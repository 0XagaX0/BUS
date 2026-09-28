import tkinter as tk
window = tk.Tk()
window.title("Ma Fenetre")
window.geometry("400x300")

def bonjour():
    print("Bonjour")

menu = tk.Frame(window)
menu.pack(side="left", fill ="y")


bonton1 = tk.Button(
    menu,
    text="CLICK",
    width=10
)

bonton2 = tk.Button(
    menu,
    text="CLICK",
    width=10
)
bonton3 = tk.Button(
    menu,
    text="CLICK",
    width=10
)
bonton4 = tk.Button(
    menu,
    text="CLICK",
    width=10
)
bonton5 = tk.Button(
    menu,
    text="CLICK",
    width=10
)

bonton1.pack(pady=5)
bonton2.pack(pady=5)
bonton3.pack(pady=5)
bonton4.pack(pady=5)
bonton5.pack(pady=5)


window.mainloop()