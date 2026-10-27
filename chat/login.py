"""Sistema de login com interface gráfica (Tkinter).

- Telas de login e cadastro
- Senhas guardadas com hash (PBKDF2 + salt)
- Dados salvos em usuarios.json
"""

import hashlib
import hmac
import json
import os
import secrets
import tkinter as tk
from tkinter import messagebox, ttk

ARQUIVO = "usuarios.json"
ITERACOES = 200_000
MAX_TENTATIVAS = 3


# ---------- Lógica ----------
def carregar_usuarios() -> dict:
    if not os.path.exists(ARQUIVO):
        return {}
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_usuarios(usuarios: dict) -> None:
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)


def gerar_hash(senha: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, ITERACOES).hex()


# ---------- Interface ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Login")
        self.geometry("340x300")
        self.resizable(False, False)
        self.tentativas = 0

        self.container = ttk.Frame(self, padding=25)
        self.container.pack(fill="both", expand=True)
        self.mostrar_login()

    def limpar(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def campo(self, texto, oculto=False):
        ttk.Label(self.container, text=texto).pack(anchor="w", pady=(8, 2))
        entrada = ttk.Entry(self.container, show="•" if oculto else "")
        entrada.pack(fill="x")
        return entrada

    # --- Tela de login ---
    def mostrar_login(self):
        self.limpar()
        self.geometry("340x300")
        ttk.Label(self.container, text="Entrar", font=("Segoe UI", 16, "bold")).pack()

        self.e_usuario = self.campo("Usuário")
        self.e_senha = self.campo("Senha", oculto=True)
        self.e_senha.bind("<Return>", lambda e: self.entrar())

        ttk.Button(self.container, text="Entrar", command=self.entrar).pack(
            fill="x", pady=(18, 6)
        )
        ttk.Button(
            self.container, text="Criar conta", command=self.mostrar_cadastro
        ).pack(fill="x")
        self.e_usuario.focus()

    def entrar(self):
        usuario = self.e_usuario.get().strip().lower()
        senha = self.e_senha.get()
        dados = carregar_usuarios().get(usuario)

        if dados:
            calculado = gerar_hash(senha, bytes.fromhex(dados["salt"]))
            if hmac.compare_digest(calculado, dados["hash"]):
                self.mostrar_boas_vindas(usuario)
                return

        self.tentativas += 1
        restantes = MAX_TENTATIVAS - self.tentativas
        if restantes <= 0:
            messagebox.showerror("Bloqueado", "Muitas tentativas. Fechando o app.")
            self.destroy()
        else:
            messagebox.showerror(
                "Erro", f"Usuário ou senha incorretos.\nTentativas restantes: {restantes}"
            )
            self.e_senha.delete(0, "end")

    # --- Tela de cadastro ---
    def mostrar_cadastro(self):
        self.limpar()
        self.geometry("340x380")
        ttk.Label(
            self.container, text="Criar conta", font=("Segoe UI", 16, "bold")
        ).pack()

        self.c_usuario = self.campo("Novo usuário")
        self.c_senha = self.campo("Senha (mín. 6 caracteres)", oculto=True)
        self.c_confirma = self.campo("Confirmar senha", oculto=True)

        ttk.Button(self.container, text="Cadastrar", command=self.cadastrar).pack(
            fill="x", pady=(18, 6)
        )
        ttk.Button(self.container, text="Voltar", command=self.mostrar_login).pack(
            fill="x"
        )
        self.c_usuario.focus()

    def cadastrar(self):
        usuario = self.c_usuario.get().strip().lower()
        senha = self.c_senha.get()
        confirma = self.c_confirma.get()
        usuarios = carregar_usuarios()

        if not usuario:
            messagebox.showwarning("Atenção", "Informe um usuário.")
        elif usuario in usuarios:
            messagebox.showwarning("Atenção", "Esse usuário já existe.")
        elif len(senha) < 6:
            messagebox.showwarning("Atenção", "A senha deve ter ao menos 6 caracteres.")
        elif senha != confirma:
            messagebox.showwarning("Atenção", "As senhas não coincidem.")
        else:
            salt = secrets.token_bytes(16)
            usuarios[usuario] = {"salt": salt.hex(), "hash": gerar_hash(senha, salt)}
            salvar_usuarios(usuarios)
            messagebox.showinfo("Sucesso", "Cadastro realizado! Faça login.")
            self.mostrar_login()

    # --- Tela pós-login ---
    def mostrar_boas_vindas(self, usuario):
        self.limpar()
        self.geometry("340x300")
        ttk.Label(
            self.container, text=f"Bem-vindo, {usuario}!", font=("Segoe UI", 16, "bold")
        ).pack(pady=40)
        ttk.Button(self.container, text="Sair", command=self.mostrar_login).pack(
            fill="x"
        )


if __name__ == "__main__":
    App().mainloop()