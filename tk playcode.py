import tkinter as tk
from tkinter import messagebox, simpledialog
from basedatos import conectar, inicializar_db
from inventariotxt import cargar_inventario_txt
from main import Estudiante, Admin

def mostrar_inventario():
    inv = cargar_inventario_txt()
    if not inv:
        return "No hay inventario."
    texto = ""
    for cat, items in inv.items():
        texto += "\n[" + cat + "]\n"
        for nom, info in items.items():
            texto += "  " + nom + ": " + str(info["cantidad"])
            if info.get("unidad"):
                texto += " " + info["unidad"]
            texto += "\n"
    return texto


def hacer_login(ventana):
    v = tk.Toplevel(ventana)
    v.title("Login")
    v.geometry("300x260")
    v.grab_set()

    tk.Label(v, text="Tipo de usuario").pack(pady=5)
    rol = tk.StringVar(value="estudiante")
    tk.Radiobutton(v, text="Estudiante", variable=rol, value="estudiante").pack()
    tk.Radiobutton(v, text="Admin", variable=rol, value="admin").pack()

    tk.Label(v, text="Usuario").pack(pady=(10, 0))
    entrada_usuario = tk.Entry(v)
    entrada_usuario.pack()
    entrada_usuario.focus_set()

    tk.Label(v, text="Password").pack(pady=(10, 0))
    entrada_clave = tk.Entry(v, show="*")
    entrada_clave.pack()

    resultado = {"usuario": None}

    def entrar():
        usuario = entrada_usuario.get().strip()
        clave = entrada_clave.get().strip()
        if not usuario or not clave:
            messagebox.showerror("Error", "Completa los campos", parent=v)
            return
        con = conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT id, nombre FROM usuarios WHERE rol=? AND identificador=? AND password=?",
            (rol.get(), usuario, clave),
        )
        fila = cur.fetchone()
        con.close()
        if not fila:
            messagebox.showerror("Error", "Datos incorrectos", parent=v)
            return
        uid, nombre = fila
        if rol.get() == "estudiante":
            resultado["usuario"] = Estudiante(uid, nombre, usuario)
        else:
            resultado["usuario"] = Admin(uid, nombre)
        v.destroy()

    tk.Button(v, text="Entrar", command=entrar).pack(pady=15)
    v.bind("<Return>", lambda e: entrar())
    v.wait_window()
    return resultado["usuario"]


def ventana_estudiante(est):
    v = tk.Toplevel()
    v.title("Estudiante - " + est.nombre)
    v.geometry("800x600")

    def cerrar_sesion():
        v.destroy()
        iniciar()

    tk.Button(v, text="Cerrar sesion", command=cerrar_sesion, bg="white", fg="black").pack(pady=5)

    salida = tk.Text(v, wrap="word")
    salida.pack(fill="both", expand=True, padx=10, pady=10)

    def ver():
        salida.delete("1.0", "end")
        salida.insert("end", mostrar_inventario())

    def pedir():
        item = simpledialog.askstring("Pedir", "Nombre del item:", parent=v)
        if not item:
            return
        cant = simpledialog.askinteger("Pedir", "Cantidad:", parent=v)
        if not cant:
            return
        est.pedir(item.strip(), cant)
        ver()

    def devolver():
        item = simpledialog.askstring("Devolver", "Nombre del item:", parent=v)
        if not item:
            return
        cant = simpledialog.askinteger("Devolver", "Cantidad:", parent=v)
        if not cant:
            return
        est.devolver(item.strip(), cant)
        ver()

    def mis():
        salida.delete("1.0", "end")
        con = conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT item, cantidad, fecha FROM prestamos WHERE usuario_id=? ORDER BY fecha DESC",
            (est.id,),
        )
        filas = cur.fetchall()
        con.close()
        if not filas:
            salida.insert("end", "No tienes prestamos.")
            return
        salida.insert("end", "=== MIS PRESTAMOS ===\n")
        for nombre, cant, fecha in filas:
            salida.insert("end", str(cant) + " x " + nombre + "  (" + fecha + ")\n")

    barra = tk.Frame(v)
    barra.pack(fill="x", padx=10)
    tk.Button(barra, text="Ver inventario", command=ver).pack(side="left", padx=3)
    tk.Button(barra, text="Pedir", command=pedir).pack(side="left", padx=3)
    tk.Button(barra, text="Devolver", command=devolver).pack(side="left", padx=3)
    tk.Button(barra, text="Mis prestamos", command=mis).pack(side="left", padx=3)

    ver()

