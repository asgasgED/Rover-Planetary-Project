# Configure AMD TokenLab for TerraRover

**The provider API key belongs in `.env`, not in `.venv`.** `.venv/` is created by Python and contains installed libraries. The model `Qwen3.8-27B` is remote; its weights do not belong in the repository.

## Windows PowerShell

```powershell
# Run in the TerraRover_Plataforma project root.
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
Copy-Item .env.example .env
```

Open `.env` and set your **own** credential:

```dotenv
AMD_BASE_URL=https://api.tokenlab.amd.com/v1
AMD_MODEL=Qwen3.8-27B
AMD_API_KEY=PASTE_YOUR_REAL_PRIVATE_KEY
ENVIAR_A_IA=true
```

Start the **Python backend**, not `http.server`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000/api/health to confirm that the backend is running. It only reports whether a key is set, never the key itself. Use the **Planetary Comparator** and the **Interpret findings with AMD AI** action.

### Troubleshooting

| Symptom | Cause / action |
|---|---|
| `ModuleNotFoundError` | Install `requirements-backend.txt` into the same interpreter used to run the backend. |
| Backend required in web UI | Run `uvicorn backend.api:app`, not a plain static server. |
| `AMD_API_KEY is not configured` | Create `.env` in **project root** and use a real private key, not the template text. Restart server. |
| AI disabled | Set `ENVIAR_A_IA=true` then restart. Numerical analysis works with false. |
| HTTP 401/403 or provider request failed | Verify account, correct key and endpoint on AMD TokenLab. Keys must not be logged or shared. |
| HTTP 404 | Verify the model identifier is enabled for your account. |
| HTTP 429 or timeout | Provider quota/concurrency/network issue. Retry later; numeric results remain available. |
| 33 terrains not visible as complete | Run the importer after copying six real final files per region into `datos_para_importar/entrega_5km/REGION/`. |

**Privacy note:** This backend sends calculated metrics and low-resolution context images of the chosen DEMs to the remote AI service when enabled. Turn AI off if data sharing is undesirable. No key is sent to the browser.

**Public deployment note:** Never commit `.env`. A public AI endpoint needs user authentication, quotas and a secure backend reverse proxy; the local prototype intentionally binds to `127.0.0.1`.
