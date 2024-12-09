import os
import subprocess
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Папка для загрузки файлов и хранения результатов
UPLOAD_FOLDER = './uploads'
COMPILE_FOLDER = './compiled'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COMPILE_FOLDER, exist_ok=True)

# Тестовые данные
TEST_INPUT = "test_input.txt"   # Файл с входными данными
TEST_OUTPUT = "test_output.txt" # Файл с ожидаемым результатом

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "ФАЙЛ", "error": "Файл не загружен"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "ФАЙЛ", "error": "Файл не выбран"}), 400

    if not file.filename.endswith(".cpp"):
        return jsonify({"status": "ФАЙЛ", "error": "Файл должен быть .cpp"}), 400

    # Сохраняем файл
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Компиляция файла
    executable_path = os.path.join(COMPILE_FOLDER, "program.out")
    compile_command = f"g++ {file_path} -o {executable_path}"

    try:
        subprocess.run(compile_command, shell=True, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "ФАЙЛ", "error": "Ошибка компиляции", "details": e.stderr.decode('utf-8', errors='replace')}), 400

    # Выполнение программы с входными данными
    with open(TEST_INPUT, "r") as input_file:
        try:
            result = subprocess.run(executable_path, stdin=input_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        except subprocess.TimeoutExpired:
            return jsonify({"status": "ФАЙЛ", "error": "Программа выполнялась слишком долго"}), 400

    # Чтение и сравнение результата
    try:
        actual_output = result.stdout.decode('utf-8', errors='replace').strip()
    except UnicodeDecodeError as e:
        return jsonify({"status": "ФАЙЛ", "error": f"Ошибка декодирования вывода: {str(e)}"}), 400

    # Читаем ожидаемый результат из test_output.txt
    with open(TEST_OUTPUT, "r") as expected_output_file:
        expected_output = expected_output_file.read().strip()

    # Сравниваем фактический и ожидаемый результаты
    if actual_output == expected_output:
        return jsonify({"status": "УСПЕХ", "message": "Вывод совпадает с ожидаемым", "output": actual_output}), 200
    else:
        return jsonify({"status": "НЕУДАЧА", "message": "Вывод не совпадает с ожидаемым", "actual_output": actual_output, "expected_output": expected_output}), 200

if __name__ == '__main__':
    app.run(debug=True)
