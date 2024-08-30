from flask import Flask, render_template, request
import psycopg2
from datetime import datetime, timedelta
import os


app = Flask(__name__)

def get_db_connection():
    # Obtén la URL de la base de datos de la variable de entorno DATABASE_URL o usa los parámetros locales
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Configuración para Heroku
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    else:
        # Configuración local
        conn = psycopg2.connect(
            dbname='APPLOTI',
            user='postgres',
            password='samuelloco123',
            port='5432',
            host='localhost'
        )

    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fecha, numero1, numero2, numero3 
        FROM ResultadosDiarios 
        ORDER BY fecha DESC
        LIMIT 7
    """)
    last_7_days_results = cursor.fetchall()
    conn.close()

    return render_template('index.html', last_7_days_results=last_7_days_results)

@app.route('/view_all')
def view_all():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, numero1, numero2, numero3 FROM ResultadosDiarios ORDER BY fecha DESC")
    resultados = cursor.fetchall()
    conn.close()
    return render_template('results.html', resultados=resultados)

@app.route('/most_frequent', methods=['GET', 'POST'])
def most_frequent():
    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT numero1, numero2, numero3 FROM ResultadosDiarios
            WHERE fecha BETWEEN %s AND %s
        """, (fecha_inicio, fecha_fin))
        numeros = cursor.fetchall()
        conn.close()

        all_numbers = [num for row in numeros for num in row]
        freq = {num: all_numbers.count(num) for num in set(all_numbers)}
        sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)

        resultado_con_paridad = []
        for num, count in sorted_freq:
            try:
                num = int(num)
                paridad = 'Par' if num % 2 == 0 else 'Impar'
            except ValueError:
                paridad = 'Desconocido'
            resultado_con_paridad.append((num, count, paridad))

        return render_template('most_frequent.html', frecuencias=resultado_con_paridad, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    return render_template('most_frequent.html')


@app.route('/check_number_frequency', methods=['GET', 'POST'])
def check_number_frequency():
    frequency = None
    frequency_combination = None
    numero = None
    numero1 = None
    numero2 = None
    numero3 = None
    mes = None
    anio = None

    if request.method == 'POST':
        numero = request.form.get('numero')  # Número individual
        numero1 = request.form.get('numero1')  # Primer número de la combinación
        numero2 = request.form.get('numero2')  # Segundo número de la combinación
        numero3 = request.form.get('numero3')  # Tercer número de la combinación
        mes = request.form.get('mes')  # Mes
        anio = request.form.get('anio')  # Año

        # Validar mes y año antes de ejecutar la consulta
        if mes and mes.isdigit():
            mes = int(mes)
        else:
            mes = None

        if anio and anio.isdigit():
            anio = int(anio)
        else:
            anio = None

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Caso 1: Buscar la frecuencia de un número individual
            if numero and anio:
                if mes:  # Buscar en un mes específico
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM ResultadosDiarios
                        WHERE (numero1 = %s OR numero2 = %s OR numero3 = %s)
                        AND EXTRACT(MONTH FROM fecha) = %s
                        AND EXTRACT(YEAR FROM fecha) = %s
                    """, (numero, numero, numero, mes, anio))
                else:  # Buscar en todo el año
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM ResultadosDiarios
                        WHERE (numero1 = %s OR numero2 = %s OR numero3 = %s)
                        AND EXTRACT(YEAR FROM fecha) = %s
                    """, (numero, numero, numero, anio))
                
                result = cursor.fetchone()
                if result:
                    frequency = result[0]

            # Caso 2: Buscar la frecuencia de una combinación de tres números
            if numero1 and numero2 and numero3 and anio:
                if mes:  # Buscar en un mes específico
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM ResultadosDiarios
                        WHERE (numero1 = %s AND numero2 = %s AND numero3 = %s)
                        AND EXTRACT(MONTH FROM fecha) = %s
                        AND EXTRACT(YEAR FROM fecha) = %s
                    """, (numero1, numero2, numero3, mes, anio))
                else:  # Buscar en todo el año
                    cursor.execute("""
                        SELECT COUNT(*)
                        FROM ResultadosDiarios
                        WHERE (numero1 = %s AND numero2 = %s AND numero3 = %s)
                        AND EXTRACT(YEAR FROM fecha) = %s
                    """, (numero1, numero2, numero3, anio))
                
                result_combination = cursor.fetchone()
                if result_combination:
                    frequency_combination = result_combination[0]

        except psycopg2.Error as e:
            print(f"Error al ejecutar la consulta: {e}")
        finally:
            conn.close()

    return render_template('check_number_frequency.html', 
                           frequency=frequency, 
                           frequency_combination=frequency_combination, 
                           numero=numero, 
                           numero1=numero1, 
                           numero2=numero2, 
                           numero3=numero3, 
                           mes=mes, 
                           anio=anio)

@app.route('/type_frequencies', methods=['GET', 'POST'])
def type_frequencies():
    if request.method == 'POST':
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

        if not fecha_inicio or not fecha_fin:
            return "Las fechas de inicio y fin son necesarias."

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                SELECT numero1, numero2, numero3 FROM ResultadosDiarios
                WHERE fecha BETWEEN %s AND %s
            """
            cursor.execute(query, (fecha_inicio, fecha_fin))
            numeros = cursor.fetchall()
            conn.close()

            all_numbers = []
            for row in numeros:
                for num in row:
                    try:
                        num = int(num)
                        all_numbers.append(num)
                    except (TypeError, ValueError):
                        pass

            if not all_numbers:
                return "No se encontraron números válidos en el rango de fechas."

            freq = {}
            for num in all_numbers:
                tipo = 'Par' if num % 2 == 0 else 'Impar'
                if num not in freq:
                    freq[num] = {'count': 1, 'tipo': tipo}
                else:
                    freq[num]['count'] += 1

            sorted_freq = sorted(freq.items(), key=lambda x: x[1]['count'], reverse=True)

            return render_template('type_frequencies.html', frecuencias=sorted_freq, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

        except Exception as e:
            print("Error durante la ejecución de la consulta SQL o procesamiento:", e)
            return "Ocurrió un error al procesar su solicitud."

    return render_template('type_frequencies.html')

@app.route('/least_frequent', methods=['GET', 'POST'])
def least_frequent():
    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT numero1, numero2, numero3 FROM ResultadosDiarios
            WHERE fecha BETWEEN %s AND %s
        """, (fecha_inicio, fecha_fin))
        numeros = cursor.fetchall()
        conn.close()

        all_numbers = [num for row in numeros for num in row]
        freq = {}
        for num in all_numbers:
            if num not in freq:
                freq[num] = {'count': 1}
            else:
                freq[num]['count'] += 1

        sorted_freq = sorted(freq.items(), key=lambda x: x[1]['count'])

        return render_template('least_frequent.html', frecuencias=sorted_freq, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    return render_template('least_frequent.html')

@app.route('/filter_even_numbers', methods=['GET', 'POST'])
def filter_even_numbers():
    resultados = []
    if request.method == 'POST':
        year = request.form.get('year')
        month = request.form.get('month')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Construir consulta SQL
        query = """
        SELECT numero1, numero2, numero3, fecha FROM ResultadosDiarios
        WHERE 
            CAST(numero1 AS INTEGER) % 2 = 0 AND
            CAST(numero2 AS INTEGER) % 2 = 0 AND
            CAST(numero3 AS INTEGER) % 2 = 0
        """

        # Agregar filtros de año y mes si se proporcionan
        if year:
            query += " AND EXTRACT(YEAR FROM fecha) = %s" % year
        if month:
            query += " AND EXTRACT(MONTH FROM fecha) = %s" % month

        cursor.execute(query)
        resultados = cursor.fetchall()
        conn.close()

    return render_template('filter_even_numbers.html', resultados=resultados)


if __name__ == '__main__':
    app.run(debug=True)
