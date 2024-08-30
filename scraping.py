import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime

# Configura tus credenciales y detalles de PostgreSQL
HOST = 'localhost'
DATABASE = 'APPLOTI'
USER = 'postgres'
PASSWORD = 'samuelloco123'

# Función para conectarse a PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        dbname=DATABASE,
        user=USER,
        password=PASSWORD,
        host=HOST
    )
    return conn

# Función para hacer scraping y almacenar los datos
def scrape_and_store():
    # URL de la página web que contiene los números
    url = 'https://loteriasdominicanas.com/loteria-nacional/gana-mas'  # Reemplaza con la URL real

    # Obtener el contenido de la página
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error al acceder a la página: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extraer la fecha
    fecha_div = soup.find('div', class_='session-date px-2')
    if not fecha_div:
        print("No se encontró la fecha en la página.")
        return

    fecha_str = fecha_div.get_text(strip=True)  # Obtiene '23-08'
    # Asumiendo que el año es el actual
    dia, mes = map(int, fecha_str.split('-'))
    ano = datetime.now().year
    try:
        fecha = datetime(ano, mes, dia).date()
    except ValueError:
        print(f"Fecha inválida extraída: {fecha_str}")
        return

    # Extraer los tres números
    scores_div = soup.find('div', class_='game-scores p-2 ball-mode')
    if not scores_div:
        print("No se encontraron los números en la página.")
        return

    score_spans = scores_div.find_all('span', class_='score')
    if len(score_spans) < 3:
        print("No se encontraron suficientes números en la página.")
        return

    try:
        numero1 = int(score_spans[0].get_text(strip=True))
        numero2 = int(score_spans[1].get_text(strip=True))
        numero3 = int(score_spans[2].get_text(strip=True))
    except ValueError:
        print("Error al convertir los números a enteros.")
        return

    # Conectar a la base de datos y almacenar los datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Convertir fecha a formato de cadena para SQL
    fecha_str = fecha.strftime('%Y-%m-%d')

    # Verificar si ya existe un registro para la fecha
    cursor.execute("SELECT COUNT(*) FROM ResultadosDiarios WHERE fecha = %s", (fecha_str,))
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"Ya existe un registro para la fecha {fecha}.")
    else:
        cursor.execute("""
            INSERT INTO ResultadosDiarios (fecha, numero1, numero2, numero3)
            VALUES (%s, %s, %s, %s)
        """, (fecha_str, numero1, numero2, numero3))
        conn.commit()
        print(f"Datos almacenados para la fecha {fecha}: {numero1}, {numero2}, {numero3}")

    conn.close()


if __name__ == "__main__":
    scrape_and_store()
