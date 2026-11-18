from aiohttp import web
import hashlib
import hmac
import time

# Твой токен бота
BOT_TOKEN = "9177937588:AAFEdgj5Zs4w5xkSclSKGbibKRSM6KejWiE"
async def handle_telegram_auth(request):
    try:
        params = dict(request.query)
        received_hash = params.get('hash')
        if not received_hash:
            return web.Response(text="No hash provided", status=400)
        
        auth_date = int(params.get('auth_date', 0))
        if time.time() - auth_date > 86400:
            return web.Response(text="Data is outdated", status=400)

        check_data = []
        for key in sorted(params.keys()):
            if key == 'hash':
                continue
            check_data.append(f"{key}={params[key]}")
        data_check_string = "\n".join(check_data)

        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        calculated_hash = hmac.new(
            secret_key, 
            data_check_string.encode(), 
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return web.Response(text="Invalid hash signature", status=400)

        first_name = params.get('first_name', 'Гость')
        
        raise web.HTTPFound(location='/')
    except web.HTTPFound as e:
        e.set_cookie('tg_user_name', first_name, max_age=86400*30)
        raise e
    except Exception as e:
        return web.Response(text=str(e), status=400)

