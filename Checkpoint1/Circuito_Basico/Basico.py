import numpy as np
import matplotlib.pyplot as plt
import re
import os

# estilo general para que los graficos se vean mas prolijos
plt.style.use('default')

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


# función chiquita para marcar el punto maximo de una curva con un circulo y un texto
def marcar_punto_maximo(eje_x, eje_y, unidad_y):
    indice_max = np.argmax(eje_y)
    x_max = eje_x[indice_max]
    y_max = eje_y[indice_max]

    plt.plot(x_max, y_max, marker='o', color='black', markersize=6, zorder=5)

    texto = 'máx: ' + str(round(y_max, 3)) + ' ' + unidad_y
    plt.annotate(texto, xy=(x_max, y_max), xytext=(-10, 15),
                 textcoords='offset points', fontsize=9,
                 ha='right',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor='gray', alpha=0.9))

    # dejamos un poco de aire arriba del grafico para que la anotacion entre
    limite_actual = plt.ylim()
    rango = limite_actual[1] - limite_actual[0]
    plt.ylim(limite_actual[0], limite_actual[1] + rango * 0.12)


# función para encontrar el punto donde la curva empieza a regular
# (donde la pendiente deja de ser pronunciada y se aplana, DESPUES de la rampa)
def encontrar_inicio_regulacion(eje_x, eje_y):
    # calculamos la pendiente entre cada par de puntos consecutivos
    pendientes = []
    for i in range(1, len(eje_x)):
        dx = eje_x[i] - eje_x[i - 1]
        dy = eje_y[i] - eje_y[i - 1]
        if dx == 0:
            pendiente = 0
        else:
            pendiente = dy / dx
        pendientes.append(pendiente)
    pendientes = np.array(pendientes)

    pendiente_maxima = np.max(pendientes)
    umbral = pendiente_maxima * 0.1  # 10% de la pendiente maxima

    # primero buscamos donde arranca la rampa (donde la pendiente ya es
    # significativa), para no confundir la zona plana del principio con el
    # aplanamiento real de despues
    umbral_rampa = pendiente_maxima * 0.3
    indice_arranque_rampa = None
    for i in range(len(pendientes)):
        if pendientes[i] > umbral_rampa:
            indice_arranque_rampa = i
            break

    if indice_arranque_rampa is None:
        return None, None

    # recien a partir de ahi buscamos donde la pendiente vuelve a caer
    # y se mantiene baja (el aplanamiento real, despues de la rampa)
    indice_inicio = None
    for i in range(indice_arranque_rampa, len(pendientes)):
        if pendientes[i] < umbral:
            ventana = pendientes[i:i + 20]
            if len(ventana) > 0 and np.mean(ventana) < umbral:
                indice_inicio = i + 1
                break

    if indice_inicio is None:
        return None, None

    return eje_x[indice_inicio], eje_y[indice_inicio]


# función para marcar en el gráfico el punto donde empieza a regular
def marcar_inicio_regulacion(eje_x, eje_y, nombre_variable):
    x_reg, y_reg = encontrar_inicio_regulacion(eje_x, eje_y)

    if x_reg is None:
        return

    plt.axvline(x=x_reg, color='red', linestyle='--', linewidth=1)

    texto = nombre_variable + ' = ' + str(round(x_reg, 2))
    plt.annotate(texto, xy=(x_reg, y_reg), xytext=(10, -30),
                 textcoords='offset points', fontsize=9,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='mistyrose',
                           edgecolor='red', alpha=0.9))


# función para encontrar la frecuencia de corte (donde |T| cae a maximo/raiz(2))
def encontrar_frecuencia_corte(frecuencia, magnitud_lineal):
    valor_maximo = np.max(magnitud_lineal)
    umbral_corte = valor_maximo / np.sqrt(2)

    # buscamos el primer punto, despues del maximo, donde la magnitud
    # cae por debajo del umbral de corte
    indice_maximo = np.argmax(magnitud_lineal)

    indice_corte = None
    for i in range(indice_maximo, len(magnitud_lineal)):
        if magnitud_lineal[i] < umbral_corte:
            indice_corte = i
            break

    if indice_corte is None:
        return None, None

    return frecuencia[indice_corte], magnitud_lineal[indice_corte]


# función para marcar en el gráfico la frecuencia de corte
def marcar_frecuencia_corte(frecuencia, magnitud_lineal):
    f_corte, mag_corte = encontrar_frecuencia_corte(frecuencia, magnitud_lineal)

    if f_corte is None:
        return

    plt.axvline(x=f_corte, color='red', linestyle='--', linewidth=1)
    plt.plot(f_corte, mag_corte, marker='o', color='red', markersize=6, zorder=5)

    texto = 'f_corte ≈ ' + '{:.2e}'.format(f_corte) + ' Hz'
    plt.annotate(texto, xy=(f_corte, mag_corte), xytext=(10, 15),
                 textcoords='offset points', fontsize=9,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='mistyrose',
                           edgecolor='red', alpha=0.9))


