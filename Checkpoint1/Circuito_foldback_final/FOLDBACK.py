import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import re
import os

# --- estilo general "prolijo / académico", para que se vean bien en el informe ---
plt.style.use('default')

plt.rcParams.update({
    'font.size': 12,            # texto general un poco más grande que el default
    'axes.titlesize': 14,       # título de cada gráfico
    'axes.titleweight': 'bold',
    'axes.labelsize': 12,       # etiquetas de los ejes
    'legend.fontsize': 10,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': '#444444',
    'axes.linewidth': 1.0,
    'xtick.color': '#333333',
    'ytick.color': '#333333',
})

# paleta de colores fija para que cada tipo de curva se vea siempre igual
COLOR_LINEA = '#1f6f9c'      # azul
COLOR_CARGA = '#d97b29'      # naranja
COLOR_BODE = '#2e8b57'       # verde
COLOR_FOLDBACK = '#c0392b'   # rojo

# formateador para mostrar los numeros de frecuencia abreviados (1k, 10k, 1M, etc)
formateador_frecuencia = mticker.EngFormatter(unit='Hz', sep=' ')
# mismo formateador pero forzando 3 decimales, para la anotación de fc
formateador_frecuencia_3dec = mticker.EngFormatter(unit='Hz', sep=' ', places=3)

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


# función para formatear un valor numérico con hasta 3 decimales,
# sacando los ceros finales que no aportan nada (ej: "6.000" -> "6",
# "5.030" -> "5.03"), y agregarle la unidad correspondiente
def formatear_valor(valor, unidad=''):
    texto_numero = quitar_ceros_finales('%.3f' % valor)

    if unidad:
        return texto_numero + ' ' + unidad
    return texto_numero


# función chiquita que le saca los ceros finales (y el punto, si sobra)
# a un numero ya formateado como texto, ej "6.000" -> "6", "5.030" -> "5.03"
def quitar_ceros_finales(texto_numero):
    if '.' in texto_numero:
        texto_numero = texto_numero.rstrip('0').rstrip('.')
    return texto_numero


# función que le da a cada gráfico el mismo look: bordes limpios y grilla suave
def aplicar_estilo_ejes(ax=None):
    if ax is None:
        ax = plt.gca()

    # sacamos el marco de arriba y de la derecha (look más "paper", menos "excel")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.grid(True, which='major', color='gray', linewidth=0.6, alpha=0.5)
    ax.minorticks_on()
    ax.grid(True, which='minor', color='gray', linewidth=0.3, alpha=0.25)


# función para que el eje x de un gráfico de frecuencia muestre "1k", "10k", "1M"
# en vez de notacion cientifica tipo "1e4"
def formatear_eje_frecuencia(ax=None):
    if ax is None:
        ax = plt.gca()
    ax.xaxis.set_major_formatter(formateador_frecuencia)


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

    texto = 'máx: ' + formatear_valor(y_max, unidad_y)
    plt.annotate(texto, xy=(x_max, y_max), xytext=(-10, 15),
                 textcoords='offset points', fontsize=9,
                 ha='right',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor='gray', alpha=0.9))

    # dejamos un poco de aire arriba del grafico para que la anotacion entre
    limite_actual = plt.ylim()
    rango = limite_actual[1] - limite_actual[0]
    plt.ylim(limite_actual[0], limite_actual[1] + rango * 0.12)


# función para encontrar el punto donde la curva ya alcanzó su valor final
# (dentro de una tolerancia) y se queda ahí, sin volver a alejarse
def encontrar_inicio_regulacion(eje_x, eje_y, tolerancia=0.01):
    valor_final = eje_y[-1]

    for i in range(len(eje_y)):
        diferencia = abs(eje_y[i] - valor_final)
        if abs(valor_final) > 1e-12:
            diferencia_relativa = diferencia / abs(valor_final)
        else:
            diferencia_relativa = diferencia

        if diferencia_relativa <= tolerancia:
            # verificamos que desde aca en adelante se mantenga cerca del
            # valor final (para no confundir un cruce de paso con el
            # aplanamiento real)
            resto = eje_y[i:]
            diferencias_resto = np.abs(resto - valor_final)
            if abs(valor_final) > 1e-12:
                diferencias_resto = diferencias_resto / abs(valor_final)

            if np.all(diferencias_resto <= tolerancia * 3):
                return eje_x[i], eje_y[i]

    return None, None