def ventana_admin(admin):
    v = tk.Toplevel()
    v.title("Admin - " + admin.nombre)
    v.geometry("800x600")

    def cerrar_sesion():
        v.destroy()
        iniciar()

    tk.Button(v, text="Cerrar sesion", command=cerrar_sesion, bg="white", fg="black").pack(pady=5)

    salida = tk.Text(v, wrap="word")
    salida.pack(fill="both", expand=True, padx=10, pady=10)

    def ver_inv():
        salida.delete("1.0", "end")
        salida.insert("end", mostrar_inventario())

    def ver_pres():
        salida.delete("1.0", "end")
        con = conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT p.item, p.cantidad, u.nombre, u.identificador, p.fecha "
            "FROM prestamos p JOIN usuarios u ON u.id=p.usuario_id ORDER BY p.fecha DESC"
        )
        filas = cur.fetchall()
        con.close()
        if not filas:
            salida.insert("end", "No hay prestamos.")
            return
        salida.insert("end", "=== PRESTAMOS ===\n")
        for item, cant, nom, ident, fecha in filas:
            salida.insert("end", str(cant) + " x " + item + " -> " + nom +
                          " (" + ident + ")  [" + fecha + "]\n")

    def ver_usr():
        salida.delete("1.0", "end")
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT nombre, rol, identificador FROM usuarios ORDER BY rol, nombre")
        filas = cur.fetchall()
        con.close()
        salida.insert("end", "=== USUARIOS ===\n")
        for nom, rol, ident in filas:
            salida.insert("end", "[" + rol + "] " + nom + " - " + ident + "\n")

    def stock():
        item = simpledialog.askstring("Stock", "Nombre del item:", parent=v)
        if not item:
            return
        cant = simpledialog.askinteger("Stock", "Cantidad a agregar:", parent=v)
        if not cant:
            return
        admin.agregar_stock(item.strip(), cant)
        ver_inv()

    def agregar_item():
        cat = simpledialog.askstring("Nuevo item", "Categoria:", parent=v)
        if not cat:
            return
        nom = simpledialog.askstring("Nuevo item", "Nombre:", parent=v)
        if not nom:
            return
        cant = simpledialog.askinteger("Nuevo item", "Cantidad:", parent=v)
        if not cant:
            return
        admin.agregar_item(cat.strip(), nom.strip(), cant)
        ver_inv()

    def eliminar_item():
        nom = simpledialog.askstring("Eliminar item", "Nombre:", parent=v)
        if nom:
            admin.eliminar_item(nom.strip())
            ver_inv()

    def agregar_usr():
        nom = simpledialog.askstring("Nuevo usuario", "Nombre:", parent=v)
        if not nom:
            return
        rol = simpledialog.askstring("Nuevo usuario", "Rol (estudiante/admin):", parent=v)
        if not rol:
            return
        ident = simpledialog.askstring("Nuevo usuario", "Codigo:", parent=v)
        if not ident:
            return
        pwd = simpledialog.askstring("Nuevo usuario", "Password:", show="*", parent=v)
        if not pwd:
            return
        admin.agregar_usuario(nom.strip(), rol.strip().lower(), ident.strip(), pwd)
        ver_usr()

    def eliminar_usr():
        ident = simpledialog.askstring("Eliminar usuario", "Codigo:", parent=v)
        if ident:
            admin.eliminar_usuario(ident.strip())
            ver_usr()

    barra1 = tk.Frame(v)
    barra1.pack(fill="x", padx=10)
    tk.Button(barra1, text="Ver inventario", command=ver_inv).pack(side="left", padx=3)
    tk.Button(barra1, text="Ver prestamos", command=ver_pres).pack(side="left", padx=3)
    tk.Button(barra1, text="Ver usuarios", command=ver_usr).pack(side="left", padx=3)

    barra2 = tk.Frame(v)
    barra2.pack(fill="x", padx=10, pady=5)
    tk.Button(barra2, text="Agregar stock", command=stock).pack(side="left", padx=3)
    tk.Button(barra2, text="Agregar item", command=agregar_item).pack(side="left", padx=3)
    tk.Button(barra2, text="Eliminar item", command=eliminar_item).pack(side="left", padx=3)
    tk.Button(barra2, text="Agregar usuario", command=agregar_usr).pack(side="left", padx=3)
    tk.Button(barra2, text="Eliminar usuario", command=eliminar_usr).pack(side="left", padx=3)

    ver_inv()

def iniciar():
    usuario = hacer_login(raiz)
    
    if usuario is None:
        raiz.destroy()
        return
        
    if isinstance(usuario, Estudiante):
        ventana_estudiante(usuario)
    else:
        ventana_admin(usuario)

inicializar_db()

raiz = tk.Tk()
raiz.withdraw() 

iniciar()
raiz.mainloop()