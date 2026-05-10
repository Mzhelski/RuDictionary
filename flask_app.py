from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os

app = Flask(__name__)

# Добавляем CORS вручную для локальной разработки
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# Маршрут для favicon и статических файлов
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/site.webmanifest')
def webmanifest():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'site.webmanifest', mimetype='application/manifest+json')

# Определяем базовую директорию проекта (где лежит этот файл)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Формируем абсолютный путь к файлу со словами
JSON_PATH = os.path.join(BASE_DIR, 'data', 'words.json')

def load_dictionaries():
    """Загружает основной и обратный словари из файла."""
    try:
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                main_dict = json.load(f)
        else:
            # Создаем директорию data, если её нет
            os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)

            # Тестовые данные, если файл не найден
            main_dict = {
                "глаза": ["очи", "зенки"],
                "дом": ["хоромы", "чертоги"],
                "дорога": ["стезя", "путь"],
                "лицо": ["лик", "облик"],
                "рука": ["длань", "десница"],
                "голова": ["глава", "маковка"]
            }

            # Сохраняем тестовые данные по абсолютному пути
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(main_dict, f, ensure_ascii=False, indent=2)

        # Автоматически создаем обратный словарь
        reverse_dict = {}
        for modern_word, archaic_words in main_dict.items():
            for archaic in archaic_words:
                if archaic not in reverse_dict:
                    reverse_dict[archaic] = []
                reverse_dict[archaic].append(modern_word)

        return main_dict, reverse_dict

    except Exception as e:
        print(f"Ошибка загрузки словаря: {e}")
        return {"ошибка": ["проверьте файл"]}, {"проверьте": ["ошибка"]}

# Загружаем словари один раз при старте сервера
modern_to_archaic, archaic_to_modern = load_dictionaries()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    try:
        query = request.args.get('q', '').lower().strip()
        mode = request.args.get('mode', 'auto')

        if not query:
            return jsonify({'error': 'Введите слово для поиска'})

        result = {'query': query, 'mode': mode, 'results': []}

        # Логика поиска (Modern)
        if mode in ['modern', 'auto']:
            for word, synonyms in modern_to_archaic.items():
                if query in word:
                    result['results'].append({'type': 'modern', 'word': word, 'synonyms': synonyms})

        # Логика поиска (Archaic)
        if mode in ['archaic', 'auto']:
            for word, synonyms in archaic_to_modern.items():
                if query in word:
                    result['results'].append({'type': 'archaic', 'word': word, 'synonyms': synonyms})

        if not result['results']:
            result['error'] = f'Не найдено слов, содержащих "{query}"'

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/suggest')
def api_suggest():
    try:
        query = request.args.get('q', '').lower().strip()
        suggestions = []
        if len(query) >= 2:
            seen_words = set()
            # Поиск подсказок в обоих словарях
            for d, t in [(modern_to_archaic, 'modern'), (archaic_to_modern, 'archaic')]:
                for word in d:
                    if query in word and word not in seen_words:
                        suggestions.append({'word': word, 'type': t})
                        seen_words.add(word)

            suggestions.sort(key=lambda x: (0 if x['word'].startswith(query) else 1, x['word']))
            suggestions = suggestions[:10]
        return jsonify({'suggestions': suggestions})
    except Exception as e:
        return jsonify({'suggestions': []})

@app.route('/api/status')
def api_status():
    return jsonify({
        'status': 'ok',
        'modern_words_count': len(modern_to_archaic),
        'archaic_words_count': len(archaic_to_modern)
    })

if __name__ == '__main__':
    # На PythonAnywhere этот блок не используется, сервер запускается через WSGI
    app.run(debug=False)