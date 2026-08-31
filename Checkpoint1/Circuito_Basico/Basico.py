import numpy as np
import matplotlib.pyplot as plt
import re
import os

# carpeta donde esta este script, y subcarpetas Data / Graficos adentro
carpeta_script = os.path.dirname(os.path.abspath(__file__))
carpeta_datos = os.path.join(carpeta_script, 'Data')
carpeta_graficos = os.path.join(carpeta_script, 'Graficos')

# si la carpeta Graficos no existe, la creamos
if not os.path.exists(carpeta_graficos):
    os.makedirs(carpeta_graficos)


# función chiquita para armar la ruta completa de un archivo de datos
def ruta_dato(nombre_archivo):
    return os.path.join(carpeta_datos, nombre_archivo)


# función para leer archivos de regulación (línea y carga): dos columnas separadas por tabulador
def leer_regulacion(nombre_archivo):
    eje_x = []
    eje_y = []

    archivo = open(nombre_archivo, 'r', encoding='latin-1')
    lineas = archivo.readlines()
    archivo.close()

    # arrancamos en 1 para saltear el encabezado (vreg / V(vo), etc)
    for i in range(1, len(lineas)):
        linea = lineas[i].strip()
        if linea == '':
            continue
        columnas = linea.split('\t')
        x = float(columnas[0])
        y = float(columnas[1])
        eje_x.append(x)
        eje_y.append(y)

    return np.array(eje_x), np.array(eje_y)


# función para leer archivos de Bode: frecuencia + valor complejo tipo (magnituddB,fase°)
def leer_bode(nombre_archivo):
    frecuencia = []
    magnitud_db = []
    fase_grados = []

    # patron que busca: (numerodB,numero°)
    patron = re.compile(r'\(([-\d\.eE\+]+)dB,([-\d\.eE\+]+).\)')

    archivo = open(nombre_archivo, 'r', encoding='latin-1')
    lineas = archivo.readlines()
    archivo.close()

    for i in range(1, len(lineas)):
        linea = lineas[i].strip()
        if linea == '':
            continue
        columnas = linea.split('\t')
        f = float(columnas[0])

        match = patron.search(columnas[1])
        mag = float(match.group(1))
        fase = float(match.group(2))

        frecuencia.append(f)
        magnitud_db.append(mag)
        fase_grados.append(fase)

    return np.array(frecuencia), np.array(magnitud_db), np.array(fase_grados)


# --- regulación de línea: un gráfico por archivo ---
archivos_linea = [
    'reglinea_3.3_basico.txt',
    'reglinea_6.8_basico.txt',
    'reglinea_25_basico.txt',
    'reglinea_50_basico.txt'
]

titulos_linea = {
    'reg_linea_basico.txt': 'Regulación de línea',
    'reglinea_3.3_basico.txt': 'Regulación de línea — $R_L$ = 3.3 $\Omega$',
    'reglinea_6.8_basico.txt': 'Regulación de línea — $R_L$ = 6.8 $\Omega$',
    'reglinea_25_basico.txt': 'Regulación de línea — $R_L$ = 25 $\Omega$',
    'reglinea_50_basico.txt': 'Regulación de línea — $R_L$ = 50 $\Omega$'
}

for nombre in archivos_linea:
    vreg, vo = leer_regulacion(ruta_dato(nombre))

    plt.figure(figsize=(7, 4.5))
    plt.plot(vreg, vo, color='tab:blue')
    plt.xlabel(r'$V_{reg}$ [V]')
    plt.ylabel(r'$V_{o}$ [V]')
    plt.title(titulos_linea[nombre])
    plt.grid(True)
    plt.tight_layout()

    nombre_salida = nombre.replace('.txt', '.png')
    plt.savefig(os.path.join(carpeta_graficos, nombre_salida))

    plt.close()


# --- regulación de carga ---
rl, vo = leer_regulacion(ruta_dato('regcarga_basico.txt'))

plt.figure(figsize=(7, 4.5))
plt.plot(rl, vo, color='tab:orange')
plt.xlabel(r'$R_L$ [$\Omega$]')
plt.ylabel(r'$V_{o}$ [V]')
plt.title('Regulación de carga')
plt.grid(True)
plt.tight_layout()

plt.savefig(os.path.join(carpeta_graficos, 'regulacion_carga.png'))
plt.close()


# --- Bode: magnitud y fase separados, un gráfico por archivo ---
archivos_bode = [
    'T_3.3ohm_basico.txt',
    'T_6.8ohm_basico.txt',
    'T_25ohm_basico.txt',
    'T_50ohm_basico.txt'
]

titulos_bode = {
    'T_3.3ohm_basico.txt': '$R_L$ = 3.3 $\Omega$',
    'T_6.8ohm_basico.txt': '$R_L$ = 6.8 $\Omega$',
    'T_25ohm_basico.txt': '$R_L$ = 25 $\Omega$',
    'T_50ohm_basico.txt': '$R_L$ = 50 $\Omega$'
}

for nombre in archivos_bode:
    frecuencia, magnitud_db, fase_grados = leer_bode(ruta_dato(nombre))

    # convertimos la magnitud de dB a módulo lineal
    magnitud_lineal = 10 ** (magnitud_db / 20)

    # magnitud en lineal
    plt.figure(figsize=(7, 4.5))
    plt.semilogx(frecuencia, magnitud_lineal, color='tab:green')
    plt.xlabel('Frecuencia [Hz]')
    plt.ylabel('|T|')
    plt.title('Bode - Magnitud — ' + titulos_bode[nombre])
    plt.grid(True, which='both')
    plt.tight_layout()

    nombre_salida_mag = nombre.replace('.txt', '_magnitud.png')
    plt.savefig(os.path.join(carpeta_graficos, nombre_salida_mag))
    plt.close()

    # # fase
    # plt.figure(figsize=(7, 4.5))
    # plt.semilogx(frecuencia, fase_grados, color='tab:red')
    # plt.xlabel('Frecuencia [Hz]')
    # plt.ylabel('Fase [°]')
    # plt.title('Bode - Fase — ' + nombre)
    # plt.grid(True, which='both')
    # plt.tight_layout()
    # plt.show()