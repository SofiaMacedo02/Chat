import queue
import threading
import time
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from dotenv import load_dotenv
from google import genai

MODELO = "gemini-3.5-flash-lite"  # troque se quiser usar outro modelo

TEMAS = {
    "claro": {
        "bg": "#f5f5f5",
        "fg": "#1a1a1a",
        "botao_bg": "#e0e0e0",
        "botao_fg": "#1a1a1a",
        "entrada_bg": "#ffffff",
        "autor": "#1a5fb4",
    },
    "escuro": {
        "bg": "#1e1e1e",
        "fg": "#f5f5f5",
        "botao_bg": "#333333",
        "botao_fg": "#f5f5f5",
        "entrada_bg": "#2b2b2b",
        "autor": "#78aeed",
    },
}

tema_atual = "claro"

load_dotenv()
try:
    client = genai.Client()
except Exception as e:
    raise SystemExit(f"Erro ao iniciar o cliente (confira o .env): {e}")

fila = queue.Queue()


# ---------- Tema ----------
def aplicar_tema():
    c = TEMAS[tema_atual]
    root.config(bg=c["bg"])
    topo.config(bg=c["bg"])
    barra.config(bg=c["bg"])

    conversa.config(bg=c["entrada_bg"], fg=c["fg"], insertbackground=c["fg"])
    conversa.tag_config("autor", foreground=c["autor"])

    entrada.config(bg=c["entrada_bg"], fg=c["fg"], insertbackground=c["fg"])

    for b in (botao, botao_tema):
        b.config(bg=c["botao_bg"], fg=c["botao_fg"],
                 activebackground=c["botao_bg"],
                 activeforeground=c["botao_fg"],
                 disabledforeground="#888888")

    botao_tema.config(text="Tema escuro" if tema_atual == "claro" else "Tema claro")


def alternar_tema():
    global tema_atual
    tema_atual = "escuro" if tema_atual == "claro" else "claro"
    aplicar_tema()


# ---------- Gemini ----------
def consultar(pergunta):
    for tentativa in range(3):
        try:
            resposta = client.models.generate_content(model=MODELO, contents=pergunta)
            fila.put(("Gemini", resposta.text))
            return
        except Exception as e:
            if "503" in str(e) and tentativa < 2:
                time.sleep(2 * (tentativa + 1))  # espera 2s, depois 4s
                continue
            fila.put(("Erro", str(e)))
            return


def mostrar(autor, texto):
    conversa.config(state="normal")
    conversa.insert(tk.END, f"{autor}:\n", "autor")
    conversa.insert(tk.END, f"{texto}\n\n")
    conversa.config(state="disabled")
    conversa.see(tk.END)


def verificar_fila():
    try:
        autor, texto = fila.get_nowait()
    except queue.Empty:
        root.after(100, verificar_fila)
        return
    mostrar(autor, texto)
    botao.config(state="normal", text="Enviar")
    entrada.focus()


def enviar(event=None):
    if str(botao["state"]) == "disabled":  # evita enviar enquanto espera resposta
        return
    pergunta = entrada.get().strip()
    if not pergunta:
        return
    mostrar("Você", pergunta)
    entrada.delete(0, tk.END)
    botao.config(state="disabled", text="Pensando...")
    threading.Thread(target=consultar, args=(pergunta,), daemon=True).start()
    root.after(100, verificar_fila)


# ---------- Interface ----------
root = tk.Tk()
root.title("Chat com Gemini")
root.geometry("600x500")

topo = tk.Frame(root)
topo.pack(fill="x", padx=10, pady=(10, 0))

botao_tema = tk.Button(topo, command=alternar_tema, relief="flat", padx=10, pady=3)
botao_tema.pack(side="right")

conversa = ScrolledText(root, wrap="word", state="disabled", padx=10, pady=10)
conversa.tag_config("autor", font=("Arial", 10, "bold"))
conversa.pack(fill="both", expand=True, padx=10, pady=(10, 5))

barra = tk.Frame(root)
barra.pack(fill="x", padx=10, pady=(0, 10))

entrada = tk.Entry(barra, font=("Arial", 11))
entrada.pack(side="left", fill="x", expand=True, ipady=5)
entrada.bind("<Return>", enviar)
entrada.focus()

botao = tk.Button(barra, text="Enviar", command=enviar, width=10, relief="flat")
botao.pack(side="right", padx=(8, 0))

aplicar_tema()  # aplica o tema inicial depois de criar todos os widgets
root.mainloop() 