# función para marcar en el gráfico el punto donde empieza a regular
def marcar_inicio_regulacion(eje_x, eje_y, nombre_variable, unidad_x=''):
    x_reg, y_reg = encontrar_inicio_regulacion(eje_x, eje_y)

    if x_reg is None:
        return

    plt.axvline(x=x_reg, color='#c0392b', linestyle='--', linewidth=1.2)

    texto = nombre_variable + ' = ' + formatear_valor(x_reg, unidad_x)
    plt.annotate(texto, xy=(x_reg, y_reg), xytext=(10, -30),
                 textcoords='offset points', fontsize=9,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='mistyrose',
                           edgecolor='#c0392b', alpha=0.9))


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

    plt.axvline(x=f_corte, color='#c0392b', linestyle='--', linewidth=1.2)
    plt.plot(f_corte, mag_corte, marker='o', color='#c0392b', markersize=6, zorder=5)

    # antes decia algo como "1.23e+04 Hz", ahora usamos el mismo formato
    # abreviado que el eje x (1k, 10k, 1M, etc), con 3 decimales fijos,
    # sacando los ceros finales que sobren
    texto_frecuencia = formateador_frecuencia_3dec(f_corte)
    partes_frecuencia = texto_frecuencia.split(' ')
    partes_frecuencia[0] = quitar_ceros_finales(partes_frecuencia[0])
    texto = r'$f_c$ = ' + ' '.join(partes_frecuencia)
    plt.annotate(texto, xy=(f_corte, mag_corte), xytext=(10, 15),
                 textcoords='offset points', fontsize=9,
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='mistyrose',
                           edgecolor='#c0392b', alpha=0.9))


# --- regulación de línea: un gráfico por archivo ---
archivos_linea = [
    'reglinea_3.4ohm_foldback.txt',
    'reglinea_4ohm_foldback.txt',
    'reglinea_50ohm_foldback.txt'
]

titulos_linea = {
    'reglinea_3.4ohm_foldback.txt': r'Regulación de línea — $R_L$ = 3.4 $\Omega$',
    'reglinea_4ohm_foldback.txt': r'Regulación de línea — $R_L$ = 4 $\Omega$',
    'reglinea_50ohm_foldback.txt': r'Regulación de línea — $R_L$ = 50 $\Omega$'
}

for nombre in archivos_linea:
    vreg, vo = leer_regulacion(ruta_dato(nombre))

    plt.figure(figsize=(9, 5.5))
    plt.plot(vreg, vo, color=COLOR_LINEA, linewidth=2, label='V(vo)')
    plt.xlabel(r'$V_{reg}$ [V]')
    plt.ylabel(r'$V_{o}$ [V]')
    plt.title(titulos_linea[nombre])
    aplicar_estilo_ejes()
    plt.legend(frameon=False)

    marcar_inicio_regulacion(vreg, vo, r'$V_{reg}$', 'V')
    marcar_punto_maximo(vreg, vo, 'V')

    plt.tight_layout()

    nombre_salida = nombre.replace('.txt', '.png')
    plt.savefig(os.path.join(carpeta_graficos, nombre_salida), dpi=200)

    plt.close()


# --- regulación de carga ---
rl, vo = leer_regulacion(ruta_dato('regcarga_foldback.txt'))

plt.figure(figsize=(9, 5.5))
plt.plot(rl, vo, color=COLOR_CARGA, linewidth=2, label='V(vo)')
plt.xlabel(r'$R_L$ [$\Omega$]')
plt.ylabel(r'$V_{o}$ [V]')
plt.title('Regulación de carga')
aplicar_estilo_ejes()
plt.legend(frameon=False)

marcar_inicio_regulacion(rl, vo, r'$R_L$', 'Ω')
marcar_punto_maximo(rl, vo, 'V')

plt.tight_layout()

plt.savefig(os.path.join(carpeta_graficos, 'regulacion_foldback.png'), dpi=200)
plt.close()


# --- Bode: magnitud y fase separados, un gráfico por archivo ---
archivos_bode = [
    'T(af)_4ohm_conRE_magnitud_foldback.txt',
    'T(af)_50ohm_conRE_magnitud_foldback.txt',
    'T(af)_4ohm_sinRE_magnitud_foldback.txt',
    'T(af)_50ohm_sinRE_magnitud_foldback.txt'
]

