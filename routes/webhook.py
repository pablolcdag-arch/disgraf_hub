from fastapi import APIRouter, Request
from dependencies import get_current_user, DATA_DIR, gemini_client, TELEGRAM_API_URL, TELEGRAM_TOKEN, GEMINI_API_KEY
import os
import json
from datetime import datetime, timedelta
import requests
import threading
from seo_service import run_seo_workflow

router = APIRouter()
@router.post("/api/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" not in data or "text" not in data["message"]:
        return {"status": "ok"}

    chat_id = data["message"]["chat"]["id"]
    text = data["message"]["text"]

    def process_message():
        if not GEMINI_API_KEY:
            reply = "No tengo cerebro conectado (Falta GEMINI_API_KEY)."
        else:
            try:
                import json
                
                quotes_file = os.path.join(DATA_DIR, 'historial_presupuestos.json')
                history = []
                if os.path.exists(quotes_file):
                    with open(quotes_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                
                from datetime import datetime, timedelta
                
                today = datetime.now()
                today_date = today.strftime("%Y-%m-%d")
                today_quotes = [q for q in history if q.get("date", "").startswith(today_date)]
                
                # Filter history for the last 15 days
                fifteen_days_ago = today - timedelta(days=15)
                recent_quotes = []
                for q in history:
                    q_date_str = q.get("date", "")
                    if q_date_str:
                        try:
                            # Handle ISO format dates
                            q_date = datetime.fromisoformat(q_date_str)
                            if q_date >= fifteen_days_ago:
                                recent_quotes.append(q)
                        except:
                            pass
                
                total_today = sum(q.get("total", 0) for q in today_quotes)
                total_b = sum(1 for q in today_quotes if q.get("tipoB"))
                total_a = len(today_quotes) - total_b
                
                summary = f"Hoy ({today_date}) se hicieron {len(today_quotes)} presupuestos. "
                summary += f"Total presupuestado estimado: ${total_today:,.2f}. "
                summary += f"Presupuestos Tipo B: {total_b}. Presupuestos Normales: {total_a}."
                
                prompt = f"""Eres el Asistente Inteligente de la plataforma Disgraf Hub. 
El usuario que te habla es tu jefe (Pablo) o un administrador de ventas. Responde sus consultas basándote estrictamente en los datos proporcionados.
Si te pide presupuestos, analiza los datos. No inventes respuestas. Responde siempre en un tono amable pero directo, sin excederte en saludos.

REGLAS DE FORMATO (MUY IMPORTANTE):
Telegram NO soporta tablas Markdown (como | Cliente | Total |). NUNCA uses tablas.
1. SIEMPRE comienza tu respuesta con un resumen del día consultado. Ejemplo: "Aquí tienes los presupuestos registrados el día [Fecha]: se realizaron X presupuestos por un total de $X."
2. Si tienes que listar presupuestos o datos, usa listas limpias con emojis y negritas. Ejemplo de cómo debes listar:

👤 **Nombre Cliente** (Vendedor)
🔹 Producto principal resumido...
💰 Total: $1,234.00
📝 ID: 1234abcd

NUEVO COMANDO (SÚPER IMPORTANTE):
Si el usuario te pide explícitamente "crear una oferta", "hacer un blog", "crear una promo" de algún producto específico, DEBES responder exactamente con este formato:
[ACCION_SEO: Nombre del Producto]

Por ejemplo, si dice "Haceme una promo del Vinilo Esmerilado", respondes:
[ACCION_SEO: Vinilo Esmerilado]
(Y nada más, solo esa línea).

Resumen del día de hoy:
{summary}

Historial COMPLETO de presupuestos de los últimos 15 días (en formato JSON):
{json.dumps(recent_quotes, ensure_ascii=False)}

La pregunta del usuario es: {text}
"""
                response = gemini_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
                reply = response.text.strip()
                
                # Check if it is an SEO action
                if reply.startswith("[ACCION_SEO:") and reply.endswith("]"):
                    product_target = reply.replace("[ACCION_SEO:", "").replace("]", "").strip()
                    reply = f"🚀 Entendido. Generando un post de blog y oferta SEO para: *{product_target}*. Esto tardará unos segundos, publicando..."
                    
                    # Send immediate response
                    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": reply,
                        "parse_mode": "Markdown"
                    })
                    
                    # Run SEO in background
                    try:
                        link = run_seo_workflow(product_target)
                        msg = f"✅ ¡Post publicado exitosamente en el blog!\n\n🔗 Puedes verlo aquí: {link}"
                    except Exception as e:
                        msg = f"❌ Ocurrió un error al intentar publicar el artículo: {str(e)}"
                        
                    requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": "Markdown"
                    })
                    return # Exit early for SEO actions
                    
            except Exception as e:
                reply = f"Error procesando con IA: {str(e)}"

        if TELEGRAM_TOKEN:
            requests.post(f"{TELEGRAM_API_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": reply,
                "parse_mode": "Markdown"
            })
            
        # --- Guardar Log de Conversacion (10 días) ---
        try:
            chat_log_file = os.path.join(DATA_DIR, 'telegram_chat_history.json')
            chat_history = []
            if os.path.exists(chat_log_file):
                with open(chat_log_file, 'r', encoding='utf-8') as f:
                    chat_history = json.load(f)
                    
            now = datetime.now()
            chat_history.append({
                "timestamp": now.isoformat(),
                "user_text": text,
                "bot_reply": reply
            })
            
            ten_days_ago = now - __import__('datetime').timedelta(days=10)
            valid_chat_history = []
            for msg in chat_history:
                try:
                    msg_date = datetime.fromisoformat(msg["timestamp"])
                    if msg_date >= ten_days_ago:
                        valid_chat_history.append(msg)
                except:
                    pass
                    
            with open(chat_log_file, 'w', encoding='utf-8') as f:
                json.dump(valid_chat_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error guardando log de telegram:", e)
            
    import threading
    threading.Thread(target=process_message).start()
    return {"status": "ok"}

