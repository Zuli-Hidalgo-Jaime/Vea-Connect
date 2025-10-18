import os
import sys
try:
    import readline  # type: ignore  # En Windows puede no existir
except Exception:  # pragma: no cover - sólo para compatibilidad Windows
    readline = None  # No es crítico; seguimos sin historial/edición avanzada

# Colores ANSI para consola
BLUE = "\x1b[34m"      # Azul para usuario
GREEN = "\x1b[32m"     # Verde para bot
RESET = "\x1b[0m"      # Reset color


def ensure_django():
    # Asegurar que la raíz del proyecto esté en sys.path (para importar 'config')
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Seleccionar settings como hace manage.py
    settings_module = (
        "config.settings.azure_production"
        if 'WEBSITE_HOSTNAME' in os.environ
        else 'config.settings.development'
    )
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

    # Cargar .env solo en local (igual que manage.py)
    if 'WEBSITE_HOSTNAME' not in os.environ:
        try:
            from dotenv import load_dotenv  # type: ignore
            load_dotenv('./.env')
        except Exception:
            pass

    import django  # noqa: WPS433
    django.setup()


def main() -> int:
    ensure_django()

    from django.conf import settings  # noqa: WPS433
    # Habilitar RAG bajo flag (sin tocar .env)
    setattr(settings, 'BOT_USE_RAG', True)

    from utilities.azure_search_client import get_azure_search_client  # noqa: WPS433
    from utilities.embedding_manager import EmbeddingManager  # noqa: WPS433
    from apps.whatsapp_bot.handlers import WhatsAppBotHandler  # noqa: WPS433
    import types

    sc = get_azure_search_client()
    em = EmbeddingManager(search_client=sc)

    class DummyACS:
        def send_text_message(self, phone, text):
            return {"success": True, "message_id": "local"}

    handler = WhatsAppBotHandler(acs_service=DummyACS(), embedding_manager=em)

    # Prompt personalizable para LLM (system). Puede cargarse desde archivo
    prompt_dir = os.path.join(os.path.dirname(__file__), 'prompts')
    os.makedirs(prompt_dir, exist_ok=True)
    default_prompt = (
        "Responde en español, claro y breve, usando exclusivamente el contexto provisto. "
        "Si el contexto no contiene la respuesta, indícalo y sugiere contactar a un humano."
    )
    prompt_file = os.environ.get('CLI_PROMPT_FILE') or os.path.join(prompt_dir, 'whatsapp_cli_prompt.txt')
    current_system_prompt = default_prompt
    try:
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r', encoding='utf-8') as f:
                txt = f.read().strip()
                if txt:
                    current_system_prompt = txt
    except Exception:
        pass

    # Monkeypatch opcional de OpenAIService.generate_chat_response para inyectar el prompt
    try:
        from apps.embeddings import openai_service as oai_mod  # noqa: WPS433
        if hasattr(oai_mod, 'OpenAIService'):
            _orig_generate = oai_mod.OpenAIService.generate_chat_response

            def _wrapped_generate(self, messages, max_tokens=1000, temperature=0.7):  # noqa: ANN001
                if messages and isinstance(messages, list):
                    # Reemplazar/inyectar el mensaje de sistema
                    new_messages = []
                    has_system = False
                    for m in messages:
                        if m.get('role') == 'system' and not has_system:
                            new_messages.append({'role': 'system', 'content': current_system_prompt})
                            has_system = True
                        else:
                            new_messages.append(m)
                    if not has_system:
                        new_messages.insert(0, {'role': 'system', 'content': current_system_prompt})
                    messages = new_messages
                return _orig_generate(self, messages, max_tokens=max_tokens, temperature=temperature)

            # Guardar en el módulo para que el handler lo use
            oai_mod.OpenAIService.generate_chat_response = _wrapped_generate  # type: ignore
    except Exception:
        pass

    # Modo de operación: 'rag' por defecto (siempre usa _rag_answer); alternativo: 'intents'
    mode = os.environ.get('CLI_MODE', 'rag').lower()
    if mode not in {"rag", "intents"}:
        mode = "rag"

    # print("WhatsApp Bot CLI (RAG habilitado). Comandos: :prompt, :setprompt, :loadprompt, :clearprompt, :rag <texto>, :mode rag|intents, salir")  # Suprimido para CLI
    phone = os.environ.get('CLI_WHATSAPP_PHONE', 'whatsapp:+520000000000')
    while True:
        try:
            user = input(f"{BLUE}Tú: {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()  # nueva línea
            break
        if not user:
            continue
        if user.startswith(':mode'):
            parts = user.split()
            if len(parts) == 2 and parts[1].lower() in {"rag", "intents"}:
                mode = parts[1].lower()
                print(f"[OK] Modo cambiado a {mode}")
            else:
                print("[INFO] Uso: :mode rag | :mode intents")
            continue
        if user.startswith(':prompt'):
            print("--- System prompt actual ---")
            print(current_system_prompt)
            continue
        if user.startswith(':setprompt '):
            current_system_prompt = user[len(':setprompt '):].strip() or default_prompt
            print("[OK] Prompt actualizado en memoria")
            continue
        if user.startswith(':loadprompt'):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    current_system_prompt = f.read().strip() or default_prompt
                print(f"[OK] Prompt cargado desde {prompt_file}")
            except Exception as e:
                print(f"[ERR] No se pudo cargar {prompt_file}: {e}")
            continue
        if user.startswith(':clearprompt'):
            current_system_prompt = default_prompt
            print("[OK] Prompt restablecido al default")
            continue
        if user.startswith(':rag '):
            text = user[len(':rag '):].strip()
            if not text:
                print("[ERR] Uso: :rag <texto>")
                continue
            # Forzar respuesta RAG directa (sin pasar por intents)
            try:
                ans = handler._rag_answer(text)
                print(f"{GREEN}Bot: {ans}{RESET}")
                print("-" * 80)
            except Exception as e:
                print(f"[ERR] RAG directo falló: {e}")
            continue
        if user.lower() in {"salir", "exit", "quit"}:
            break

        if mode == 'rag':
            try:
                texto = handler._rag_answer(user)
            except Exception as e:
                texto = f"[ERR] RAG falló: {e}"
            # Imprimir y enviar por DummyACS para consistencia visual
            handler.acs_service.send_text_message(phone, texto)
            print(f"{GREEN}Bot: {texto}{RESET}")
            print("-" * 80)
        else:
            payload = {"phone_number": phone, "message_text": user}
            resp = handler.process_message(payload)
            texto = resp.get('response') if isinstance(resp, dict) else str(resp)
            print(f"{GREEN}Bot: {texto}{RESET}")
            print("-" * 80)

    print("Hasta luego")
    return 0


if __name__ == "__main__":
    sys.exit(main())