titulos_bode = {
    'T(af)_4ohm_conRE_magnitud_foldback.txt': r'$R_L$ = 4 $\Omega$',
    'T(af)_50ohm_conRE_magnitud_foldback.txt': r'$R_L$ = 50 $\Omega$',
    'T(af)_4ohm_sinRE_magnitud_foldback.txt': r'$R_L$ = 4 $\Omega$',
    'T(af)_50ohm_sinRE_magnitud_foldback.txt': r'$R_L$ = 50 $\Omega$',
}

for nombre in archivos_bode:
    frecuencia, magnitud_db, fase_grados = leer_bode(ruta_dato(nombre))

    # convertimos la magnitud de dB a módulo lineal
    magnitud_lineal = 10 ** (magnitud_db / 20)

    # magnitud en lineal
    plt.figure(figsize=(9, 5.5))
    plt.semilogx(frecuencia, magnitud_lineal, color=COLOR_BODE, linewidth=2, label='|T|')
    plt.xlabel('Frecuencia [Hz]')
    plt.ylabel('|T|')
    plt.title('Ganancia de lazo ' + titulos_bode[nombre])
    aplicar_estilo_ejes()
    formatear_eje_frecuencia()
    plt.legend(frameon=False)

    marcar_punto_maximo(frecuencia, magnitud_lineal, '')
    marcar_frecuencia_corte(frecuencia, magnitud_lineal)

    plt.tight_layout()

    nombre_salida_mag = nombre.replace('.txt', '_magnitud.png')
    plt.savefig(os.path.join(carpeta_graficos, nombre_salida_mag), dpi=200)
    plt.close()

# --- foldback: curva de protección Vo vs Io ---
rl_fb, vo_fb = leer_regulacion(ruta_dato('I_foldback_final.txt'))

# la corriente de salida se calcula como Io = Vo / RL (ley de ohm sobre la carga)
io_fb = vo_fb / rl_fb

plt.figure(figsize=(9, 5.5))
plt.plot(io_fb, vo_fb, color=COLOR_FOLDBACK, linewidth=2, label='V(vo)')
plt.xlabel(r'$I_{o}$ [A]')
plt.ylabel(r'$V_{o}$ [V]')
plt.title('Protección por Foldback')
aplicar_estilo_ejes()
plt.legend(frameon=False)

# marcamos el pico de corriente: el punto donde empieza a "doblarse"
indice_pico = np.argmax(io_fb)
io_pico = io_fb[indice_pico]
vo_pico = vo_fb[indice_pico]

plt.plot(io_pico, vo_pico, marker='o', color='black', markersize=6, zorder=5)
texto_pico = 'Io máx ≈ ' + formatear_valor(io_pico, 'A')
plt.annotate(texto_pico, xy=(io_pico, vo_pico), xytext=(10, 10),
             textcoords='offset points', fontsize=9,
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                       edgecolor='gray', alpha=0.9))

# marcamos la corriente mínima (extremo de la curva, ~cortocircuito): se
# busca el punto de Vo mínima (ahí es donde Io también toca su mínimo) y
# solo mostramos el valor de Io, para no tapar el resto del gráfico
indice_minimo = np.argmin(vo_fb)
vo_minima = vo_fb[indice_minimo]
io_minima = io_fb[indice_minimo]

plt.plot(io_minima, vo_minima, marker='o', color='black', markersize=6, zorder=5)
texto_minimo = 'Io mín ≈ ' + formatear_valor(io_minima, 'A')
plt.annotate(texto_minimo, xy=(io_minima, vo_minima), xytext=(12, -8),
             textcoords='offset points', fontsize=9, ha='left', va='top',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                       edgecolor='gray', alpha=0.9))

# dejamos algo de aire debajo de la curva para que esta etiqueta entre
limite_actual_fb = plt.ylim()
rango_fb = limite_actual_fb[1] - limite_actual_fb[0]
plt.ylim(limite_actual_fb[0] - rango_fb * 0.08, limite_actual_fb[1])

plt.tight_layout()

plt.savefig(os.path.join(carpeta_graficos, 'foldback.png'), dpi=200)
plt.close()