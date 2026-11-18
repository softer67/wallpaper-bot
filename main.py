from aiohttp import web
import hashlib
import hmac
import time

# Твой токен бота
BOT_TOKEN = "9177937588:AAFEdgj5Zs4w5xkSclSKGbibKRSM6KejWiE"

async def handle_telegram_auth(request):
    try:
        data = await request.json()
        
        received_hash = data.get('hash')
        if not received_hash:
            return web.json_response({'success': False, 'message': 'No hash provided'})
        
        # Проверяем свежесть данных (не старше 1 дня)
        auth_date = data.get('auth_date', 0)
        if time.time() - auth_date > 86400:
            return web.json_response({'success': False, 'message': 'Data is outdated'})

        # Формируем строку проверки
        check_data = []
        for key in sorted(data.keys()):
            if key == 'hash':
                continue
            check_data.append(f"{key}={data[key]}")
        data_check_string = "\n".join(check_data)

        # Вычисляем HMAC-SHA256 подпись
        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        calculated_hash = hmac.new(
            secret_key, 
            data_check_string.encode(), 
            hashlib.sha256
        ).hexdigest()

        # Сверяем хэши
        if not hmac.compare_digest(calculated_hash, received_hash):
            return web.json_response({'success': False, 'message': 'Invalid hash signature'})

        # Успешная авторизация
        user_id = data.get('id')
        first_name = data.get('first_name')
        
        # Здесь можно добавить логику сессии для пользователя

        return web.json_response({'success': True, 'message': 'Authorized successfully'})

    except Exception as e:
        return web.json_response({'success': False, 'message': str(e)}, status=400)