# --- regulación de línea: un gráfico por archivo ---
archivos_linea = [
    'reglinea_3.3_basico.txt',
    'reglinea_6.8_basico.txt',
    'reglinea_25_basico.txt',
    'reglinea_50_basico.txt'
]

titulos_linea = {
    'reg_linea_basico.txt': r'Regulación de línea',
    'reglinea_3.3_basico.txt': r'Regulación de línea — $R_L$ = 3.3 $\Omega$',
    'reglinea_6.8_basico.txt': r'Regulación de línea — $R_L$ = 6.8 $\Omega$',
    'reglinea_25_basico.txt': r'Regulación de línea — $R_L$ = 25 $\Omega$',
    'reglinea_50_basico.txt': r'Regulación de línea — $R_L$ = 50 $\Omega$'
}

for nombre in archivos_linea:
    vreg, vo = leer_regulacion(ruta_dato(nombre))

    plt.figure(figsize=(11, 6))
    plt.plot(vreg, vo, color='tab:blue', label='V(vo)')
    plt.xlabel(r'$V_{reg}$ [V]')
    plt.ylabel(r'$V_{o}$ [V]')
    plt.title(titulos_linea[nombre])
    plt.grid(True, which='major', color='gray', linewidth=0.6)
    plt.minorticks_on()
    plt.grid(True, which='minor', color='gray', linewidth=0.3, alpha=0.5)
    plt.legend()

    marcar_inicio_regulacion(vreg, vo, r'$V_{reg}$')
    marcar_punto_maximo(vreg, vo, 'V')

    plt.tight_layout()

    nombre_salida = nombre.replace('.txt', '.png')
    plt.savefig(os.path.join(carpeta_graficos, nombre_salida), dpi=150)

    plt.close()


# --- regulación de carga ---
rl, vo = leer_regulacion(ruta_dato('regcarga_basico.txt'))

plt.figure(figsize=(11, 6))
plt.plot(rl, vo, color='tab:orange', label='V(vo)')
plt.xlabel(r'$R_L$ [$\Omega$]')
plt.ylabel(r'$V_{o}$ [V]')
plt.title('Regulación de carga')
plt.grid(True, which='major', color='gray', linewidth=0.6)
plt.minorticks_on()
plt.grid(True, which='minor', color='gray', linewidth=0.3, alpha=0.5)
plt.legend()

marcar_inicio_regulacion(rl, vo, r'$R_L$')
marcar_punto_maximo(rl, vo, 'V')

plt.tight_layout()

plt.savefig(os.path.join(carpeta_graficos, 'regulacion_carga.png'), dpi=150)
plt.close()


# --- Bode: magnitud y fase separados, un gráfico por archivo ---
archivos_bode = [
    'T_3.3ohm_basico.txt',
    'T_6.8ohm_basico.txt',
    'T_25ohm_basico.txt',
    'T_50ohm_basico.txt'
]

titulos_bode = {
    'T_3.3ohm_basico.txt': r'$R_L$ = 3.3 $\Omega$',
    'T_6.8ohm_basico.txt': r'$R_L$ = 6.8 $\Omega$',
    'T_25ohm_basico.txt': r'$R_L$ = 25 $\Omega$',
    'T_50ohm_basico.txt': r'$R_L$ = 50 $\Omega$'
}

for nombre in archivos_bode:
    frecuencia, magnitud_db, fase_grados = leer_bode(ruta_dato(nombre))

    # convertimos la magnitud de dB a módulo lineal
    magnitud_lineal = 10 ** (magnitud_db / 20)

    # magnitud en lineal
    plt.figure(figsize=(11, 6))
    plt.semilogx(frecuencia, magnitud_lineal, color='tab:green', label='|T|')
    plt.xlabel('Frecuencia [Hz]')
    plt.ylabel('|T|')
    plt.title('Ganancia de lazo ' + titulos_bode[nombre])
    plt.grid(True, which='major', color='gray', linewidth=0.6)
    plt.minorticks_on()
    plt.grid(True, which='minor', color='gray', linewidth=0.3, alpha=0.5)
    plt.legend()

    marcar_punto_maximo(frecuencia, magnitud_lineal, '')
    marcar_frecuencia_corte(frecuencia, magnitud_lineal)

    plt.tight_layout()

    nombre_salida_mag = nombre.replace('.txt', '_magnitud.png')
    plt.savefig(os.path.join(carpeta_graficos, nombre_salida_mag), dpi=150)
    plt.close()

