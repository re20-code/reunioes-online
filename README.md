# Reuniões Online – Backend + App

API em FastAPI + página web que mostra reuniões **agora** e **hoje**.

## O que faz

- Serve a lista de reuniões (grade pública + tentativa de extrair salas do CSR)
- Endpoint `/api/meetings?mode=now|today|all`
- Frontend em `/` com botões Agora / Hoje e links de entrada

## Limite importante

O site **csrbrasil.org.br** carrega as salas por JavaScript.  
Sem navegador headless (Playwright), a API não consegue listar as 100+ salas Zoom uma a uma.  
Nesses casos o app aponta para a seção AO VIVO do CSR (senha padrão `000000`).

Grupos com link fixo público (CCA, Amor-Exigente, VOREN, CoDA, etc.) abrem o Zoom/Meet direto.

---

## Como subir GRÁTIS no Render.com (recomendado)

### 1. Conta
1. Acesse https://render.com
2. Crie conta (pode usar GitHub)

### 2. Subir o código
**Opção fácil – ZIP:**
1. Compacte a pasta `reunioes-backend` em um ZIP
2. No Render: **New → Web Service**
3. Se pedir repositório Git, crie um repositório no GitHub, envie esta pasta e conecte

**Ou pelo GitHub:**
```bash
cd reunioes-backend
git init
git add .
git commit -m "reunioes api"
# crie um repo no github.com e:
git remote add origin https://github.com/SEU_USUARIO/reunioes-api.git
git push -u origin main
```

### 3. Configurar o serviço no Render
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Plano: **Free**

### 4. Depois do deploy
O Render gera uma URL tipo:
`https://reunioes-api-xxxx.onrender.com`

Abra essa URL no celular → é o app.  
API: `https://reunioes-api-xxxx.onrender.com/api/meetings?mode=now`

**Obs.:** no plano free o serviço “dorme” após ~15 min sem uso. O primeiro acesso depois pode demorar 30–60 s.

---

## Rodar no seu computador (teste)

```bash
cd reunioes-backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Abra: http://localhost:8000

---

## Outros servidores gratuitos

| Serviço | Site | Observação |
|---------|------|------------|
| **Render** | render.com | Mais simples |
| **Railway** | railway.app | Também fácil |
| **Fly.io** | fly.io | Um pouco mais técnico |
| **PythonAnywhere** | pythonanywhere.com | Bom para iniciantes |

---

## Próximos passos (se quiser melhorar)

1. Adicionar Playwright no servidor para ler de verdade as salas do CSR
2. Agendar atualização a cada 10 minutos
3. Transformar o frontend em PWA instalável

Arquivos principais:
- `main.py` → API
- `static/index.html` → app
- `requirements.txt` → dependências
