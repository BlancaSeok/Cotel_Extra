import random
import re
import string
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
from functools import wraps
import logging
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import make_response
import io
import base64
import uuid
import json
from werkzeug.utils import secure_filename

# ============================================================
app = Flask(__name__)
app.secret_key = ''

# ---- MAIL CONFIG ----
app.config['MAIL_SERVER']   = ''
app.config['MAIL_PORT']     = 
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS']  = 
mail = Mail(app)

# ---- UPLOAD CONFIG ----
UPLOAD_FOLDER = 'uploads/documentos'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear carpetas si no existen
os.makedirs('uploads', exist_ok=True)
os.makedirs('uploads/documentos', exist_ok=True)


# ============================================================
# BASE DE DATOS
# ============================================================

def get_db_connection():
    return psycopg2.connect(
        dbname="COTEL_RL2",
        user="",
        password="",
        host="localhost"
    )
    


def obtener_roles():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id_rol, rol FROM roles")
        return cur.fetchall()
    except Exception as e:
        flash(f'Error al obtener los roles: {str(e)}', 'danger')
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def obtener_zonas():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id, nombre FROM zonas WHERE activo = TRUE ORDER BY nombre")
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_zonas: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def obtener_zona_reclamo(reclamo_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT u.zona_id, z.nombre
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN zonas z ON u.zona_id = z.id
            WHERE r.id = %s
        """, (reclamo_id,))
        row = cur.fetchone()
        return (row[0], row[1]) if row else (None, None)
    except Exception as e:
        print(f"ERROR obtener_zona_reclamo: {e}")
        return (None, None)
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def obtener_contratos_usuario(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT c.id, c.numero_contrato, c.tipo_servicio, c.direccion,
                   c.telefono_referencia, c.telefono_factura, z.nombre AS zona
            FROM contratos c
            LEFT JOIN zonas z ON c.zona_id = z.id
            WHERE c.usuario_id = %s AND c.activo = TRUE
            ORDER BY c.numero_contrato
        """, (usuario_id,))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_contratos_usuario: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def obtener_perfil_completo(usuario_id, rol):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT u.usuario_id, u.nombre, u.apellido, u.correo, u.telefono,
                   u.foto_perfil, u.zona_id, z.nombre AS zona_nombre
            FROM usuarios u
            LEFT JOIN zonas z ON u.zona_id = z.id
            WHERE u.usuario_id = %s
        """, (usuario_id,))
        row = cur.fetchone()
        if not row:
            return None

        zona_id_real, zona_nombre_real = row[6], row[7]

        if rol == 'tecnico':
            cur.execute("""
                SELECT t.zona_id, z.nombre
                FROM tecnicos t
                LEFT JOIN zonas z ON t.zona_id = z.id
                WHERE t.usuario_id = %s AND t.activo = TRUE
            """, (usuario_id,))
            trow = cur.fetchone()
            if trow:
                zona_id_real, zona_nombre_real = trow[0], trow[1]

        return {
            'usuario_id': row[0], 'nombre': row[1], 'apellido': row[2],
            'correo': row[3], 'telefono': row[4], 'foto_perfil': row[5],
            'zona_id': zona_id_real, 'zona_nombre': zona_nombre_real,
        }
    except Exception as e:
        print(f"ERROR obtener_perfil_completo: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def ejecutar_consulta(query, params=None):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        return cur.fetchall()
    except Exception as e:
        flash(f'Error al ejecutar la consulta: {str(e)}', 'danger')
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()

#fotos de perfil guardado en el sistema 
UPLOAD_FOLDER_PERFILES = 'static/uploads/perfiles'
ALLOWED_EXTENSIONS_FOTO = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FOTO_SIZE_MB = 3
os.makedirs(UPLOAD_FOLDER_PERFILES, exist_ok=True)

def allowed_foto(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_FOTO
# Helper para convertir el nombre en texto seguro para archivo

import unicodedata

def slugify_nombre(texto):
    """Convierte 'Nombre Completo' en 'nombre:completo' — sin tildes, espacios ni símbolos."""
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = texto.lower().strip()
    texto = re.sub(r'[^a-z0-9]+', '_', texto)
    texto = re.sub(r'_+', '_', texto).strip('_')
    return texto or 'usuario'


# ============================================================
# UTILIDADES
# ============================================================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generar_codigo(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def validar_contraseña(contraseña):
    if len(contraseña) < 8: return False
    if not any(c.isupper() for c in contraseña): return False
    if not any(c.islower() for c in contraseña): return False
    if not any(c.isdigit() for c in contraseña): return False
    if not any(c in "!@#$%^&*()_+" for c in contraseña): return False
    return True


def obtener_nombre_lugar(latitud, longitud, intentos=3):
    if intentos == 0:
        return 'Lugar desconocido'
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitud}&lon={longitud}&zoom=18&addressdetails=1"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('display_name', 'Lugar desconocido')
        return obtener_nombre_lugar(latitud, longitud, intentos - 1)
    except Exception as e:
        print(f"Error al obtener el nombre del lugar: {e}")
        return 'Lugar desconocido'


# ============================================================
# AUTENTICACIÓN
# ============================================================

@app.route('/inicio_sesion', methods=['GET', 'POST'])
def inicio_sesion():
    if request.method == 'POST':
        action = request.form.get('action')

        # ---------- LOGIN ----------
        if action == 'login':
            codigo_login = (request.form.get('codigo_login') or '').strip()
            contraseña   = request.form.get('contraseña_login')
 
            usuario_id = buscar_usuario_id_por_codigo(codigo_login)
            if not usuario_id:
                flash('Código de acceso incorrecto.', 'danger')
                return redirect(url_for('inicio_sesion'))
 
            conn = cur = None
            try:
                conn = get_db_connection()
                cur  = conn.cursor()
                cur.execute("""
                    SELECT u.usuario_id, u.nombre, r.rol, u.contraseña, u.verificado
                    FROM usuarios u
                    JOIN roles r ON u.id_rol = r.id_rol
                    WHERE u.usuario_id = %s
                """, (usuario_id,))
                user = cur.fetchone()
 
                if user and check_password_hash(user[3], contraseña):
                    if user[4]:
                        session['usuario_id'] = user[0]
                        session['nombre']     = user[1]
                        session['rol']        = user[2].strip().lower() if user[2] else ''
 
                        rol = session['rol']
                        if rol == 'cliente':
                            return redirect(url_for('dashboard_cliente'))
                        elif rol == 'help_desk':
                            return redirect(url_for('dashboard_soporte'))
                        elif rol == 'tecnico':
                            return redirect(url_for('dashboard_tecnico'))
                        elif rol in ('admin', 'administrador'):
                            return redirect(url_for('dashboard_admin'))
                        elif rol == 'nodo_internet':
                            return redirect(url_for('dashboard_nodo_internet'))
                        elif rol == 'turno_planta_interna':
                            return redirect(url_for('dashboard_planta_interna'))
                        elif rol == 'calidad':
                            return redirect(url_for('dashboard_calidad'))
                        elif rol in ('jefe_primera_instancia', 'jefe_segunda_instancia'):
                            return redirect(url_for('dashboard_jefe'))
                        elif rol == 'jefe_help_desk':
                            return redirect(url_for('dashboard_jefe_helpdesk'))
                        elif rol in ('jefe_dra', 'jefe_drc'):
                            return redirect(url_for('dashboard_jefe_especialidad'))
                        else:
                            flash('Rol desconocido. Contacta al administrador.', 'danger')
                            return redirect(url_for('inicio_sesion'))
                    
                    
                    else:
                        flash('Debes verificar tu correo antes de iniciar sesión.', 'warning')
                else:
                    flash('Código de acceso o contraseña incorrectos.', 'danger')
            except Exception as e:
                flash(f'Error de conexión: {str(e)}', 'danger')
            finally:
                if cur:  cur.close()
                if conn: conn.close()

        # ---------- REGISTRO ----------
        
         
        elif action == 'register':
            nombre                  = request.form.get('nombre')
            apellido                = request.form.get('apellido')
            correo                  = request.form.get('correo')
            contraseña              = request.form.get('contraseña')
            confirmacion_contraseña = request.form.get('confirmacion_contraseña')
            telefono                = request.form.get('telefono')
            id_rol                  = request.form.get('rol')
            codigo_cliente          = (request.form.get('codigo_cliente') or '').strip()
            codigo_empleado         = (request.form.get('codigo_empleado') or '').strip()
            tipo_tecnico            = (request.form.get('tipo_tecnico') or '').strip().upper()
 
            if not all([nombre, apellido, correo, contraseña, confirmacion_contraseña, telefono, id_rol]):
                flash('Todos los campos son obligatorios.', 'danger')
                return redirect(url_for('inicio_sesion'))
 
            if contraseña != confirmacion_contraseña:
                flash('Las contraseñas no coinciden.', 'danger')
                return redirect(url_for('inicio_sesion'))
 
            if not validar_contraseña(contraseña):
                flash('La contraseña debe tener al menos 8 caracteres, incluyendo mayúscula, minúscula, número y símbolo.', 'danger')
                return redirect(url_for('inicio_sesion'))
 
            contraseña_hash     = generate_password_hash(contraseña)
            codigo_verificacion = generar_codigo()
            conn = cur = None
            try:
                conn = get_db_connection()
                cur  = conn.cursor()
 
                cur.execute("SELECT COUNT(*) FROM usuarios WHERE correo = %s", (correo,))
                if cur.fetchone()[0] > 0:
                    flash('Este correo ya está registrado.', 'danger')
                    return redirect(url_for('inicio_sesion'))
 
                codigo_cliente_id  = None
                codigo_empleado_id = None
                rol_nombre         = None
                rol_lower          = None
 
             
                if id_rol == 'JEFE':
                    if not codigo_empleado:
                        flash('Debes ingresar el código de verificación de empleado.', 'danger')
                        return redirect(url_for('inicio_sesion'))
 
                    cur.execute("""
                        SELECT id, id_rol, rol FROM codigos_registro_empleado
                        WHERE codigo = %s AND activo = TRUE AND usado = FALSE
                          AND rol IN ('jefe_primera_instancia', 'jefe_segunda_instancia')
                    """, (codigo_empleado,))
                    fila = cur.fetchone()
                    if not fila:
                        flash('El código de verificación es inválido, ya fue usado, o no corresponde a un cargo de Jefe.', 'danger')
                        return redirect(url_for('inicio_sesion'))
 
                    codigo_empleado_id, id_rol, rol_nombre = fila[0], fila[1], fila[2]
 
                    if id_rol is None:
                        flash('Este código no tiene un rol asignado correctamente en el sistema. Contacta al administrador.', 'danger')
                        return redirect(url_for('inicio_sesion'))
 
                    rol_lower = rol_nombre.strip().lower()
 
                # ── FLUJO NORMAL: cliente y demás roles de empleado ──
                else:
                    cur.execute("SELECT rol FROM roles WHERE id_rol = %s", (id_rol,))
                    rol_result = cur.fetchone()
                    if not rol_result:
                        flash('Rol no válido.', 'danger')
                        return redirect(url_for('inicio_sesion'))
                    rol_nombre = rol_result[0]
                    rol_lower  = rol_nombre.strip().lower()
 
                    if rol_lower == 'cliente':
                        if not codigo_cliente:
                            flash('Debes ingresar tu código de verificación de cliente.', 'danger')
                            return redirect(url_for('inicio_sesion'))
                        cur.execute("""
                            SELECT id FROM codigos_registro_cliente
                            WHERE codigo = %s AND activo = TRUE AND usado = FALSE
                        """, (codigo_cliente,))
                        fila = cur.fetchone()
                        if not fila:
                            flash('El código de cliente es inválido o ya fue usado.', 'danger')
                            return redirect(url_for('inicio_sesion'))
                        codigo_cliente_id = fila[0]
 
                    elif rol_lower in ('help_desk', 'tecnico', 'nodo_internet', 'calidad', 'administrador',
                                        'jefe_help_desk', 'jefe_dra', 'jefe_drc', 'turno_planta_interna'):
                        if not codigo_empleado:
                            flash('Debes ingresar el código de verificación de empleado.', 'danger')
                            return redirect(url_for('inicio_sesion'))
                        cur.execute("""
                            SELECT id FROM codigos_registro_empleado
                            WHERE codigo = %s AND rol = %s AND activo = TRUE AND usado = FALSE
                        """, (codigo_empleado, rol_lower))
                        fila = cur.fetchone()
                        if not fila:
                            flash('El código de verificación es inválido, ya fue usado, o no corresponde a este rol.', 'danger')
                            return redirect(url_for('inicio_sesion'))
                        codigo_empleado_id = fila[0]
 
                        if rol_lower == 'tecnico' and tipo_tecnico not in ('RA', 'RC'):
                            flash('Selecciona si el técnico es de Redes de Acceso (RA) o Redes de Cableado (RC).', 'danger')
                            return redirect(url_for('inicio_sesion'))
 
                # ── Insertar usuario (SIN numero_contrato) ──────────────
                cur.execute("""
                    INSERT INTO usuarios
                        (nombre, apellido, correo, contraseña, telefono,
                         codigo_verificacion, verificado, fecha_registro, activo, id_rol)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),%s,%s)
                    RETURNING usuario_id
                """, (nombre, apellido, correo, contraseña_hash, telefono,
                      codigo_verificacion, False, True, id_rol))
                nuevo_usuario_id = cur.fetchone()[0]
 
                if codigo_cliente_id:
                    cur.execute("""
                        UPDATE codigos_registro_cliente
                        SET usado = TRUE, usuario_id = %s, fecha_uso = NOW()
                        WHERE id = %s
                    """, (nuevo_usuario_id, codigo_cliente_id))
 
                if codigo_empleado_id:
                    cur.execute("""
                        UPDATE codigos_registro_empleado
                        SET usado = TRUE, usuario_id = %s, fecha_uso = NOW()
                        WHERE id = %s
                    """, (nuevo_usuario_id, codigo_empleado_id))
 
                conn.commit()
 
                if rol_lower == 'help_desk':
                    asegurar_registro_empleado_soporte(nuevo_usuario_id)
                elif rol_lower == 'tecnico':
                    asegurar_registro_tecnico(nuevo_usuario_id, tipo_tecnico=tipo_tecnico)
                try:
                    msg = Message(
                        subject='Verificación de cuenta COTEL RL',
                        sender=('COTEL RL', app.config['MAIL_USERNAME']),
                        recipients=[correo]
                    )
                    msg.html = f'<h1>Verificación de cuenta</h1><p>Tu código: <strong>{codigo_verificacion}</strong></p>'
                    mail.send(msg)
                except Exception as mail_error:
                    print(f"Error enviando correo: {mail_error}")
                    flash('Usuario registrado, pero hubo un problema al enviar el correo de verificación.', 'warning')
 
                session['correo_verificacion'] = correo
                flash(f'¡Registro exitoso! Revisa tu correo. Rol: {rol_nombre}. '
                      f'Guarda bien tu código de acceso: lo necesitarás para iniciar sesión.', 'success')
                return redirect(url_for('verificar_codigo_registro'))
 
            except Exception as e:
                if conn: conn.rollback()
                flash(f'Error al registrar: {str(e)}', 'danger')
            finally:
                if cur:  cur.close()
                if conn: conn.close()
 
 
    roles = obtener_roles()
    return render_template('inicio_sesion.html', roles=roles)


@app.route('/verificar_codigo_registro', methods=['GET', 'POST'])
def verificar_codigo_registro():
    correo = session.get('correo_verificacion')
    if request.method == 'POST':
        codigo_ingresado = request.form['codigo']
        conn = cur = None
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("SELECT codigo_verificacion FROM usuarios WHERE correo = %s", (correo,))
            codigo_correcto = cur.fetchone()
            if codigo_correcto and codigo_correcto[0].strip() == codigo_ingresado.strip():
                cur.execute("UPDATE usuarios SET verificado = TRUE WHERE correo = %s", (correo,))
                conn.commit()
                flash('Cuenta verificada correctamente.', 'success')
                return redirect(url_for('login_register'))
            else:
                flash('El código ingresado es incorrecto.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            if cur:  cur.close()
            if conn: conn.close()
    return render_template('verificar_codigo_registro.html')


@app.route('/recuperar_contraseña', methods=['GET', 'POST'])
def recuperar_contraseña():
    if request.method == 'POST':
        correo = request.form['correo']
        conn = cur = None
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
            user = cur.fetchone()
            if user:
                token = generar_codigo(32)
                cur.execute("UPDATE usuarios SET token_recuperacion = %s WHERE correo = %s", (token, correo))
                conn.commit()
                msg = Message(
                    subject='Recuperación de Contraseña',
                    sender=('COTEL RL', app.config['MAIL_USERNAME']),
                    recipients=[correo]
                )
                msg.html = f'''<h1>Recuperación de Contraseña</h1>
                    <a href="{url_for('restablecer_contraseña', token=token, _external=True)}">Restablecer Contraseña</a>'''
                mail.send(msg)
                flash('Enlace de recuperación enviado a tu correo.', 'success')
            else:
                flash('No se encontró una cuenta con ese correo.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            if cur:  cur.close()
            if conn: conn.close()
    return render_template('recuperar_contraseña.html')


@app.route('/restablecer_contraseña/<token>', methods=['GET', 'POST'])
def restablecer_contraseña(token):
    if request.method == 'POST':
        contraseña             = request.form['contraseña']
        confirmacion_contraseña = request.form['confirmacion_contraseña']
        if contraseña != confirmacion_contraseña:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('restablecer_contraseña.html', token=token)
        if not validar_contraseña(contraseña):
            flash('Contraseña débil. Debe tener mayúscula, minúscula, número y símbolo.', 'danger')
            return render_template('restablecer_contraseña.html', token=token)

        contraseña_hash = generate_password_hash(contraseña)
        conn = cur = None
        try:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute("SELECT usuario_id FROM usuarios WHERE token_recuperacion = %s", (token,))
            user = cur.fetchone()
            if user:
                cur.execute("""
                    UPDATE usuarios SET contraseña = %s, token_recuperacion = NULL
                    WHERE usuario_id = %s
                """, (contraseña_hash, user[0]))
                conn.commit()
                flash('Contraseña restablecida correctamente.', 'success')
                return redirect(url_for('inicio_sesion'))
            else:
                flash('Token inválido o expirado.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
        finally:
            if cur:  cur.close()
            if conn: conn.close()
    return render_template('restablecer_contraseña.html', token=token)


@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('inicio_sesion'))


# ============================================================
# RUTAS PRINCIPALES
# ============================================================

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/login_register')
def login_register():
    return redirect(url_for('inicio_sesion'))


# ============================================================
# FUNCIONES AUXILIARES — CLIENTE
# ============================================================

def obtener_servicios_usuario(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT s.id, s.tipo_servicio, s.numero_servicio, s.plan, s.estado,
                   s.fecha_contratacion, s.monto_mensual, s.direccion_instalacion
            FROM servicios s
            WHERE s.usuario_id = %s AND s.estado = 'activo'
            ORDER BY s.fecha_contratacion DESC
        """, (usuario_id,))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_servicios_usuario: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()
        
 
 
def obtener_pagos_recientes(usuario_id, limit=5):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT p.id, p.monto, p.fecha_pago, p.metodo_pago, p.estado, p.referencia
            FROM pagos p
            WHERE p.usuario_id = %s
            ORDER BY p.fecha_pago DESC
            LIMIT %s
        """, (usuario_id, limit))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_pagos_recientes: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()



def obtener_reclamos_usuario(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, tipo_reclamo, titulo, descripcion, estado,
                   fecha_creacion, fecha_resolucion, servicio_afectado,
                   problema_especifico, ubicacion_cliente, numero_cliente,
                   estado_cuenta, monto_adeudado, prioridad
            FROM reclamos
            WHERE usuario_id = %s
            ORDER BY fecha_creacion DESC
        """, (usuario_id,))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_reclamos_usuario: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def obtener_info_usuario_completa(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT usuario_id, nombre, apellido, correo, telefono,
                   direccion, numero_cliente
            FROM usuarios WHERE usuario_id = %s
        """, (usuario_id,))
        return cur.fetchone()
    except Exception as e:
        print(f"ERROR obtener_info_usuario_completa: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def es_turno_nocturno(momento=None):
    """
    (tabla feriados).
    explícitamente porque el servidor corre en UTC
    (igual que ya hace `fuera_de_horario` con NOW() AT TIME ZONE 'America/La_Paz').
    Esto es DISTINTO de `fuera_de_horario` (ventana 8:00-20:00, otro propósito
    ya existente) — no se deben confundir.
    """
    if momento is None:
        momento = datetime.now(ZoneInfo('America/La_Paz'))
    elif momento.tzinfo is None:
        
        pass

    hora = momento.hour + momento.minute / 60
    es_horario_nocturno = (hora >= 22) or (hora < 8.5)
    es_fin_de_semana = momento.weekday() in (5, 6)  

    if es_horario_nocturno or es_fin_de_semana:
        return True

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT 1 FROM feriados WHERE fecha = %s", (momento.date(),))
        return cur.fetchone() is not None
    except Exception as e:
        print(f"ERROR es_turno_nocturno (feriados): {e}")
        return False
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def obtener_estado_cuenta_cliente(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN estado IN ('pendiente','vencido') THEN total ELSE 0 END), 0) AS monto_adeudado,
                CASE
                    WHEN COUNT(CASE WHEN estado = 'vencido' THEN 1 END) > 0 THEN 'mora'
                    WHEN COUNT(CASE WHEN estado = 'pendiente' THEN 1 END) > 0 THEN 'pendiente'
                    ELSE 'al_dia'
                END AS estado_cuenta
            FROM facturas
            WHERE usuario_id = %s
        """, (usuario_id,))
        resultado = cur.fetchone()
        return resultado if resultado else (0, 'al_dia')
    except Exception as e:
        print(f"ERROR obtener_estado_cuenta_cliente: {e}")
        return (0, 'al_dia')
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def buscar_usuario_id_por_codigo(codigo):
    """
    Busca en ambas tablas de códigos (empleado y cliente) y
    devuelve el usuario_id vinculado a ese código, si existe y
    ya fue usado (es decir, ya hay una cuenta creada con él).
    Devuelve None si el código no existe o no está vinculado.
    """
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT usuario_id FROM codigos_registro_empleado
            WHERE codigo = %s AND usado = TRUE AND usuario_id IS NOT NULL
            UNION
            SELECT usuario_id FROM codigos_registro_cliente
            WHERE codigo = %s AND usado = TRUE AND usuario_id IS NOT NULL
        """, (codigo, codigo))
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"ERROR buscar_usuario_id_por_codigo: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def asegurar_registro_empleado_soporte(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM empleados_soporte WHERE usuario_id = %s", (usuario_id,))
        if not cur.fetchone():
            cur.execute("SELECT nombre || ' ' || apellido FROM usuarios WHERE usuario_id = %s", (usuario_id,))
            row = cur.fetchone()
            cur.execute("""
                INSERT INTO empleados_soporte (usuario_id, nombre_completo, especialidad, activo, carga_trabajo)
                VALUES (%s, %s, 'general', TRUE, 0)
            """, (usuario_id, row[0] if row else 'Agente Soporte'))
            conn.commit()
            print(f"INFO: empleado_soporte creado para usuario_id={usuario_id}")
    except Exception as e:
        print(f"ERROR asegurar_registro_empleado_soporte: {e}")
        if conn: conn.rollback()
    finally:
        if cur:  cur.close()
        if conn: conn.close()
# ============================================================
# DASHBOARD CLIENTE
# ============================================================

@app.route('/dashboard_cliente')
def dashboard_cliente():
    if 'usuario_id' not in session or session.get('rol', '').lower() != 'cliente':
        flash('Debes iniciar sesión como cliente.', 'warning')
        return redirect(url_for('inicio_sesion'))
 
    usuario_id      = session['usuario_id']
    servicios       = obtener_servicios_usuario(usuario_id)
    pagos_recientes = obtener_pagos_recientes(usuario_id)
    monto_adeudado, estado_cuenta = obtener_estado_cuenta_cliente(session['usuario_id'])
    facturas_cliente = obtener_facturas_usuario(session['usuario_id'])
    facturas_vencidas = sum(1 for f in facturas_cliente if f[5] == 'vencido')
 
    return render_template('dashboard_cliente.html',
                           servicios=servicios,
                           pagos_recientes=pagos_recientes,
                           nombre_usuario=session.get('nombre', ''),
                           monto_adeudado=monto_adeudado,
                           estado_cuenta=estado_cuenta,
                           facturas_vencidas=facturas_vencidas)
 
 

#__________________________________________________________________________________
# ============================================================
# ZONAS — HELP DESK 

@app.route('/api/soporte/fallas_por_zona')
def api_fallas_por_zona():
    if 'usuario_id' not in session or not verificar_rol(
        'help_desk', 'jefe_help_desk', 'jefe_dra', 'jefe_drc', 'tecnico', 'turno_planta_interna'
    ):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        ESTADOS_PROCESO = ('abierto', 'en_proceso', 'en_diagnostico',
                            'pendiente_asignacion', 'falla_masiva')
 
        cur.execute("SELECT id, nombre FROM zonas WHERE activo = TRUE ORDER BY nombre")
        todas_zonas = cur.fetchall()
 
        zonas = {nombre: {'total': 0, 'en_proceso': 0} for _id, nombre in todas_zonas}
        zonas['Sin zona'] = {'total': 0, 'en_proceso': 0}
 
        cur.execute("""
            SELECT z.nombre, r.estado
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN zonas z ON u.zona_id = z.id
        """)
        for nombre_zona, estado in cur.fetchall():
            clave = nombre_zona if nombre_zona else 'Sin zona'
            if clave not in zonas:
                zonas[clave] = {'total': 0, 'en_proceso': 0}
            zonas[clave]['total'] += 1
            if estado in ESTADOS_PROCESO:
                zonas[clave]['en_proceso'] += 1
 
        return jsonify({'success': True, 'zonas': zonas})
    except Exception as e:
        print(f"ERROR api_fallas_por_zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 

@app.route('/api/soporte/fallas_recientes')
def api_soporte_fallas_recientes():
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'jefe_help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(f"""
            SELECT
                r.id, u.nombre, u.apellido, r.tipo_reclamo, r.titulo,
                r.estado, r.fecha_creacion, r.prioridad,
                COALESCE(ut.nombre || ' ' || ut.apellido, es.nombre_completo, '—') AS agente_asignado,
                r.servicio_afectado, r.fuera_de_horario,
                {SQL_FECHA_INICIO_ETAPA} AS fecha_inicio_etapa,
                r.fecha_resolucion
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN empleados_soporte es ON r.asignado_a = es.id
            LEFT JOIN tecnicos t           ON r.asignado_a = t.id
            LEFT JOIN usuarios ut          ON t.usuario_id  = ut.usuario_id
            WHERE (
                r.estado IN ('abierto','en_proceso','en_diagnostico','pendiente_asignacion','falla_masiva',
                              'pendiente_triage','pendiente_revision_especialidad')
                OR (
                    r.estado IN ('resuelto','resuelto_tecnico','resuelto_remoto','liberado','cerrado','auditado')
                    AND (r.fecha_resolucion IS NULL OR r.fecha_resolucion >= NOW() - INTERVAL '24 hours')
                )
            )
            ORDER BY
                CASE r.estado
                    WHEN 'abierto' THEN 1 WHEN 'en_diagnostico' THEN 2
                    WHEN 'pendiente_asignacion' THEN 3 WHEN 'falla_masiva' THEN 3
                    WHEN 'en_proceso' THEN 4 ELSE 5
                END,
                CASE r.prioridad
                    WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 WHEN 'baja' THEN 4
                END,
                r.fecha_creacion DESC
            LIMIT 15
        """)
        filas = cur.fetchall()

        cur.execute("SELECT COUNT(*) FROM reclamos")
        total_fallas = cur.fetchone()[0]
        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE estado IN ('en_proceso','en_diagnostico','pendiente_asignacion','falla_masiva')
        """)
        fallas_en_proceso = cur.fetchone()[0]

        return jsonify({
            'success': True,
            'total_fallas': total_fallas,
            'fallas_en_proceso': fallas_en_proceso,
            'reclamos': [
                {
                    'id': f[0], 'nombre': f[1], 'apellido': f[2],
                    'estado': f[5], 'prioridad': f[7], 'titulo': f[4],
                    'agente': f[8], 'servicio': f[9],
                    'fecha_creacion': f[6].strftime('%Y-%m-%dT%H:%M:%S') if f[6] else None,
                    'fuera_de_horario': f[10] if len(f) > 10 else False,
                    'fecha_inicio_etapa': f[11].isoformat() if len(f) > 11 and f[11] else None,
                    'fecha_resolucion': f[12].strftime('%Y-%m-%dT%H:%M:%S') if len(f) > 12 and f[12] else None,
                }
                for f in filas
            ]
        })
    except Exception as e:
        print(f"ERROR api_soporte_fallas_recientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/reclamos_por_zona/<zona>')
def api_soporte_reclamos_por_zona(zona):
    if 'usuario_id' not in session or not verificar_rol(
        'help_desk', 'jefe_primera_instancia', 'jefe_segunda_instancia', 'tecnico', 'turno_planta_interna'
    ):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    if verificar_rol('jefe_primera_instancia', 'jefe_segunda_instancia'):
        conn_chk = cur_chk = None
        try:
            conn_chk = get_db_connection()
            cur_chk  = conn_chk.cursor()
            cur_chk.execute("""
                SELECT z.nombre FROM usuarios u
                LEFT JOIN zonas z ON u.zona_id = z.id
                WHERE u.usuario_id = %s
            """, (session['usuario_id'],))
            row_chk = cur_chk.fetchone()
            mi_zona = row_chk[0] if row_chk else None
        finally:
            if cur_chk:  cur_chk.close()
            if conn_chk: conn_chk.close()
        if not mi_zona or mi_zona != zona:
            return jsonify({'success': False, 'message': 'Solo puedes ver el detalle de tu propia zona.'}), 403
 
    elif verificar_rol('tecnico'):
        conn_chk = cur_chk = None
        try:
            conn_chk = get_db_connection()
            cur_chk  = conn_chk.cursor()
            cur_chk.execute("""
                SELECT z.nombre FROM tecnicos t
                LEFT JOIN zonas z ON t.zona_id = z.id
                WHERE t.usuario_id = %s AND t.activo = TRUE
            """, (session['usuario_id'],))
            row_chk = cur_chk.fetchone()
            mi_zona = row_chk[0] if row_chk else None
        finally:
            if cur_chk:  cur_chk.close()
            if conn_chk: conn_chk.close()
        if not mi_zona or mi_zona != zona:
            return jsonify({'success': False, 'message': 'Solo puedes ver el detalle de tu propia zona.'}), 403
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        if zona == 'Sin zona':
            filtro_zona, params = "u.zona_id IS NULL", []
        else:
            filtro_zona, params = "z.nombre = %s", [zona]
 
        cur.execute(f"""
            SELECT r.id, u.nombre, u.apellido, r.titulo, r.estado,
                   r.prioridad, r.fecha_creacion, r.servicio_afectado
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN zonas z ON u.zona_id = z.id
            WHERE {filtro_zona}
            ORDER BY r.fecha_creacion DESC
            LIMIT 50
        """, params)
        filas = cur.fetchall()
        return jsonify({
            'success': True,
            'zona': zona,
            'reclamos': [
                {
                    'id': f[0], 'cliente': f"{f[1]} {f[2]}", 'titulo': f[3],
                    'estado': f[4], 'prioridad': f[5],
                    'fecha_creacion': f[6].strftime('%d/%m/%Y %H:%M') if f[6] else '—',
                    'servicio': f[7] or '—',
                }
                for f in filas
            ]
        })
    except Exception as e:
        print(f"ERROR api_soporte_reclamos_por_zona: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/verificacion_previa/<int:reclamo_id>')
def api_verificacion_previa(reclamo_id):
    """
    Corresponde al paso 'Nodo verifica cortes, trámites pendientes' +
    '¿Existen cambios de estado?' del diagrama de proceso: antes de
    abrir el diagnóstico técnico completo, se revisa si:
      a) ya existe una falla masiva ACTIVA en la zona del cliente, o
      b) la cuenta del cliente está en mora.
    Si alguna es cierta, el frontend muestra un aviso en vez de
    forzar el checklist completo — igual que el diagrama termina el
    flujo en 'Informa al usuario del cambio de estado'.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("SELECT usuario_id FROM reclamos WHERE id = %s", (reclamo_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
        usuario_id = row[0]
 
        zona_id, zona_nombre = obtener_zona_reclamo(reclamo_id)
 
        falla_masiva = None
        if zona_id:
            cur.execute("""
                SELECT fm.id, fm.codigo, fm.nombre, fm.estado
                FROM fallas_masivas fm
                JOIN reclamos_fallas_masivas rfm ON rfm.falla_masiva_id = fm.id
                JOIN reclamos r2  ON r2.id = rfm.reclamo_id
                JOIN usuarios u2  ON r2.usuario_id = u2.usuario_id
                WHERE u2.zona_id = %s AND fm.estado IN ('activa', 'en_reparacion')
                ORDER BY fm.fecha_inicio DESC
                LIMIT 1
            """, (zona_id,))
            fm_row = cur.fetchone()
            if fm_row:
                falla_masiva = {'id': fm_row[0], 'codigo': fm_row[1], 'nombre': fm_row[2], 'estado': fm_row[3]}
 
        monto_adeudado, estado_cuenta = obtener_estado_cuenta_cliente(usuario_id)
 
        return jsonify({
            'success': True,
            'zona': zona_nombre,
            'falla_masiva': falla_masiva,
            'estado_cuenta': estado_cuenta,
            'monto_adeudado': float(monto_adeudado),
            'en_mora': estado_cuenta == 'mora',
        })
    except Exception as e:
        print(f"ERROR api_verificacion_previa: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/api/soporte/cerrar_por_estado_cuenta/<int:reclamo_id>', methods=['POST'])
def api_cerrar_por_estado_cuenta(reclamo_id):
    """
    Atajo del diagrama: cuando la falla real es la cuenta en mora (no
    la red), el flujo termina informando al cliente, sin pasar por
    diagnóstico técnico ni técnico de campo.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("SELECT id, estado FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
        if reclamo[1] not in ('abierto', 'en_diagnostico'):
            return jsonify({'success': False, 'message': f'El reclamo ya está en estado "{reclamo[1]}".'}), 400
 
        empleado_id = obtener_empleado_id_por_usuario(session['usuario_id'])
 
        cur.execute("""
            UPDATE reclamos SET estado = 'cerrado', fecha_resolucion = NOW()
            WHERE id = %s
        """, (reclamo_id,))
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, %s, 'cerrado',
                    'Cerrado sin diagnóstico técnico: cuenta en mora/suspendida. Se informó al cliente su estado de cuenta.')
        """, (reclamo_id, empleado_id))
 
        conn.commit()
        return jsonify({
            'success': True,
            'message': f'Reclamo #{reclamo_id} cerrado. Se informó al cliente sobre su estado de cuenta.'
        })
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_cerrar_por_estado_cuenta: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
# ============================================================
# DASHBOARD SOPORTE
# ============================================================

@app.route('/dashboard_soporte')
def dashboard_soporte():
    if 'usuario_id' not in session or session.get('rol') != 'help_desk':
        flash('No tienes permisos para acceder a esta área.', 'danger')
        return redirect(url_for('inicio_sesion'))

    reclamos_pendientes = tramites_pendientes = usuarios_activos = mis_reclamos = 0
    reclamos_recientes  = []
    mis_reclamos_lista  = []
    empleado_id         = None

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

       
        cur.execute("""
            SELECT id FROM empleados_soporte
            WHERE usuario_id = %s AND activo = TRUE
        """, (session['usuario_id'],))
        empleado_soporte = cur.fetchone()

        

        empleado_id = empleado_soporte[0] if empleado_soporte else None

     
        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE estado IN ('abierto','en_proceso')
              AND NOT (es_turno_nocturno = TRUE AND escalado_a IS NULL)
        """)
        reclamos_pendientes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE")
        usuarios_activos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM reclamos")
        total_fallas = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE estado IN ('en_proceso','en_diagnostico','pendiente_asignacion','falla_masiva')
              AND NOT (es_turno_nocturno = TRUE AND escalado_a IS NULL)
        """)
        fallas_en_proceso = cur.fetchone()[0]

        
        cur.execute("""
            SELECT COUNT(*) FROM diagnosticos_remotos d
            JOIN reclamos r ON r.id = d.reclamo_id
            WHERE d.operador_id = %s AND d.fecha_fin IS NULL
              AND r.estado = 'en_diagnostico'
        """, (session['usuario_id'],))
        mis_reclamos = cur.fetchone()[0]

       
        cur.execute("""
            SELECT
                r.id, u.nombre, u.apellido, r.tipo_reclamo, r.titulo,
                r.estado, r.fecha_creacion, r.prioridad,
                COALESCE(
                    ut.nombre || ' ' || ut.apellido,
                    es.nombre_completo,
                    '—'
                ) AS agente_asignado,
                r.servicio_afectado, r.fuera_de_horario, r.fecha_resolucion
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN empleados_soporte es ON r.asignado_a = es.id
            LEFT JOIN tecnicos t           ON r.asignado_a = t.id
            LEFT JOIN usuarios ut          ON t.usuario_id  = ut.usuario_id
            WHERE (
                r.estado IN (
                    'abierto', 'en_proceso', 'en_diagnostico',
                    'pendiente_asignacion', 'falla_masiva'
                )
                OR (
                    r.estado IN (
                        'resuelto', 'resuelto_tecnico', 'resuelto_remoto',
                        'liberado', 'cerrado', 'auditado'
                    )
                    AND (
                        r.fecha_resolucion IS NULL
                        OR r.fecha_resolucion >= NOW() - INTERVAL '24 hours'
                    )
                )
            )
            AND NOT (r.es_turno_nocturno = TRUE AND r.escalado_a IS NULL)
            ORDER BY
                CASE r.estado
                    WHEN 'abierto'              THEN 1
                    WHEN 'en_diagnostico'        THEN 2
                    WHEN 'pendiente_asignacion'  THEN 3
                    WHEN 'falla_masiva'          THEN 3
                    WHEN 'en_proceso'            THEN 4
                    ELSE 5
                END,
                CASE r.prioridad
                    WHEN 'critica' THEN 1
                    WHEN 'alta'    THEN 2
                    WHEN 'media'   THEN 3
                    WHEN 'baja'    THEN 4
                END,
                r.fecha_creacion DESC
            LIMIT 15
        """)
        reclamos_recientes = cur.fetchall()

       
        cur.execute("""
            SELECT
                r.id, u.nombre, u.apellido, r.tipo_reclamo, r.titulo,
                r.estado, r.fecha_creacion, r.prioridad,
                r.servicio_afectado, r.problema_especifico
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            JOIN diagnosticos_remotos d ON d.reclamo_id = r.id
            WHERE d.operador_id = %s AND d.fecha_fin IS NULL
              AND r.estado = 'en_diagnostico'
            ORDER BY
                CASE r.prioridad
                    WHEN 'critica' THEN 1
                    WHEN 'alta'    THEN 2
                    WHEN 'media'   THEN 3
                    WHEN 'baja'    THEN 4
                END,
                r.fecha_creacion ASC
            LIMIT 10
        """, (session['usuario_id'],))
        mis_reclamos_lista = cur.fetchall()

    except Exception as e:
        print(f"ERROR dashboard_soporte: {e}")
        reclamos_pendientes = usuarios_activos = mis_reclamos = 0
        reclamos_recientes  = []
        mis_reclamos_lista  = []
        empleado_id         = None
        total_fallas = fallas_en_proceso = 0
    finally:
        if cur:  cur.close()
        if conn: conn.close()

    return render_template('dashboard_soporte.html',
                           reclamos_pendientes=reclamos_pendientes,
                           usuarios_activos=usuarios_activos,
                           mis_reclamos=mis_reclamos,
                           reclamos_recientes=reclamos_recientes,
                           mis_reclamos_lista=mis_reclamos_lista,
                           empleado_id=empleado_id,
                           nombre_usuario=session.get('nombre', ''),
                           total_fallas=total_fallas,
                           fallas_en_proceso=fallas_en_proceso)



def obtener_empleado_soporte_por_usuario(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, nombre_completo, especialidad
            FROM empleados_soporte WHERE usuario_id=%s AND activo=TRUE
        """, (usuario_id,))
        return cur.fetchone()
    except Exception as e:
        print(f"ERROR obtener_empleado_soporte_por_usuario: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()



@app.route('/api/jefe_especialidad/miembros')
def api_je_miembros():
    """
    Lista, para el Jefe DRA/DRC, TODOS los miembros de su rama a
    los que puede asignar/rotar zona:
      - Técnicos de su tipo (RA para DRA, RC para DRC)
      - El Jefe de Instancia correspondiente (1ra para DRA, 2da
        para DRC) — porque ese jefe también necesita zona antes
        de poder ver reclamos en su propio dashboard.
    """
    if 'usuario_id' not in session or not verificar_rol('jefe_dra', 'jefe_drc'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    especialidad = (request.args.get('especialidad') or _especialidad_de_sesion()).upper()
    tipo_tecnico = 'RA' if especialidad == 'DRA' else 'RC'
    rol_jefe = 'jefe_primera_instancia' if especialidad == 'DRA' else 'jefe_segunda_instancia'
    etiqueta_jefe = 'Jefe 1ra Instancia' if especialidad == 'DRA' else 'Jefe 2da Instancia'

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        miembros = []

        cur.execute("""
            SELECT u.usuario_id, u.nombre || ' ' || u.apellido AS nombre_completo,
                   'Técnico ' || t.tipo_tecnico AS rol, t.zona_id
            FROM tecnicos t
            JOIN usuarios u ON u.usuario_id = t.usuario_id
            WHERE t.activo = TRUE AND t.tipo_tecnico = %s
            ORDER BY u.nombre
        """, (tipo_tecnico,))
        miembros += [
            {'usuario_id': m[0], 'nombre_completo': m[1], 'rol': m[2], 'zona_id': m[3], 'tipo_miembro': 'tecnico'}
            for m in cur.fetchall()
        ]

        cur.execute("""
            SELECT u.usuario_id, u.nombre || ' ' || u.apellido AS nombre_completo, u.zona_id
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE r.rol = %s AND u.activo = TRUE
            ORDER BY u.nombre
        """, (rol_jefe,))
        miembros += [
            {'usuario_id': m[0], 'nombre_completo': m[1], 'rol': etiqueta_jefe, 'zona_id': m[2], 'tipo_miembro': 'jefe_instancia'}
            for m in cur.fetchall()
        ]

        return jsonify({'success': True, 'miembros': miembros})
    except Exception as e:
        print(f"ERROR api_je_miembros: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/jefe_especialidad/asignar_zona_miembro/<int:usuario_id>', methods=['POST'])
def api_je_asignar_zona_miembro(usuario_id):
    """
    Asigna/rota zona a un miembro del equipo del Jefe DRA/DRC.
    Detecta si el usuario_id es un técnico de su tipo o el Jefe
    de Instancia de su rama, y actualiza la(s) tabla(s) correctas:
      - Técnico: tecnicos.zona_id Y usuarios.zona_id
      - Jefe de Instancia: solo usuarios.zona_id (no tiene fila
        en tecnicos)
    """
    if 'usuario_id' not in session or not verificar_rol('jefe_dra', 'jefe_drc'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    especialidad = _especialidad_de_sesion()
    tipo_tecnico = 'RA' if especialidad == 'DRA' else 'RC'
    rol_jefe = 'jefe_primera_instancia' if especialidad == 'DRA' else 'jefe_segunda_instancia'

    conn = cur = None
    try:
        data    = request.get_json()
        zona_id = data.get('zona_id')
        if not zona_id:
            return jsonify({'success': False, 'message': 'Selecciona una zona.'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id, nombre FROM zonas WHERE id = %s AND activo = TRUE", (zona_id,))
        zona = cur.fetchone()
        if not zona:
            return jsonify({'success': False, 'message': 'Zona no válida.'}), 400

        # ¿Es un técnico de esta especialidad?
        cur.execute("""
            SELECT t.zona_id FROM tecnicos t
            WHERE t.usuario_id = %s AND t.tipo_tecnico = %s AND t.activo = TRUE
        """, (usuario_id, tipo_tecnico))
        tec = cur.fetchone()

        if tec:
            zona_anterior_id = tec[0]
            cur.execute("UPDATE tecnicos SET zona_id = %s WHERE usuario_id = %s", (zona_id, usuario_id))
            cur.execute("UPDATE usuarios SET zona_id = %s WHERE usuario_id = %s", (zona_id, usuario_id))
            tipo_accion = 'rotacion_jefe_especialidad'
        else:
            # ¿Es el Jefe de Instancia de esta rama?
            cur.execute("""
                SELECT u.zona_id FROM usuarios u
                JOIN roles r ON u.id_rol = r.id_rol
                WHERE u.usuario_id = %s AND r.rol = %s AND u.activo = TRUE
            """, (usuario_id, rol_jefe))
            jefe = cur.fetchone()
            if not jefe:
                return jsonify({'success': False, 'message': 'Este usuario no pertenece a tu equipo.'}), 403

            zona_anterior_id = jefe[0]
            cur.execute("UPDATE usuarios SET zona_id = %s WHERE usuario_id = %s", (zona_id, usuario_id))
            tipo_accion = 'rotacion_jefe_especialidad_jefe_instancia'

        cur.execute("""
            INSERT INTO historial_zona (usuario_id, zona_anterior_id, zona_nueva_id, modificado_por, tipo_accion)
            VALUES (%s, %s, %s, %s, %s)
        """, (usuario_id, zona_anterior_id, zona_id, session['usuario_id'], tipo_accion))

        conn.commit()
        return jsonify({'success': True, 'zona_nombre': zona[1],
                         'message': f'Zona "{zona[1]}" asignada correctamente.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_je_asignar_zona_miembro: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()



# ── Constante que faltaba (usada por las consultas de abajo) ──
SQL_FECHA_INICIO_ETAPA = """
    COALESCE(
        (SELECT MAX(rs.fecha_accion) FROM reclamos_seguimiento rs WHERE rs.reclamo_id = r.id),
        r.fecha_creacion
    )
"""
 
# ── Helpers que faltaban (los usa api_je_miembros que ya tienes) ──
def _instancia_por_especialidad(especialidad):
    return 1 if especialidad == 'DRA' else 2
 
def _especialidad_de_sesion():
    rol = session.get('rol')
    return 'DRA' if rol == 'jefe_dra' else 'DRC'
 
 
# ============================================================
# DASHBOARD JEFE HELP DESK
# ============================================================
 
@app.route('/dashboard_jefe_helpdesk')
def dashboard_jefe_helpdesk():
    if 'usuario_id' not in session or not verificar_rol('jefe_help_desk'):
        flash('Acceso solo para Jefe de Help Desk.', 'danger')
        return redirect(url_for('inicio_sesion'))
    return render_template('dashboard_jefe_helpdesk.html', nombre_usuario=session.get('nombre', ''))
 
 
@app.route('/api/jefe_helpdesk/reclamos_pendientes')
def api_jh_reclamos_pendientes():
    if 'usuario_id' not in session or not verificar_rol('jefe_help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(f"""
            SELECT r.id, u.nombre || ' ' || u.apellido AS cliente,
                   r.servicio_afectado, r.prioridad, r.estado,
                   {SQL_FECHA_INICIO_ETAPA} AS fecha_inicio_etapa
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            WHERE r.estado = 'pendiente_triage'
            ORDER BY
                CASE r.prioridad WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END,
                r.fecha_creacion ASC
        """)
        filas = cur.fetchall()
 
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE accion = 'enviado_a_especialidad' AND fecha_accion::date = CURRENT_DATE),
                COUNT(*) FILTER (WHERE accion = 'asignado_directo' AND fecha_accion::date = CURRENT_DATE)
            FROM reclamos_seguimiento
        """)
        hoy = cur.fetchone()
 
        return jsonify({
            'success': True,
            'reclamos': [
                {
                    'id': f[0], 'cliente': f[1], 'servicio': f[2],
                    'prioridad': f[3], 'estado': f[4],
                    'fecha_inicio_etapa': f[5].isoformat() if f[5] else None,
                }
                for f in filas
            ],
            'enviados_instancia_hoy': hoy[0] or 0,
            'asignados_directo_hoy': hoy[1] or 0,
        })
    except Exception as e:
        print(f"ERROR api_jh_reclamos_pendientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/api/jefe_helpdesk/enviar_instancia/<int:reclamo_id>', methods=['POST'])
def api_jh_enviar_instancia(reclamo_id):
    if 'usuario_id' not in session or not verificar_rol('jefe_help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        data = request.get_json() or {}
        instancia = int(data.get('instancia') or 0)
        nota = (data.get('nota') or '').strip()
        if instancia not in (1, 2):
            return jsonify({'success': False, 'message': 'Instancia inválida'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id, estado FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
        if reclamo[1] != 'pendiente_triage':
            return jsonify({'success': False, 'message': f'El reclamo ya está en estado "{reclamo[1]}".'}), 400
 
        cur.execute("""
            UPDATE reclamos SET estado = 'pendiente_revision_especialidad', instancia = %s
            WHERE id = %s
        """, (instancia, reclamo_id))
 
        desc = f"Jefe Help Desk ({session.get('nombre','')}) envió a revisión de {'Jefe DRA' if instancia==1 else 'Jefe DRC'}."
        if nota:
            desc += f" Nota: {nota}"
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'enviado_a_especialidad', %s)
        """, (reclamo_id, desc))
 
        conn.commit()
        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} enviado a revisión de especialidad.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_jh_enviar_instancia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/api/jefe_helpdesk/tecnicos_disponibles')
def api_jh_tecnicos_disponibles():
    if 'usuario_id' not in session or not verificar_rol('jefe_help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT t.id, u.nombre || ' ' || u.apellido AS nombre_completo,
                   t.tipo_tecnico, COUNT(r2.id) AS reclamos_activos
            FROM tecnicos t
            JOIN usuarios u ON u.usuario_id = t.usuario_id
            LEFT JOIN reclamos r2 ON r2.asignado_a = t.id AND r2.estado = 'en_proceso'
            WHERE t.activo = TRUE
            GROUP BY t.id, u.nombre, u.apellido, t.tipo_tecnico
            ORDER BY reclamos_activos ASC, u.nombre ASC
        """)
        tecnicos = [
            {'id': t[0], 'nombre_completo': t[1], 'tipo_tecnico': t[2], 'reclamos_activos': t[3]}
            for t in cur.fetchall()
        ]
        return jsonify({'success': True, 'tecnicos': tecnicos})
    except Exception as e:
        print(f"ERROR api_jh_tecnicos_disponibles: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/api/jefe_helpdesk/asignar_tecnico_directo/<int:reclamo_id>', methods=['POST'])
def api_jh_asignar_directo(reclamo_id):
    if 'usuario_id' not in session or not verificar_rol('jefe_help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        data       = request.get_json() or {}
        tecnico_id = data.get('tecnico_id')
        nota       = (data.get('nota') or '').strip()
        if not tecnico_id:
            return jsonify({'success': False, 'message': 'Técnico requerido'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT r.id, r.titulo, r.descripcion, r.tipo_reclamo, r.prioridad,
                   r.servicio_afectado, r.usuario_id
            FROM reclamos r WHERE r.id = %s
        """, (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
 
        cur.execute("""
            UPDATE reclamos SET asignado_a = %s, estado = 'en_proceso', fecha_asignacion = NOW()
            WHERE id = %s
        """, (tecnico_id, reclamo_id))
 
        cur.execute("SELECT NEXTVAL('seq_numero_ot')")
        seq = cur.fetchone()[0]
        numero_ot = f"OT-{seq:04d}"
 
        cur.execute("""
            INSERT INTO ordenes_trabajo (
                numero_ot, titulo, descripcion, tipo_trabajo, prioridad, estado,
                tecnico_id, usuario_cliente_id, observaciones, creado_por, reclamo_id,
                fecha_creacion, fecha_actualizacion
            ) VALUES (%s,%s,%s,%s,%s,'pendiente',%s,%s,%s,%s,%s, NOW(), NOW())
            RETURNING id
        """, (
            numero_ot, f"[Directo Jefe Help Desk] {reclamo[1]}", reclamo[2] or 'Sin descripción',
            reclamo[3], reclamo[4], tecnico_id, reclamo[6], nota or None,
            session['usuario_id'], reclamo_id
        ))
        ot_id = cur.fetchone()[0]
 
        cur.execute("""
            INSERT INTO ot_actividades (ot_id, tecnico_id, descripcion, tipo)
            VALUES (%s, %s, %s, 'nota')
        """, (ot_id, tecnico_id,
              f"OT asignada directamente por Jefe Help Desk ({session.get('nombre','')}), sin pasar por instancia."
              + (f" Nota: {nota}" if nota else "")))
 
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'asignado_directo', %s)
        """, (reclamo_id, f"Jefe Help Desk ({session.get('nombre','')}) asignó técnico directo, saltando instancia."))
 
        conn.commit()
        return jsonify({'success': True, 'numero_ot': numero_ot,
                         'message': f'Reclamo #{reclamo_id} asignado directamente ({numero_ot}).'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_jh_asignar_directo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
# ============================================================
# DASHBOARD JEFE DRA / JEFE DRC (un mismo template))
# ============================================================
 
@app.route('/dashboard_jefe_especialidad')
def dashboard_jefe_especialidad():
    if 'usuario_id' not in session or not verificar_rol('jefe_dra', 'jefe_drc'):
        flash('Acceso solo para Jefe DRA / Jefe DRC.', 'danger')
        return redirect(url_for('inicio_sesion'))
    especialidad = _especialidad_de_sesion()
    etiqueta = 'Jefe DRA' if especialidad == 'DRA' else 'Jefe DRC'
    return render_template(
        'dashboard_jefe_especialidad.html',
        especialidad=especialidad, etiqueta=etiqueta,
        nombre_usuario=session.get('nombre', ''),
    )
 
 
@app.route('/api/jefe_especialidad/reclamos_pendientes')
def api_je_reclamos_pendientes():
    if 'usuario_id' not in session or not verificar_rol('jefe_dra', 'jefe_drc'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    especialidad = (request.args.get('especialidad') or _especialidad_de_sesion()).upper()
    instancia = _instancia_por_especialidad(especialidad)
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(f"""
            SELECT r.id, u.nombre || ' ' || u.apellido AS cliente,
                   r.servicio_afectado, r.prioridad,
                   COALESCE(z.nombre, '— sin zona —') AS zona_cliente,
                   {SQL_FECHA_INICIO_ETAPA} AS fecha_inicio_etapa
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN zonas z ON u.zona_id = z.id
            WHERE r.estado = 'pendiente_revision_especialidad' AND r.instancia = %s
            ORDER BY
                CASE r.prioridad WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END,
                r.fecha_creacion ASC
        """, (instancia,))
        filas = cur.fetchall()
 
        cur.execute("""
            SELECT COUNT(*) FROM reclamos_seguimiento
            WHERE accion = 'aprobado_especialidad' AND fecha_accion::date = CURRENT_DATE
        """)
        enviados_hoy = cur.fetchone()[0]
 
        return jsonify({
            'success': True,
            'reclamos': [
                {
                    'id': f[0], 'cliente': f[1], 'servicio': f[2], 'prioridad': f[3],
                    'zona_cliente': f[4],
                    'fecha_inicio_etapa': f[5].isoformat() if f[5] else None,
                }
                for f in filas
            ],
            'enviados_hoy': enviados_hoy or 0,
        })
    except Exception as e:
        print(f"ERROR api_je_reclamos_pendientes: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/api/jefe_especialidad/aprobar_enviar_instancia/<int:reclamo_id>', methods=['POST'])
def api_je_aprobar_enviar_instancia(reclamo_id):
    if 'usuario_id' not in session or not verificar_rol('jefe_dra', 'jefe_drc'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id, estado, instancia FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
        if reclamo[1] != 'pendiente_revision_especialidad':
            return jsonify({'success': False, 'message': f'El reclamo ya está en estado "{reclamo[1]}".'}), 400
 
        cur.execute("UPDATE reclamos SET estado = 'pendiente_asignacion' WHERE id = %s", (reclamo_id,))
 
        etiqueta = 'Jefe DRA' if session.get('rol') == 'jefe_dra' else 'Jefe DRC'
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'aprobado_especialidad', %s)
        """, (reclamo_id, f"{etiqueta} ({session.get('nombre','')}) aprobó el caso y lo envió al Jefe de Instancia."))
 
        conn.commit()
 
        notificar_jefes_instancia(
            reclamo[2], reclamo_id,
            f'{etiqueta} aprobó y envió el reclamo #{reclamo_id} para asignación de técnico.'
        )
 
        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} enviado al Jefe de Instancia.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_je_aprobar_enviar_instancia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 

 
@app.route('/api/zonas')
def api_zonas():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    filas = obtener_zonas()
    return jsonify({'success': True, 'zonas': [{'id': f[0], 'nombre': f[1]} for f in filas]})
 


#___________________________
from datetime import datetime
import json
import os
import uuid
from werkzeug.utils import secure_filename
 

# ============================================================
# RECLAMOS (cliente)
# ============================================================

def obtener_servicios_disponibles():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, nombre_servicio, categoria
            FROM servicios_disponibles WHERE activo=TRUE
            ORDER BY categoria, nombre_servicio
        """)
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_servicios_disponibles: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()

@app.route('/perfil')
@app.route('/perfil')
def perfil():
    if 'usuario_id' not in session or not verificar_rol(
        'help_desk', 'jefe_primera_instancia', 'jefe_segunda_instancia', 'tecnico',
        'jefe_help_desk', 'jefe_dra', 'jefe_drc'
    ):
        flash('Esta sección es solo para personal de COTEL RL.', 'danger')
        return redirect(url_for('inicio_sesion'))
 
    rol = session.get('rol')
    perfil_datos = obtener_perfil_completo(session['usuario_id'], rol)
    if not perfil_datos:
        flash('No se encontró tu perfil.', 'danger')
        return redirect(url_for('inicio_sesion'))
 
    etiqueta_rol = {
        'help_desk': 'Help Desk',
        'jefe_primera_instancia': 'Jefe de 1ra Instancia',
        'jefe_segunda_instancia': 'Jefe de 2da Instancia',
        'tecnico': 'Técnico',
        'jefe_help_desk': 'Jefe Help Desk',
        'jefe_dra': 'Jefe DRA',
        'jefe_drc': 'Jefe DRC',
    }.get(rol, rol)
 
    return render_template(
        'perfil.html',
        perfil=perfil_datos,
        rol=rol,
        etiqueta_rol=etiqueta_rol,
        nombre_usuario=session.get('nombre', ''),
    )


@app.route('/perfil_cliente')
def perfil_cliente():
    if 'usuario_id' not in session or session.get('rol', '').lower() != 'cliente':
        flash('Esta sección es solo para clientes.', 'danger')
        return redirect(url_for('inicio_sesion'))

    perfil_datos = obtener_perfil_completo(session['usuario_id'], 'cliente')
    if not perfil_datos:
        flash('No se encontró tu perfil.', 'danger')
        return redirect(url_for('inicio_sesion'))

    return render_template(
        'perfil_cliente.html',
        perfil=perfil_datos,
        nombre_usuario=session.get('nombre', ''),
    )

def obtener_problemas_por_servicio(servicio_nombre):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT tp.id, tp.nombre_problema, tp.descripcion_problema, tp.categoria,
                   tp.solucion_sugerida
            FROM tipos_problemas tp
            JOIN servicios_disponibles sd ON tp.servicio_id = sd.id
            WHERE sd.nombre_servicio=%s AND tp.activo=TRUE
            ORDER BY tp.categoria, tp.nombre_problema
        """, (servicio_nombre,))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_problemas_por_servicio: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/reclamos')
def reclamos():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('inicio_sesion'))
 
    reclamos_lista    = obtener_reclamos_usuario(session['usuario_id'])
    contratos_cliente = obtener_contratos_usuario(session['usuario_id'])
    monto_adeudado, estado_cuenta = obtener_estado_cuenta_cliente(session['usuario_id'])
 
    ESTADOS_PROGRESO = ('en_diagnostico', 'pendiente_asignacion', 'falla_masiva', 'en_proceso')
    ESTADOS_RESUELTO = ('resuelto', 'resuelto_remoto', 'resuelto_tecnico', 'liberado', 'cerrado', 'auditado')
 
    stats_reclamos = {'abiertos': 0, 'en_progreso': 0, 'resueltos': 0}
    for r in reclamos_lista:
        estado = r[4]
        if estado == 'abierto':
            stats_reclamos['abiertos'] += 1
        elif estado in ESTADOS_PROGRESO:
            stats_reclamos['en_progreso'] += 1
        elif estado in ESTADOS_RESUELTO:
            stats_reclamos['resueltos'] += 1
 
    return render_template(
        'reclamos.html',
        reclamos=reclamos_lista,
        contratos=contratos_cliente,
        stats_reclamos=stats_reclamos,
        estado_cuenta=estado_cuenta,
        monto_adeudado=monto_adeudado,
    )

 
@app.route('/api/problemas_servicio/<servicio>')
def obtener_problemas_api(servicio):
    return jsonify(obtener_problemas_por_servicio(servicio))


@app.route('/crear_reclamo', methods=['POST'])
def crear_reclamo():
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión.', 'warning')
        return redirect(url_for('inicio_sesion'))
    conn = cur = None
    try:
        contrato_id          = request.form.get('contrato_id')
        tipo_reclamo         = request.form.get('tipo_reclamo')
        problema_especifico  = request.form.get('problema_especifico')
        descripcion          = (request.form.get('descripcion') or '').strip()
        telefono_referencia  = (request.form.get('telefono_referencia') or '').strip()
        ubicacion_lat        = request.form.get('ubicacion_lat') or None
        ubicacion_lng        = request.form.get('ubicacion_lng') or None
 
        if not all([contrato_id, tipo_reclamo, problema_especifico, telefono_referencia]):
            flash('Selecciona tu contrato, el tipo de falla, e indica un teléfono de referencia.', 'danger')
            return redirect(url_for('reclamos'))
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT id, tipo_servicio, numero_contrato, direccion, zona_id
            FROM contratos WHERE id = %s AND usuario_id = %s AND activo = TRUE
        """, (contrato_id, session['usuario_id']))
        contrato = cur.fetchone()
        if not contrato:
            flash('El contrato seleccionado no es válido o no pertenece a tu cuenta.', 'danger')
            return redirect(url_for('reclamos'))
 
        servicio_afectado  = contrato[1]
        numero_cliente     = contrato[2]
        ubicacion_cliente  = contrato[3]
 
        # ── UN RECLAMO ACTIVO POR CONTRATO ──────────────────
        ESTADOS_CERRADOS_RECLAMO = (
            'resuelto', 'resuelto_remoto', 'resuelto_tecnico',
            'liberado', 'cerrado', 'auditado'
        )
        cur.execute("""
            SELECT id FROM reclamos
            WHERE numero_cliente = %s AND estado NOT IN %s
            LIMIT 1
        """, (numero_cliente, ESTADOS_CERRADOS_RECLAMO))
        if cur.fetchone():
            flash(f'Ya tienes un reclamo activo sobre el contrato {numero_cliente}. '
                  f'Espera a que se resuelva antes de crear uno nuevo.', 'warning')
            return redirect(url_for('reclamos'))
 
        if contrato[4]:
            cur.execute("""
                UPDATE usuarios SET zona_id = COALESCE(zona_id, %s)
                WHERE usuario_id = %s
            """, (contrato[4], session['usuario_id']))
 
        monto_adeudado, estado_cuenta = obtener_estado_cuenta_cliente(session['usuario_id'])
 
        # ── BLOQUEO POR MORA ─────────────────────────────────
        if estado_cuenta == 'mora':
            flash(
                f'No puedes registrar un reclamo mientras tengas facturas vencidas '
                f'(Bs. {float(monto_adeudado):.2f} pendientes). Regulariza tu pago en la '
                f'sección de Pagos y vuelve a intentarlo.',
                'danger'
            )
            return redirect(url_for('pagos'))
 
        titulo = f"{tipo_reclamo.capitalize()} — {problema_especifico}"[:150]

        prioridad = 'media'
        if problema_especifico and any(p in problema_especifico for p in ['Sin Conexión', 'Sin Señal', 'No conecta']):
            prioridad = 'alta'

        nocturno = es_turno_nocturno()
        if nocturno:
            prioridad = 'alta'  # el Jefe puede reclasificarla luego si corresponde

        cur.execute("""
            INSERT INTO reclamos
                (usuario_id, tipo_reclamo, titulo, descripcion,
                 servicio_afectado, problema_especifico, ubicacion_cliente,
                 numero_cliente, estado_cuenta, monto_adeudado,
                 estado, prioridad, fecha_creacion, instancia,
                 telefono_referencia, ubicacion_lat, ubicacion_lng, fuera_de_horario,
                 es_turno_nocturno)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'abierto',%s,%s,1,%s,%s,%s,
                    (EXTRACT(HOUR FROM NOW() AT TIME ZONE 'America/La_Paz') < 8
                     OR EXTRACT(HOUR FROM NOW() AT TIME ZONE 'America/La_Paz') >= 20),
                    %s)
            RETURNING id, fuera_de_horario
        """, (session['usuario_id'], tipo_reclamo, titulo, descripcion,
              servicio_afectado, problema_especifico, ubicacion_cliente,
              numero_cliente, estado_cuenta, monto_adeudado,
              prioridad, datetime.now(),
              telefono_referencia, ubicacion_lat, ubicacion_lng, nocturno))
        reclamo_id, fue_fuera_horario = cur.fetchone()
 
        registrar_seguimiento_reclamo(reclamo_id, None, 'creado', 'Reclamo creado por el cliente via web')
        conn.commit()
 
        asignado = asignar_reclamo_automaticamente(reclamo_id, tipo_reclamo, problema_especifico)
        msg = f'Reclamo N° #{reclamo_id} creado exitosamente sobre tu contrato {numero_cliente}. El equipo de soporte lo revisará.' \
              if asignado else \
              f'Reclamo N° #{reclamo_id} creado sobre tu contrato {numero_cliente}. Será asignado pronto.'
        if fue_fuera_horario:
            msg += ' Nota: lo registraste fuera de nuestro horario de atención (8:00-20:00), pero el tiempo de atención se contabiliza igual desde este momento.'
        flash(msg, 'success')
 
        return redirect(url_for('reclamos'))
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR crear_reclamo: {e}")
        flash('Error al crear reclamo.', 'danger')
        return redirect(url_for('reclamos'))
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
##__________________________________________________
# funciones para cambiar el perfil y actualizar el password
@app.route('/api/perfil/actualizar_datos', methods=['POST'])
def api_perfil_actualizar_datos():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        data     = request.get_json()
        nombre   = (data.get('nombre') or '').strip()
        apellido = (data.get('apellido') or '').strip()
        telefono = (data.get('telefono') or '').strip()

        if not nombre or not apellido:
            return jsonify({'success': False, 'message': 'Nombre y apellido son obligatorios.'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE usuarios SET nombre = %s, apellido = %s, telefono = %s
            WHERE usuario_id = %s
        """, (nombre, apellido, telefono, session['usuario_id']))
        conn.commit()
        session['nombre'] = nombre
        return jsonify({'success': True, 'message': 'Datos actualizados correctamente.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_perfil_actualizar_datos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/perfil/cambiar_password', methods=['POST'])
def api_perfil_cambiar_password():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        data         = request.get_json()
        actual       = data.get('actual') or ''
        nueva        = data.get('nueva') or ''
        confirmacion = data.get('confirmacion') or ''

        if nueva != confirmacion:
            return jsonify({'success': False, 'message': 'Las contraseñas nuevas no coinciden.'}), 400
        if not validar_contraseña(nueva):
            return jsonify({
                'success': False,
                'message': 'La nueva contraseña debe tener 8+ caracteres, mayúscula, minúscula, número y símbolo.'
            }), 400

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT contraseña FROM usuarios WHERE usuario_id = %s", (session['usuario_id'],))
        row = cur.fetchone()
        if not row or not check_password_hash(row[0], actual):
            return jsonify({'success': False, 'message': 'La contraseña actual es incorrecta.'}), 400

        cur.execute("UPDATE usuarios SET contraseña = %s WHERE usuario_id = %s",
                    (generate_password_hash(nueva), session['usuario_id']))
        conn.commit()
        return jsonify({'success': True, 'message': 'Contraseña actualizada correctamente.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_perfil_cambiar_password: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def obtener_facturas_usuario(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, numero_factura, fecha_emision, fecha_vencimiento,
                   total, estado, fecha_pago, metodo_pago
            FROM facturas
            WHERE usuario_id = %s
            ORDER BY fecha_vencimiento DESC
        """, (usuario_id,))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_facturas_usuario: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()

##SIMULACION DE PAGOS 
#
@app.route('/pagos')
def pagos():
    if 'usuario_id' not in session or session.get('rol', '').lower() != 'cliente':
        flash('Debes iniciar sesión como cliente.', 'warning')
        return redirect(url_for('inicio_sesion'))

    facturas = obtener_facturas_usuario(session['usuario_id'])
    total_adeudado, _ = obtener_estado_cuenta_cliente(session['usuario_id'])
    facturas_pagadas = sum(1 for f in facturas if f[5] == 'pagado')

    return render_template(
        'pagos.html',
        facturas=facturas,
        total_adeudado=total_adeudado,
        facturas_pagadas=facturas_pagadas,
        nombre_usuario=session.get('nombre', ''),
    )

@app.route('/api/pagos/simular_pago/<int:factura_id>', methods=['POST'])
def api_simular_pago(factura_id):
    if 'usuario_id' not in session or session.get('rol', '').lower() != 'cliente':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("""
            SELECT id, estado, total FROM facturas
            WHERE id = %s AND usuario_id = %s
        """, (factura_id, session['usuario_id']))
        factura = cur.fetchone()
        if not factura:
            return jsonify({'success': False, 'message': 'Factura no encontrada.'}), 404
        if factura[1] == 'pagado':
            return jsonify({'success': False, 'message': 'Esta factura ya está pagada.'}), 400

        cur.execute("""
            UPDATE facturas
            SET estado = 'pagado', fecha_pago = NOW(), metodo_pago = 'Simulado (prueba web)'
            WHERE id = %s
        """, (factura_id,))

        referencia = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        cur.execute("""
            INSERT INTO pagos (usuario_id, factura_id, monto, metodo_pago, estado, referencia)
            VALUES (%s, %s, %s, 'Simulado (prueba web)', 'completado', %s)
        """, (session['usuario_id'], factura_id, factura[2], referencia))

        conn.commit()

        return jsonify({
            'success': True,
            'referencia': referencia,
            'message': f'Pago simulado registrado (Ref. {referencia}). Factura marcada como pagada por Bs. {float(factura[2]):.2f}.'
        })
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_simular_pago: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
#____________________________________________________

@app.route('/api/perfil/subir_foto', methods=['POST'])
def api_perfil_subir_foto():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    if 'foto' not in request.files:
        return jsonify({'success': False, 'message': 'No se recibió ningún archivo.'}), 400

    archivo = request.files['foto']

    if archivo.filename == '':
        return jsonify({'success': False, 'message': 'No seleccionaste ningún archivo.'}), 400

    if not allowed_foto(archivo.filename):
        return jsonify({'success': False, 'message': 'Formato no permitido. Usa PNG, JPG o WEBP.'}), 400

    # Validar tamaño sin cargar todo el archivo en memoria innecesariamente
    archivo.seek(0, os.SEEK_END)
    tamaño_mb = archivo.tell() / (1024 * 1024)
    archivo.seek(0)
    if tamaño_mb > MAX_FOTO_SIZE_MB:
        return jsonify({
            'success': False,
            'message': f'La imagen supera el límite de {MAX_FOTO_SIZE_MB}MB.'
        }), 400

    conn = cur = None
    try:
        # 1) Nombre de archivo seguro y único 
        ext = secure_filename(archivo.filename).rsplit('.', 1)[1].lower()
        nombre_archivo = f"perfil_{session['usuario_id']}_{uuid.uuid4().hex[:10]}.{ext}"
        ruta_completa = os.path.join(UPLOAD_FOLDER_PERFILES, nombre_archivo)
        ruta_relativa = f"uploads/perfiles/{nombre_archivo}"

        conn = get_db_connection()
        cur  = conn.cursor()

        # 2) Busca si ya tenía una foto anterior, para borrarla luego
        cur.execute("SELECT foto_perfil FROM usuarios WHERE usuario_id = %s", (session['usuario_id'],))
        row = cur.fetchone()
        foto_anterior = row[0] if row else None

        # 3) Guarda el archivo físico en la carpeta
        archivo.save(ruta_completa)

        # 4) Guarda la referencia en la base de datos
        cur.execute(
            "UPDATE usuarios SET foto_perfil = %s WHERE usuario_id = %s",
            (ruta_relativa, session['usuario_id'])
        )
        conn.commit()

        # 5) Limpieza: borra el archivo físico de la foto anterior
        if foto_anterior:
            ruta_anterior_completa = os.path.join('static', foto_anterior)
            if os.path.exists(ruta_anterior_completa):
                try:
                    os.remove(ruta_anterior_completa)
                except OSError as e:
                    print(f"WARN: no se pudo borrar la foto anterior {ruta_anterior_completa}: {e}")

        return jsonify({
            'success': True,
            'foto_url': url_for('static', filename=ruta_relativa),
            'message': 'Foto de perfil actualizada correctamente.'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_perfil_subir_foto: {e}")
        return jsonify({'success': False, 'message': 'No se pudo guardar la foto. Intenta de nuevo.'}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/perfil/actualizar_zona', methods=['POST'])
def api_perfil_actualizar_zona():
    
    return jsonify({
        'success': False,
        'message': 'La zona/sucursal solo puede ser asignada por el administrador.'
    }), 403

# ============================================================
# FUNCIONES DE SOPORTE — ASIGNACIÓN AUTOMÁTICA
# ============================================================

def determinar_categoria_problema(problema_especifico, tipo_reclamo):
    p = (problema_especifico or '').lower()
    t = (tipo_reclamo or '').lower()
    if any(w in p for w in ['conexión', 'internet', 'wifi', 'señal', 'router', 'modem']):
        return 'tecnico'
    if any(w in t for w in ['facturación', 'pago', 'cobro', 'suspensión']):
        return 'facturacion'
    if any(w in t for w in ['cambio_plan', 'upgrade', 'nuevo_servicio']):
        return 'comercial'
    return 'general'


def obtener_empleado_para_asignacion(categoria_problema):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc WHERE proname='obtener_proximo_empleado_soporte'
            )
        """)
        if cur.fetchone()[0]:
            cur.execute("SELECT obtener_proximo_empleado_soporte(%s)", (categoria_problema,))
            res = cur.fetchone()
            empleado_id = res[0] if res else None
        else:
            cur.execute("""
                SELECT id FROM empleados_soporte
                WHERE activo=TRUE AND (especialidad=%s OR %s='general' OR especialidad='general')
                ORDER BY carga_trabajo ASC, fecha_creacion ASC LIMIT 1
            """, (categoria_problema, categoria_problema))
            res = cur.fetchone()
            empleado_id = res[0] if res else None

        if empleado_id:
            cur.execute("UPDATE empleados_soporte SET carga_trabajo=carga_trabajo+1 WHERE id=%s", (empleado_id,))
            conn.commit()
        return empleado_id
    except Exception as e:
        print(f"ERROR obtener_empleado_para_asignacion: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def crear_notificacion_soporte(empleado_id, reclamo_id, tipo_notificacion, mensaje):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO notificaciones_soporte (empleado_id, reclamo_id, tipo_notificacion, mensaje)
            VALUES (%s,%s,%s,%s)
        """, (empleado_id, reclamo_id, tipo_notificacion, mensaje))
        conn.commit()
        return True
    except Exception as e:
        print(f"ERROR crear_notificacion_soporte: {e}")
        return False
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def obtener_empleado_soporte_id(usuario_id):
    """
    Si el usuario todavía no tiene fila en empleados_soporte.
    """
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM empleados_soporte WHERE usuario_id = %s", (usuario_id,))
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute("SELECT nombre, apellido FROM usuarios WHERE usuario_id = %s", (usuario_id,))
        u = cur.fetchone()
        nombre_completo = f"{u[0]} {u[1]}".strip() if u else f"Usuario {usuario_id}"

        cur.execute("""
            INSERT INTO empleados_soporte (usuario_id, nombre_completo, especialidad)
            VALUES (%s, %s, 'general')
            RETURNING id
        """, (usuario_id, nombre_completo))
        nuevo_id = cur.fetchone()[0]
        conn.commit()
        return nuevo_id
    except Exception as e:
        print(f"ERROR obtener_empleado_soporte_id: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def registrar_seguimiento_reclamo(reclamo_id, empleado_id, accion, descripcion):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s,%s,%s,%s)
        """, (reclamo_id, empleado_id, accion, descripcion))
        conn.commit()
        return True
    except Exception as e:
        print(f"ERROR registrar_seguimiento_reclamo: {e}")
        return False
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def obtener_fecha_inicio_etapa(reclamo_id):
    """
    Fecha en que el reclamo entró a su etapa/estado ACTUAL: toma el
    último registro de reclamos_seguimiento Si no hay seguimiento, cae a fecha_creacion.
    """
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT fecha_accion FROM reclamos_seguimiento
            WHERE reclamo_id = %s
            ORDER BY fecha_accion DESC
            LIMIT 1
        """, (reclamo_id,))
        row = cur.fetchone()
        if row and row[0]:
            return row[0]
        cur.execute("SELECT fecha_creacion FROM reclamos WHERE id = %s", (reclamo_id,))
        row2 = cur.fetchone()
        return row2[0] if row2 else None
    except Exception as e:
        print(f"ERROR obtener_fecha_inicio_etapa: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()

def asignar_reclamo_automaticamente(reclamo_id, tipo_reclamo, problema_especifico):
    """
    Solo notifica a todos los agentes de soporte disponibles.
    """
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()


        cur.execute("""
            UPDATE reclamos
            SET estado = 'abierto', asignado_a = NULL
            WHERE id = %s
        """, (reclamo_id,))

        
        cur.execute("""
            SELECT id FROM empleados_soporte WHERE activo = TRUE
        """)
        agentes = cur.fetchall()
        for (agente_id,) in agentes:
            crear_notificacion_soporte(
                agente_id, reclamo_id, 'nuevo_reclamo',
                f'Nuevo reclamo sin asignar: {tipo_reclamo} - ID #{reclamo_id}. Requiere técnico.'
            )

        registrar_seguimiento_reclamo(
            reclamo_id, None, 'creado',
            'Reclamo creado, pendiente de asignación de técnico por soporte.'
        )
        conn.commit()
        return False  

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR asignar_reclamo_automaticamente: {e}")
        return False
    finally:
        if cur:  cur.close()
        if conn: conn.close()


# ============================================================
# RECLAMO TELEFÓNICO (101 / 800161040)
# ============================================================

def buscar_clientes(query):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        like = f"%{query}%"
        cur.execute("""
            SELECT DISTINCT u.usuario_id, u.nombre, u.apellido, u.correo,
                   u.telefono, COALESCE(cc.codigo, '—') AS codigo_cliente
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            LEFT JOIN codigos_registro_cliente cc ON cc.usuario_id = u.usuario_id
            LEFT JOIN contratos ct ON ct.usuario_id = u.usuario_id AND ct.activo = TRUE
            WHERE LOWER(r.rol) = 'cliente'
              AND u.activo = TRUE
              AND (
                    u.nombre           ILIKE %s OR
                    u.apellido         ILIKE %s OR
                    u.correo           ILIKE %s OR
                    u.telefono         ILIKE %s OR
                    cc.codigo          ILIKE %s OR
                    ct.numero_contrato ILIKE %s OR
                    ct.direccion       ILIKE %s
              )
            ORDER BY u.nombre
            LIMIT 15
        """, (like, like, like, like, like, like, like))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR buscar_clientes: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/buscar_cliente')
def api_buscar_cliente():
    """
    Usado por el formulario de Help Desk para ubicar al cliente
    que llamó, antes de registrar el reclamo en su nombre.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    q = (request.args.get('q') or '').strip()
    if len(q) < 3:
        return jsonify({'success': False, 'message': 'Escribe al menos 3 caracteres'}), 400
    filas = buscar_clientes(q)
    return jsonify({
        'success': True,
        'clientes': [
            {'usuario_id': f[0], 'nombre': f[1], 'apellido': f[2],
             'correo': f[3], 'telefono': f[4], 'codigo_cliente': f[5]}
            for f in filas
        ]
    })


@app.route('/soporte/reclamo_telefonico')
def soporte_reclamo_telefonico():
    """
    Página del formulario para que un agente de Help Desk registre
    un reclamo recibido por llamada (800161040 / 101), en nombre
    del cliente que llamó.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        flash('No tienes permisos para acceder a esta área.', 'danger')
        return redirect(url_for('inicio_sesion'))
    servicios_disponibles = obtener_servicios_disponibles()
    return render_template(
        'soporte_reclamo_telefonico.html',
        servicios=servicios_disponibles,
        nombre_usuario=session.get('nombre', ''),
    )

@app.route('/api/soporte/servicios_cliente/<int:usuario_id>')
def api_soporte_servicios_cliente(usuario_id):
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    servicios = obtener_servicios_usuario(usuario_id)
    return jsonify({
        'success': True,
        'servicios': [
            {
                'id': s[0],
                'tipo_servicio': s[1],
                'numero_servicio': s[2],
                'plan': s[3],
                'direccion_instalacion': s[7],
            }
            for s in servicios
        ]
    })

@app.route('/api/soporte/crear_reclamo_telefonico', methods=['POST'])
def api_crear_reclamo_telefonico():
    """
    Crea un reclamo en nombre de un cliente que llamó por teléfono.
    Replica la lógica de crear_reclamo() (prioridad automática,
    notificación a agentes, seguimiento) pero:
      - el titular es el usuario_id elegido en la búsqueda, no session
      - queda marcado con origen_reclamo='telefono'
      - guarda quién de Soporte lo registró (registrado_por)
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        data = request.get_json() or request.form
 
        usuario_cliente_id = data.get('usuario_id')
        contrato_id          = data.get('contrato_id')
        tipo_reclamo         = data.get('tipo_reclamo')
        titulo                = data.get('titulo')
        descripcion           = (data.get('descripcion') or '').strip()
        servicio_afectado     = (data.get('servicio_afectado') or '').strip()
        problema_especifico   = data.get('problema_especifico')
        ubicacion_cliente     = (data.get('ubicacion_cliente') or '').strip()
        numero_cliente        = (data.get('numero_cliente') or '').strip()
        telefono_referencia   = (data.get('telefono_referencia') or '').strip()
        telefono_cliente      = (data.get('telefono_cliente') or '').strip()
 
        if not all([usuario_cliente_id, tipo_reclamo, titulo]):
            return jsonify({
                'success': False,
                'message': 'Cliente, tipo y título son obligatorios.'
            }), 400
 
        if not descripcion:
            descripcion = 'Sin descripción adicional proporcionada por el cliente.'
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT u.usuario_id FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE u.usuario_id = %s AND LOWER(r.rol) = 'cliente'
        """, (usuario_cliente_id,))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Cliente no encontrado'}), 404
 
        if contrato_id:
            cur.execute("""
                SELECT tipo_servicio, numero_contrato, direccion, zona_id
                FROM contratos WHERE id = %s AND usuario_id = %s AND activo = TRUE
            """, (contrato_id, usuario_cliente_id))
            contrato = cur.fetchone()
            if contrato:
                servicio_afectado = contrato[0]
                numero_cliente    = contrato[1]
                ubicacion_cliente = contrato[2] or ubicacion_cliente
                if contrato[3]:
                    cur.execute("""
                        UPDATE usuarios SET zona_id = COALESCE(zona_id, %s)
                        WHERE usuario_id = %s
                    """, (contrato[3], usuario_cliente_id))
 
        notas_extra = []
        if telefono_referencia:
            notas_extra.append(f"Teléfono de referencia (contacto): {telefono_referencia}")
        if telefono_cliente:
            notas_extra.append(f"Teléfono en factura indicado por el cliente: {telefono_cliente}")
        if notas_extra:
            descripcion = f"{descripcion}\n\n" + "\n".join(notas_extra)
 
        monto_adeudado, estado_cuenta = obtener_estado_cuenta_cliente(usuario_cliente_id)
 
        # ── BLOQUEO POR MORA ─────────────────────────────────
        if estado_cuenta == 'mora':
            return jsonify({
                'success': False,
                'message': f'Este cliente tiene facturas vencidas (Bs. {float(monto_adeudado):.2f}). '
                           f'No se puede registrar un reclamo técnico mientras esté en mora — '
                           f'orienta al cliente a regularizar su pago primero.'
            }), 400
 
        prioridad = 'media'
        if problema_especifico and any(p in problema_especifico for p in ['Sin Conexión', 'Sin Señal']):
            prioridad = 'alta'

        ubicacion_lat = data.get('ubicacion_lat') or None
        ubicacion_lng = data.get('ubicacion_lng') or None

        if not telefono_referencia:
            return jsonify({'success': False, 'message': 'El teléfono de referencia es obligatorio.'}), 400

        nocturno = es_turno_nocturno()
        if nocturno:
            prioridad = 'alta'

        cur.execute("""
            INSERT INTO reclamos
                (usuario_id, tipo_reclamo, titulo, descripcion,
                 servicio_afectado, problema_especifico, ubicacion_cliente,
                 numero_cliente, estado_cuenta, monto_adeudado,
                 estado, prioridad, fecha_creacion,
                 origen_reclamo, registrado_por,
                 telefono_referencia, ubicacion_lat, ubicacion_lng, fuera_de_horario,
                 es_turno_nocturno)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'abierto',%s,%s,'telefono',%s,%s,%s,%s,
                    (EXTRACT(HOUR FROM NOW() AT TIME ZONE 'America/La_Paz') < 8
                     OR EXTRACT(HOUR FROM NOW() AT TIME ZONE 'America/La_Paz') >= 20),
                    %s)
            RETURNING id
        """, (usuario_cliente_id, tipo_reclamo, titulo, descripcion,
              servicio_afectado or None, problema_especifico, ubicacion_cliente or None,
              numero_cliente or None, estado_cuenta, monto_adeudado,
              prioridad, datetime.now(), session['usuario_id'],
              telefono_referencia, ubicacion_lat, ubicacion_lng, nocturno))
        reclamo_id = cur.fetchone()[0]
 
        registrar_seguimiento_reclamo(
            reclamo_id, obtener_empleado_id_por_usuario(session['usuario_id']),
            'creado',
            f"Reclamo registrado telefónicamente (101/800161040) por "
            f"{session.get('nombre','agente de soporte')}."
        )
        conn.commit()
 
        asignar_reclamo_automaticamente(reclamo_id, tipo_reclamo, problema_especifico)
 
        return jsonify({
            'success':    True,
            'reclamo_id': reclamo_id,
            'prioridad':  prioridad,
            'estado_cuenta': estado_cuenta,
            'message': f'Reclamo #{reclamo_id} registrado. Continúa con el diagnóstico remoto.'
        })
 
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_crear_reclamo_telefonico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 

        

@app.route('/api/soporte/contratos_cliente/<int:usuario_id>')
def api_soporte_contratos_cliente(usuario_id):
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    filas = obtener_contratos_usuario(usuario_id)
    return jsonify({
        'success': True,
        'contratos': [
            {
                'id': f[0],
                'numero_contrato': f[1],
                'tipo_servicio': f[2],
                'direccion': f[3],
                'telefono_referencia': f[4],
                'telefono_factura': f[5],
                'zona': f[6],
            }
            for f in filas
        ]
    })


@app.route('/api/soporte/enviar_jefe_instancia/<int:reclamo_id>', methods=['POST'])
def api_soporte_enviar_jefe_instancia(reclamo_id):
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id, estado FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404

        ESTADOS_BLOQUEADOS = ('cerrado', 'auditado', 'liberado')
        if reclamo[1] in ESTADOS_BLOQUEADOS:
            return jsonify({'success': False, 'message': f'El reclamo ya está en estado "{reclamo[1]}".'}), 400

        cur.execute("""
            UPDATE reclamos
            SET estado = 'pendiente_asignacion', instancia = 1
            WHERE id = %s
        """, (reclamo_id,))

        empleado_id = obtener_empleado_id_por_usuario(session['usuario_id'])
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, %s, 'pendiente_asignacion',
                    'Help Desk envió el reclamo al Jefe de 1ra Instancia para asignación de técnico.')
        """, (reclamo_id, empleado_id))

        conn.commit()

        notificar_jefes_instancia(
            1, reclamo_id,
            f'Help Desk envió el reclamo #{reclamo_id} (falla masiva) a 1ra Instancia para asignación de técnico.'
        )

        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} enviado al Jefe de 1ra Instancia.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_soporte_enviar_jefe_instancia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/continuar_diagnostico/<int:reclamo_id>')
def api_continuar_diagnostico(reclamo_id):
    """
    A diferencia de iniciar_diagnostico, este NO crea un registro nuevo.
    Solo recupera el diagnóstico en curso para que el agente pueda seguir
    llenándolo y finalizarlo, sin chocar con el bloqueo de re-inicio.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT estado FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
        if reclamo[0] != 'en_diagnostico':
            return jsonify({'success': False, 'message': f'Este reclamo está en estado "{reclamo[0]}", no en diagnóstico activo.'}), 400
 
        cur.execute("""
            SELECT d.id, d.reinicio_onu, d.validacion_potencia, d.reconfiguracion,
                   d.reinicio_puerto, d.sincronizacion, d.cambio_perfil,
                   d.codigo_falla_id, d.observaciones, d.elemento_afectado_id
            FROM diagnosticos_remotos d
            WHERE reclamo_id = %s AND fecha_fin IS NULL
            ORDER BY fecha_creacion DESC
            LIMIT 1
        """, (reclamo_id,))
        diag = cur.fetchone()
        if not diag:
            return jsonify({'success': False, 'message': 'No se encontró un diagnóstico activo para este reclamo.'}), 404
 
        return jsonify({
            'success': True, 'diagnostico_id': diag[0],
            'reinicio_onu': diag[1], 'validacion_potencia': diag[2],
            'reconfiguracion': diag[3], 'reinicio_puerto': diag[4],
            'sincronizacion': diag[5], 'cambio_perfil': diag[6],
            'codigo_falla_id': diag[7], 'observaciones': diag[8] or '',
            'elemento_afectado_id': diag[9],
        })
    except Exception as e:
        print(f"ERROR api_continuar_diagnostico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 


@app.route('/api/soporte/estado_cuenta_cliente/<int:usuario_id>')
def api_soporte_estado_cuenta_cliente(usuario_id):
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    monto_adeudado, estado_cuenta = obtener_estado_cuenta_cliente(usuario_id)

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, total, fecha_vencimiento, estado
            FROM facturas
            WHERE usuario_id = %s AND estado = 'pendiente'
            ORDER BY fecha_vencimiento ASC
        """, (usuario_id,))
        facturas_pendientes = cur.fetchall()

        return jsonify({
            'success': True,
            'estado_cuenta': estado_cuenta,           
            'monto_adeudado': float(monto_adeudado),
            'en_riesgo_corte': estado_cuenta == 'mora',
            'facturas_pendientes': [
                {
                    'id': f[0], 'total': float(f[1]),
                    'fecha_vencimiento': f[2].strftime('%d/%m/%Y') if f[2] else None,
                    'dias_vencida': (datetime.now().date() - f[2]).days if f[2] and f[2] < datetime.now().date() else 0
                }
                for f in facturas_pendientes
            ]
        })
    except Exception as e:
        print(f"ERROR api_soporte_estado_cuenta_cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/historial_reclamos_cliente/<int:usuario_id>')
def api_soporte_historial_reclamos_cliente(usuario_id):
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                r.id, r.tipo_reclamo, r.servicio_afectado, r.problema_especifico,
                r.estado, r.fecha_creacion, r.fecha_resolucion,
                r.solucion, r.liberado_ivr, r.fecha_liberacion_ivr,
                aq.fecha_auditoria, aq.resultado
            FROM reclamos r
            LEFT JOIN auditorias_calidad aq ON aq.reclamo_id = r.id
            WHERE r.usuario_id = %s
            ORDER BY r.fecha_creacion DESC
        """, (usuario_id,))
        filas = cur.fetchall()

        return jsonify({
            'success': True,
            'total': len(filas),
            'reclamos': [
                {
                    'id': f[0],
                    'tipo_reclamo': f[1],
                    'servicio_afectado': f[2] or 'N/A',
                    'problema_especifico': f[3] or 'No especificado',
                    'estado': f[4],
                    'fecha_falla': f[5].strftime('%d/%m/%Y %H:%M') if f[5] else None,
                    'fecha_resolucion': f[6].strftime('%d/%m/%Y %H:%M') if f[6] else None,
                    'solucion': f[7] or None,
                    'liberado_ivr': f[8],
                    'fecha_liberacion': f[9].strftime('%d/%m/%Y %H:%M') if f[9] else None,
                    'fecha_auditoria_calidad': f[10].strftime('%d/%m/%Y %H:%M') if f[10] else None,
                    'resultado_auditoria': f[11] or None,
                }
                for f in filas
            ]
        })
    except Exception as e:
        print(f"ERROR api_soporte_historial_reclamos_cliente: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
#-------------------------------------------------
## SOPORTE PARA RECLAMOS Y DESIGANCION DE TECNICOS 

@app.route('/api/soporte/reclamo/<int:reclamo_id>')
def api_soporte_reclamo(reclamo_id):
    if 'usuario_id' not in session or session.get('rol') != 'help_desk':
        return jsonify({'success': False, 'message': 'Sin permisos'})
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        # Datos del reclamo
        cur.execute("""
            SELECT r.id, u.nombre, u.apellido, r.tipo_reclamo, r.titulo,
                r.estado, r.fecha_creacion, r.prioridad,
                r.servicio_afectado, r.problema_especifico,
                r.descripcion, r.asignado_a,
                COALESCE(
                    ut.nombre || ' ' || ut.apellido,
                    es.nombre_completo,
                    NULL
                ) AS nombre_asignado,
                r.telefono_referencia, r.ubicacion_cliente,
                r.es_turno_nocturno, r.escalado_a,
                r.ubicacion_lat, r.ubicacion_lng
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN tecnicos t           ON r.asignado_a = t.id
            LEFT JOIN usuarios ut          ON t.usuario_id  = ut.usuario_id
            LEFT JOIN empleados_soporte es ON r.asignado_a = es.id
            WHERE r.id = %s
        """, (reclamo_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'})
 
        reclamo = {
            'id': row[0], 'nombre': row[1], 'apellido': row[2],
            'tipo_reclamo': row[3], 'titulo': row[4], 'estado': row[5],
            'fecha_creacion': row[6].strftime('%d/%m/%Y %H:%M') if row[6] else None,
            'prioridad': row[7], 'servicio_afectado': row[8],
            'problema_especifico': row[9], 'descripcion': row[10],
            'asignado_a': row[11],
            'nombre_asignado': row[12],
            'telefono_referencia': row[13],
            'ubicacion_cliente': row[14],
            'es_turno_nocturno': row[15],
            'escalado_a': row[16],
            'ubicacion_lat': float(row[17]) if row[17] is not None else None,
            'ubicacion_lng': float(row[18]) if row[18] is not None else None,
        }
 
       
        cur.execute("""
            SELECT t.id,
                u.nombre || ' ' || u.apellido AS nombre_completo,
                t.especialidad,
                t.tipo_tecnico,
                COUNT(r2.id) AS reclamos_activos
            FROM tecnicos t
            JOIN usuarios u ON u.usuario_id = t.usuario_id
            LEFT JOIN reclamos r2
                ON r2.asignado_a = t.id AND r2.estado = 'en_proceso'
            WHERE t.activo = TRUE
            GROUP BY t.id, u.nombre, u.apellido, t.especialidad, t.tipo_tecnico
            ORDER BY reclamos_activos ASC, u.nombre ASC
        """)
        tecnicos = [
            {
                'id': t[0],
                'nombre_completo': t[1],
                'especialidad': t[2],
                'tipo_tecnico': t[3],        # 'RA' | 'RC' | None
                'reclamos_activos': t[4]
            }
            for t in cur.fetchall()
        ]
 
        return jsonify({'success': True, 'reclamo': reclamo, 'tecnicos': tecnicos})
 
    except Exception as e:
        print(f"ERROR api_soporte_reclamo: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cur:  cur.close()
        if conn: conn.close()

@app.route('/api/soporte/tecnicos_por_tipo/<tipo>')
def api_soporte_tecnicos_por_tipo(tipo):
    """
    Ruta NUEVA: lista solo técnicos RA o RC, para un filtro rápido
    en el modal de asignación (ej: botones "Ver solo RA" / "Ver solo RC").
    """
    if 'usuario_id' not in session or session.get('rol') != 'help_desk':
        return jsonify({'success': False, 'message': 'Sin permisos'}), 401
 
    tipo = tipo.strip().upper()
    if tipo not in ('RA', 'RC'):
        return jsonify({'success': False, 'message': 'tipo debe ser RA o RC'}), 400
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT t.id,
                u.nombre || ' ' || u.apellido AS nombre_completo,
                t.especialidad, t.tipo_tecnico,
                COUNT(r2.id) AS reclamos_activos
            FROM tecnicos t
            JOIN usuarios u ON u.usuario_id = t.usuario_id
            LEFT JOIN reclamos r2 ON r2.asignado_a = t.id AND r2.estado = 'en_proceso'
            WHERE t.activo = TRUE AND t.tipo_tecnico = %s
            GROUP BY t.id, u.nombre, u.apellido, t.especialidad, t.tipo_tecnico
            ORDER BY reclamos_activos ASC, u.nombre ASC
        """, (tipo,))
        tecnicos = [
            {'id': t[0], 'nombre_completo': t[1], 'especialidad': t[2],
             'tipo_tecnico': t[3], 'reclamos_activos': t[4]}
            for t in cur.fetchall()
        ]
        return jsonify({'success': True, 'tecnicos': tecnicos})
    except Exception as e:
        print(f"ERROR api_soporte_tecnicos_por_tipo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
@app.route('/api/soporte/asignar_tecnico/<int:reclamo_id>', methods=['POST'])
def api_asignar_tecnico(reclamo_id):
    """
    Sin cambios de lógica respecto a tu versión original — la incluyo
    completa aquí para que tengas el flujo entero de asignación en un
    solo lugar, ya que ahora depende de la lista de técnicos con
    tipo_tecnico que devuelve api_soporte_reclamo.
    """
    if 'usuario_id' not in session or session.get('rol') != 'help_desk':
        return jsonify({'success': False, 'message': 'Sin permisos'})
 
    data       = request.get_json()
    tecnico_id = data.get('tecnico_id')
    nota       = data.get('nota', '')
 
    if not tecnico_id:
        return jsonify({'success': False, 'message': 'Técnico requerido'})
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT r.id, r.titulo, r.descripcion, r.tipo_reclamo,
                   r.prioridad, r.servicio_afectado, r.problema_especifico,
                   r.usuario_id,
                   u.nombre, u.apellido
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            WHERE r.id = %s
        """, (reclamo_id,))
        reclamo = cur.fetchone()
 
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'})
 
        cur.execute("""
            UPDATE reclamos
            SET asignado_a       = %s,
                estado           = 'en_proceso',
                nota_tecnico     = %s,
                fecha_asignacion = NOW()
            WHERE id = %s
        """, (tecnico_id, nota, reclamo_id))
 
        cur.execute("SELECT NEXTVAL('seq_numero_ot')")
        seq = cur.fetchone()[0]
        numero_ot = f"OT-{seq:04d}"
 
        prioridad_map = {'critica': 'critica', 'alta': 'alta', 'media': 'media', 'baja': 'baja'}
        prioridad_ot = prioridad_map.get(reclamo[4], 'media')
 
        descripcion_ot = reclamo[2] or reclamo[6] or 'Sin descripción'
        if nota:
            descripcion_ot += f"\n\nNota del supervisor: {nota}"
 
        cur.execute("""
            INSERT INTO ordenes_trabajo (
                numero_ot, titulo, descripcion,
                tipo_trabajo, prioridad, estado,
                tecnico_id, usuario_cliente_id,
                observaciones, creado_por,
                reclamo_id,
                fecha_creacion, fecha_actualizacion
            ) VALUES (%s,%s,%s,%s,%s,'pendiente',%s,%s,%s,%s,%s,
                NOW(), NOW()
            )
            RETURNING id
        """, (
            numero_ot,
            f"[{reclamo[3]}] {reclamo[1]}",
            descripcion_ot,
            reclamo[3],
            prioridad_ot,
            tecnico_id,
            reclamo[7],
            nota or None,
            session['usuario_id'],
            reclamo_id,
        ))
        ot_id = cur.fetchone()[0]
 
        cur.execute("""
            INSERT INTO ot_actividades (ot_id, tecnico_id, descripcion, tipo)
            VALUES (%s, %s, %s, 'nota')
        """, (
            ot_id,
            tecnico_id,
            f"OT creada por soporte a partir del reclamo #{reclamo_id}. "
            f"Cliente: {reclamo[8]} {reclamo[9] or ''}."
            + (f" Instrucciones: {nota}" if nota else "")
        ))
 
        conn.commit()
        return jsonify({'success': True, 'numero_ot': numero_ot, 'ot_id': ot_id})
 
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_asignar_tecnico: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 

@app.route('/api/soporte/notas_ot/<int:reclamo_id>')
def api_soporte_notas_ot(reclamo_id):
    if 'usuario_id' not in session or session.get('rol') != 'help_desk':
        return jsonify({'success': False, 'message': 'Sin permisos'})
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT 
                a.descripcion, a.tipo, 
                a.fecha,
                u.nombre || ' ' || u.apellido AS tecnico_nombre
            FROM ot_actividades a
            JOIN tecnicos t ON a.tecnico_id = t.id
            JOIN usuarios u ON t.usuario_id = u.usuario_id
            JOIN ordenes_trabajo ot ON a.ot_id = ot.id
            WHERE ot.reclamo_id = %s
            ORDER BY a.fecha DESC
        """, (reclamo_id,))
        notas = [
            {
                'descripcion': row[0],
                'tipo':        row[1],
                'fecha':       row[2].strftime('%d/%m/%Y %H:%M') if row[2] else '—',
                'tecnico':     row[3],
            }
            for row in cur.fetchall()
        ]
        return jsonify({'success': True, 'notas': notas})
    except Exception as e:
        print(f"ERROR api_soporte_notas_ot: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/procesar_reclamo/<int:reclamo_id>', methods=['POST'])
def api_procesar_reclamo(reclamo_id):
    if 'usuario_id' not in session or session.get('rol') != 'help_desk':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT id FROM reclamos WHERE id=%s", (reclamo_id,))
        if not cur.fetchone(): return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
        cur.execute("UPDATE reclamos SET estado='resuelto', fecha_resolucion=NOW() WHERE id=%s", (reclamo_id,))
        try:
            emp = obtener_empleado_soporte_por_usuario(session['usuario_id'])
            if emp:
                cur.execute("INSERT INTO reclamos_seguimiento (reclamo_id,empleado_id,accion,descripcion) VALUES (%s,%s,'resuelto','Resuelto desde dashboard')", (reclamo_id, emp[0]))
                cur.execute("UPDATE empleados_soporte SET carga_trabajo=GREATEST(0,carga_trabajo-1) WHERE id=%s", (emp[0],))
        except Exception: pass
        conn.commit()
        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} resuelto'})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()

#__________________ HELPER PARA NOTIFICAR A TODOS LOS JEFES DE INSTANCIA_______________
# PARA ANULAR EL RECLAMO PENDIENTE POR QUE ESTA SOLUCIONADO 
def notificar_jefes_instancia(instancia, reclamo_id, mensaje, asunto=None):
    """
    Notifica SOLO a los Jefes activos de la instancia dada que además
    pertenecen a la misma zona que el cliente del reclamo. Si el cliente
    no tiene zona asignada, cae en fallback: notifica a todos los Jefes
    de esa instancia (mejor avisar de más que dejar el reclamo huérfano).
    """
    rol_buscado = 'jefe_primera_instancia' if instancia == 1 else 'jefe_segunda_instancia'
    zona_id_reclamo, zona_nombre_reclamo = obtener_zona_reclamo(reclamo_id)

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        if zona_id_reclamo:
            cur.execute("""
                SELECT u.usuario_id, u.nombre, u.correo
                FROM usuarios u
                JOIN roles r ON u.id_rol = r.id_rol
                WHERE LOWER(r.rol) = %s AND u.activo = TRUE AND u.zona_id = %s
            """, (rol_buscado, zona_id_reclamo))
        else:
            cur.execute("""
                SELECT u.usuario_id, u.nombre, u.correo
                FROM usuarios u
                JOIN roles r ON u.id_rol = r.id_rol
                WHERE LOWER(r.rol) = %s AND u.activo = TRUE
            """, (rol_buscado,))
        jefes = cur.fetchall()

        if zona_id_reclamo and zona_nombre_reclamo:
            mensaje = f"{mensaje} (Zona: {zona_nombre_reclamo})"

        for jefe_id, jefe_nombre, jefe_correo in jefes:
            cur.execute("""
                INSERT INTO notificaciones_jefe (usuario_id, reclamo_id, tipo, mensaje)
                VALUES (%s, %s, 'nuevo_reclamo', %s)
            """, (jefe_id, reclamo_id, mensaje))

            if jefe_correo:
                try:
                    msg = Message(
                        subject=asunto or f'COTEL RL — Reclamo #{reclamo_id} pendiente de asignación',
                        sender=('COTEL RL', app.config['MAIL_USERNAME']),
                        recipients=[jefe_correo]
                    )
                    msg.html = f'''
                        <h2>Nuevo reclamo pendiente</h2>
                        <p>Hola {jefe_nombre},</p>
                        <p>{mensaje}</p>
                        <p><strong>N° de reclamo:</strong> #{reclamo_id}</p>
                        <p>Ingresa a tu panel de Jefe de Instancia para asignarlo a un técnico.</p>
                    '''
                    mail.send(msg)
                except Exception as mail_error:
                    print(f"WARN: no se pudo enviar correo a {jefe_correo}: {mail_error}")

        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR notificar_jefes_instancia: {e}")
    finally:
        if cur:  cur.close()
        if conn: conn.close()
#
def notificar_jefes_especialidad(instancia, reclamo_id, mensaje, asunto=None):
    """
    Notifica a todos los Jefe DRA (instancia=1) o Jefe DRC
    (instancia=2) activos. Sin filtro de zona — no tienen zona propia.
    """
    rol_buscado = 'jefe_dra' if instancia == 1 else 'jefe_drc'
    asunto = asunto or f'COTEL RL — Reclamo #{reclamo_id} actualizado'
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT u.usuario_id, u.nombre, u.correo
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            WHERE LOWER(r.rol) = %s AND u.activo = TRUE
        """, (rol_buscado,))
        jefes = cur.fetchall()
 
        for jefe_id, jefe_nombre, jefe_correo in jefes:
            cur.execute("""
                INSERT INTO notificaciones_jefe (usuario_id, reclamo_id, tipo, mensaje)
                VALUES (%s, %s, 'reclamo_finalizado', %s)
            """, (jefe_id, reclamo_id, mensaje))
 
            if jefe_correo:
                try:
                    msg = Message(
                        subject=asunto,
                        sender=('COTEL RL', app.config['MAIL_USERNAME']),
                        recipients=[jefe_correo]
                    )
                    msg.html = f'''
                        <h2>Actualización de reclamo</h2>
                        <p>Hola {jefe_nombre},</p>
                        <p>{mensaje}</p>
                        <p><strong>N° de reclamo:</strong> #{reclamo_id}</p>
                    '''
                    mail.send(msg)
                except Exception as mail_error:
                    print(f"WARN: no se pudo enviar correo a {jefe_correo}: {mail_error}")
 
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR notificar_jefes_especialidad: {e}")
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 

def obtener_codigo_ivr(servicio, medio):
    """Código IVR ('*108'|'*118'|'*128') según servicio+medio. Cae a '*108' si no hay match."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT codigo_ivr FROM codigos_ivr_liberacion
            WHERE servicio = %s AND medio = %s AND activo = TRUE
        """, (servicio, medio))
        row = cur.fetchone()
        return row[0] if row else '*108'
    except Exception as e:
        print(f"ERROR obtener_codigo_ivr: {e}")
        return '*108'
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
def normalizar_servicio(servicio_afectado):
    """Traduce el texto libre de reclamos.servicio_afectado a 'telefonia'|'tv_cable'|'internet'."""
    s = (servicio_afectado or '').strip().lower()
    if 'internet' in s or 'wifi' in s:
        return 'internet'
    if 'tv' in s or 'television' in s or 'televisión' in s or 'cable' in s:
        return 'tv_cable'
    if 'tel' in s:
        return 'telefonia'
    return 'internet'
 
 
def obtener_tecnicos_por_servicio_medio(servicio, medio, instancia=1):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT t.id,
                   u.nombre || ' ' || u.apellido AS nombre_completo,
                   t.especialidad, t.servicio_tecnico, t.medio_tecnico,
                   t.instancia_tecnico,
                   COUNT(r2.id) AS reclamos_activos
            FROM tecnicos t
            JOIN usuarios u ON u.usuario_id = t.usuario_id
            LEFT JOIN reclamos r2
                ON r2.asignado_a = t.id AND r2.estado = 'en_proceso'
            WHERE t.activo = TRUE
              AND t.instancia_tecnico = %s
              AND t.servicio_tecnico = %s
              AND (t.medio_tecnico = %s OR t.servicio_tecnico = 'transmisiones')
            GROUP BY t.id, u.nombre, u.apellido, t.especialidad,
                     t.servicio_tecnico, t.medio_tecnico, t.instancia_tecnico
            ORDER BY reclamos_activos ASC, u.nombre ASC
        """, (instancia, servicio, medio))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_tecnicos_por_servicio_medio: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
@app.route('/api/tecnico/rechazar_ot', methods=['POST'])
def api_tecnico_rechazar_ot():
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return jsonify({'success': False, 'message': 'Perfil técnico no encontrado'}), 403

    conn = cur = None
    try:
        data   = request.get_json()
        ot_id  = data.get('ot_id')
        motivo = (data.get('motivo') or '').strip()

        if not motivo:
            return jsonify({'success': False, 'message': 'Debes indicar el motivo del rechazo.'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("""
            SELECT id, estado, reclamo_id FROM ordenes_trabajo
            WHERE id = %s AND tecnico_id = %s
        """, (ot_id, tecnico[0]))
        ot = cur.fetchone()
        if not ot:
            return jsonify({'success': False, 'message': 'OT no encontrada'}), 404
        if ot[1] not in ('pendiente', 'en_proceso'):
            return jsonify({'success': False, 'message': f'No puedes rechazar una OT en estado "{ot[1]}".'}), 400

        reclamo_id = ot[2]
        if not reclamo_id:
            return jsonify({'success': False, 'message': 'Esta OT no está ligada a un reclamo.'}), 400

        cur.execute("""
            UPDATE ordenes_trabajo SET estado = 'rechazado', fecha_actualizacion = NOW()
            WHERE id = %s
        """, (ot_id,))

        cur.execute("""
            INSERT INTO ot_actividades (ot_id, tecnico_id, descripcion, tipo)
            VALUES (%s, %s, %s, 'nota')
        """, (ot_id, tecnico[0], f"Técnico rechazó la OT. Motivo: {motivo}"))

        cur.execute("""
            UPDATE reclamos SET
                estado = 'pendiente_asignacion',
                asignado_a = NULL,
                veces_rechazado = COALESCE(veces_rechazado, 0) + 1,
                motivo_rechazo = %s
            WHERE id = %s
        """, (motivo, reclamo_id))

        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'rechazado_tecnico', %s)
        """, (reclamo_id,
              f"Técnico {session.get('nombre','')} rechazó la asignación. Motivo: {motivo}. "
              f"El reclamo vuelve a la cola del Jefe de 1ra Instancia."))

        conn.commit()
        return jsonify({
            'success': True,
            'message': 'OT rechazada. El reclamo volvió a la cola del Jefe de 1ra Instancia.'
        })
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_tecnico_rechazar_ot: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()

 
@app.route('/api/jefe/derivar_2da_instancia', methods=['POST'])
def api_jefe_derivar_2da_instancia():
    if 'usuario_id' not in session or not verificar_rol('jefe_primera_instancia', 'administrador'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data        = request.get_json()
        reclamo_id  = data.get('reclamo_id')
        observacion = (data.get('observacion') or '').strip()
        if not reclamo_id:
            return jsonify({'success': False, 'message': 'reclamo_id es requerido'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT servicio_afectado FROM reclamos WHERE id = %s", (reclamo_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404

        escalado_a = normalizar_servicio(row[0])

        cur.execute("""
            UPDATE reclamos SET
                instancia        = 2,
                escalado_a       = %s,
                estado           = 'pendiente_asignacion',
                asignado_a       = NULL,
                fecha_escalacion = NOW()
            WHERE id = %s
        """, (escalado_a, reclamo_id))

        desc = f"El Jefe de 1ra Instancia ({session.get('nombre','')}) derivó el reclamo a 2da Instancia ({escalado_a})."
        if observacion:
            desc += f" Observación: {observacion}"

        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'escalado', %s)
        """, (reclamo_id, desc))

        cur.execute("""
            UPDATE ordenes_trabajo SET estado = 'cancelado', fecha_actualizacion = NOW()
            WHERE reclamo_id = %s AND estado NOT IN ('completado', 'cancelado')
        """, (reclamo_id,))

        conn.commit()
        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} derivado a 2da Instancia.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_jefe_derivar_2da_instancia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/tecnico/escalar_2da_instancia', methods=['POST'])
def api_tecnico_escalar_2da_instancia():
    """
    El técnico DRA (1ra instancia) marca que NO pudo resolver.
    Responde "¿Falla de energía o refrigeración?":
      True  -> escala a Responsable Transmisiones
      False -> escala a un técnico DRC del mismo servicio+medio
    """
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return jsonify({'success': False, 'message': 'Perfil técnico no encontrado'}), 403
 
    conn = cur = None
    try:
        data                        = request.get_json()
        ot_id                       = data.get('ot_id')
        falla_energia_refrigeracion = bool(data.get('falla_energia_refrigeracion'))
        observacion                 = (data.get('observacion') or '').strip()
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT id, reclamo_id FROM ordenes_trabajo
            WHERE id = %s AND tecnico_id = %s
        """, (ot_id, tecnico[0]))
        ot = cur.fetchone()
        if not ot or not ot[1]:
            return jsonify({'success': False, 'message': 'OT o reclamo no encontrado'}), 404
 
        reclamo_id = ot[1]
 
        cur.execute("SELECT servicio_afectado, medio_fisico FROM reclamos WHERE id = %s", (reclamo_id,))
        row = cur.fetchone()
        servicio_norm = normalizar_servicio(row[0] if row else '')
        medio         = (row[1] if row else None) or 'fibra_optica'
 
        escalado_a = 'transmisiones' if falla_energia_refrigeracion else servicio_norm
 
        cur.execute("""
            UPDATE reclamos SET
                instancia                   = 2,
                falla_energia_refrigeracion = %s,
                escalado_a                  = %s,
                estado                      = 'pendiente_asignacion',
                fecha_escalacion            = NOW()
            WHERE id = %s
        """, (falla_energia_refrigeracion, escalado_a, reclamo_id))
 
        cur.execute("""
            UPDATE ordenes_trabajo SET estado = 'cancelado', fecha_actualizacion = NOW()
            WHERE id = %s
        """, (ot_id,))
 
        desc = (
            f"Técnico DRA no pudo resolver. Escalado a "
            f"{'Responsable Transmisiones (falla de energía/refrigeración)' if falla_energia_refrigeracion else f'técnico DRC de {escalado_a}'}."
        )
        if observacion:
            desc += f" Observación: {observacion}"
 
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'escalado', %s)
        """, (reclamo_id, desc))
 
        conn.commit()
        return jsonify({'success': True, 'escalado_a': escalado_a, 'message': desc})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_tecnico_escalar_2da_instancia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
# ------------------------------------------------------------
@app.route('/api/admin/clasificar_tecnico/<int:usuario_id>', methods=['POST'])
def api_admin_clasificar_tecnico(usuario_id):
    if 'usuario_id' not in session or not verificar_rol('administrador', 'admin'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        data              = request.get_json()
        servicio_tecnico  = (data.get('servicio_tecnico') or '').strip().lower()
        medio_tecnico     = (data.get('medio_tecnico') or '').strip().lower() or None
        instancia_tecnico = int(data.get('instancia_tecnico') or 1)
 
        if servicio_tecnico not in ('telefonia', 'tv_cable', 'internet', 'transmisiones'):
            return jsonify({'success': False, 'message': 'servicio_tecnico inválido'}), 400
        if servicio_tecnico != 'transmisiones' and medio_tecnico not in ('fibra_optica', 'coaxial', 'cobre'):
            return jsonify({'success': False, 'message': 'medio_tecnico inválido para este servicio'}), 400
        if instancia_tecnico not in (1, 2):
            return jsonify({'success': False, 'message': 'instancia_tecnico debe ser 1 o 2'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE tecnicos SET
                servicio_tecnico  = %s,
                medio_tecnico     = %s,
                instancia_tecnico = %s
            WHERE usuario_id = %s
            RETURNING id
        """, (servicio_tecnico, medio_tecnico, instancia_tecnico, usuario_id))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Este usuario no tiene un registro de técnico'}), 404
        conn.commit()
        return jsonify({'success': True, 'message': 'Técnico clasificado correctamente.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_admin_clasificar_tecnico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()

 #==========================================================================
 # AREA DE TECNICO 

 
def obtener_tecnico_por_usuario(usuario_id):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, especialidad, zona_asignada, activo,
                   tipo_tecnico, servicio_tecnico, medio_tecnico, instancia_tecnico
            FROM tecnicos
            WHERE usuario_id = %s AND activo = TRUE
            LIMIT 1
        """, (usuario_id,))
        return cur.fetchone()
    
    except Exception as e:
        print(f"ERROR obtener_tecnico_por_usuario: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
def obtener_ots_tecnico(tecnico_id, estado=None, limit=50):
    """Devuelve las OT asignadas a un técnico, opcionalmente filtradas por estado."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        where = "WHERE ot.tecnico_id = %s"
        params = [tecnico_id]
 
        if estado and estado != 'todas':
            where += " AND ot.estado = %s"
            params.append(estado)
 
        cur.execute(f"""
            SELECT
                ot.id, ot.numero_ot, ot.titulo, ot.descripcion, ot.tipo_trabajo,
                ot.prioridad, ot.estado, ot.direccion, ot.fecha_programada,
                ot.fecha_inicio, ot.fecha_fin, ot.observaciones, ot.fecha_creacion,
                u.nombre AS cliente_nombre, u.apellido AS cliente_apellido,
                u.telefono AS cliente_telefono, u.correo AS cliente_correo,
                r.numero_cliente AS contrato,
                ot.area_dato_tecnico, ot.fecha_1er_informe, ot.fecha_2do_informe
            FROM ordenes_trabajo ot
            LEFT JOIN usuarios u ON ot.usuario_cliente_id = u.usuario_id
            LEFT JOIN reclamos r ON ot.reclamo_id = r.id
            {where}
            ORDER BY
                CASE ot.prioridad WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 WHEN 'baja' THEN 4 END,
                CASE ot.estado WHEN 'en_proceso' THEN 1 WHEN 'pendiente' THEN 2 WHEN 'completado' THEN 3 WHEN 'cancelado' THEN 4 END,
                ot.fecha_programada ASC NULLS LAST
            LIMIT %s
        """, params + [limit])
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_ots_tecnico: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
def obtener_estadisticas_tecnico(tecnico_id):
    """Cuenta OT por estado para las tarjetas del dashboard."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                COUNT(*)                                                       AS total,
                COUNT(CASE WHEN estado = 'pendiente'  THEN 1 END)             AS pendientes,
                COUNT(CASE WHEN estado = 'en_proceso' THEN 1 END)             AS en_proceso,
                COUNT(CASE WHEN estado = 'completado' THEN 1 END)             AS completadas,
                COUNT(CASE WHEN estado = 'completado'
                           AND DATE(fecha_fin AT TIME ZONE 'America/La_Paz') = 
                       CURRENT_DATE AT TIME ZONE 'America/La_Paz'
                   THEN 1 END)                                           AS hoy_completadas,
                COUNT(CASE WHEN prioridad IN ('alta','critica')
                           AND estado IN ('pendiente','en_proceso') THEN 1 END) AS urgentes
            FROM ordenes_trabajo
            WHERE tecnico_id = %s
        """, (tecnico_id,))
        row = cur.fetchone()
        if row:
            return {
                'total':          row[0] or 0,
                'pendientes':     row[1] or 0,
                'en_proceso':     row[2] or 0,
                'completadas':    row[3] or 0,
                'hoy_completadas':row[4] or 0,
                'urgentes':       row[5] or 0,
            }
        return {'total':0,'pendientes':0,'en_proceso':0,'completadas':0,'hoy_completadas':0,'urgentes':0}
    except Exception as e:
        print(f"ERROR obtener_estadisticas_tecnico: {e}")
        return {'total':0,'pendientes':0,'en_proceso':0,'completadas':0,'hoy_completadas':0,'urgentes':0}
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
def obtener_actividades_ot(ot_id):
    """Bitácora de actividades de una OT."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                a.id, a.descripcion, a.tipo, a.fecha,
                u.nombre, u.apellido
            FROM ot_actividades a
            JOIN tecnicos t ON a.tecnico_id = t.id
            JOIN usuarios  u ON t.usuario_id = u.usuario_id
            WHERE a.ot_id = %s
            ORDER BY a.fecha DESC
        """, (ot_id,))
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_actividades_ot: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
def crear_tablas_tecnico_si_no_existen():
    """Crea las tablas del módulo técnico si no existen."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tecnicos (
                id            SERIAL PRIMARY KEY,
                usuario_id    INTEGER REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
                especialidad  VARCHAR(100),
                zona_asignada VARCHAR(100),
                activo        BOOLEAN DEFAULT TRUE,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ordenes_trabajo (
                id                 SERIAL PRIMARY KEY,
                numero_ot          VARCHAR(20) UNIQUE NOT NULL,
                titulo             VARCHAR(200) NOT NULL,
                descripcion        TEXT,
                tipo_trabajo       VARCHAR(100),
                prioridad          VARCHAR(20) DEFAULT 'media',
                estado             VARCHAR(30) DEFAULT 'pendiente',
                tecnico_id         INTEGER REFERENCES tecnicos(id),
                usuario_cliente_id INTEGER REFERENCES usuarios(usuario_id),
                direccion          VARCHAR(300),
                coordenadas        VARCHAR(100),
                fecha_programada   TIMESTAMP,
                fecha_inicio       TIMESTAMP,
                fecha_fin          TIMESTAMP,
                observaciones      TEXT,
                creado_por         INTEGER REFERENCES usuarios(usuario_id),
                fecha_creacion     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ot_actividades (
                id          SERIAL PRIMARY KEY,
                ot_id       INTEGER REFERENCES ordenes_trabajo(id) ON DELETE CASCADE,
                tecnico_id  INTEGER REFERENCES tecnicos(id),
                descripcion TEXT NOT NULL,
                tipo        VARCHAR(50) DEFAULT 'nota',
                fecha       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
       
        conn.commit()
    except Exception as e:
        print(f"ERROR crear_tablas_tecnico: {e}")
        if conn: conn.rollback()
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
def asegurar_registro_tecnico(usuario_id, tipo_tecnico=None,
                               servicio_tecnico=None, medio_tecnico=None,
                               instancia_tecnico=1):
    """
    - tipo_tecnico: 'RA' | 'RC' (clasificación previa, se conserva)
    - servicio_tecnico: 'telefonia' | 'tv_cable' | 'internet' | 'transmisiones'
    - medio_tecnico: 'fibra_optica' | 'coaxial' | 'cobre' (NULL en transmisiones)
    - instancia_tecnico: 1 (DRA / Planta Externa 1ra instancia)
                         2 (DRC / 2da instancia / Transmisiones)
    """
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM tecnicos WHERE usuario_id = %s", (usuario_id,))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO tecnicos (usuario_id, especialidad, zona_asignada, activo,
                                       tipo_tecnico, servicio_tecnico, medio_tecnico, instancia_tecnico)
                VALUES (%s, 'General', 'Sin asignar', TRUE, %s, %s, %s, %s)
            """, (
                usuario_id,
                tipo_tecnico if tipo_tecnico in ('RA', 'RC') else None,
                servicio_tecnico if servicio_tecnico in ('telefonia', 'tv_cable', 'internet', 'transmisiones') else None,
                medio_tecnico if medio_tecnico in ('fibra_optica', 'coaxial', 'cobre') else None,
                instancia_tecnico if instancia_tecnico in (1, 2) else 1,
            ))
            conn.commit()
    except Exception as e:
        print(f"ERROR asegurar_registro_tecnico: {e}")
        if conn: conn.rollback()
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
#============================================================
#HELPERS DE JEFES 
# ============================================================   
def obtener_estadisticas_jefe(instancia, zona_id=None):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        filtro_zona = "AND u.zona_id = %s" if zona_id else ""
        params_base = [zona_id] if zona_id else []

        if instancia == 1:
            cur.execute(f"""
                SELECT
                    COUNT(*) FILTER (WHERE r.instancia = 1 AND r.estado IN ('pendiente_asignacion','abierto')) AS sin_asignar,
                    COUNT(*) FILTER (WHERE r.instancia = 1 AND r.estado = 'en_proceso')                        AS en_proceso,
                    COUNT(*) FILTER (WHERE r.instancia = 2 AND r.fecha_escalacion >= NOW() - INTERVAL '24 hours') AS relacionado_24h,
                    COUNT(*) FILTER (WHERE r.estado IN ('liberado','cerrado','auditado')
                                      AND r.instancia = 1 AND r.fecha_resolucion >= NOW() - INTERVAL '24 hours') AS resueltos_24h
                FROM reclamos r
                JOIN usuarios u ON r.usuario_id = u.usuario_id
                WHERE 1=1 {filtro_zona}
            """, params_base)
        else:
            cur.execute(f"""
                SELECT
                    COUNT(*) FILTER (WHERE r.escalado_a = 'transmisiones' AND r.estado NOT IN ('liberado','cerrado','auditado')) AS sin_asignar,
                    COUNT(*) FILTER (WHERE r.escalado_a IN ('telefonia','tv_cable','internet') AND r.estado NOT IN ('liberado','cerrado','auditado')) AS en_proceso,
                    0 AS relacionado_24h,
                    COUNT(*) FILTER (WHERE r.instancia = 2 AND r.estado IN ('liberado','cerrado','auditado')
                                      AND r.fecha_resolucion >= NOW() - INTERVAL '24 hours') AS resueltos_24h
                FROM reclamos r
                JOIN usuarios u ON r.usuario_id = u.usuario_id
                WHERE r.instancia = 2 {filtro_zona}
            """, params_base)
        row = cur.fetchone()

        if zona_id:
            cur.execute("""
                SELECT COUNT(*) FROM tecnicos
                WHERE activo = TRUE AND instancia_tecnico = %s AND zona_id = %s
            """, (instancia, zona_id))
        else:
            cur.execute("SELECT COUNT(*) FROM tecnicos WHERE activo = TRUE AND instancia_tecnico = %s", (instancia,))
        total_tecnicos = cur.fetchone()[0]

        return {
            'sin_asignar':      row[0] or 0,
            'en_proceso':       row[1] or 0,
            'relacionado_24h':  row[2] or 0,
            'resueltos_24h':    row[3] or 0,
            'total_tecnicos':   total_tecnicos,
        }
    except Exception as e:
        print(f"ERROR obtener_estadisticas_jefe: {e}")
        return {'sin_asignar':0,'en_proceso':0,'relacionado_24h':0,'resueltos_24h':0,'total_tecnicos':0}
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
def obtener_reclamos_jefe(instancia, zona_id=None):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        filtro_zona = "AND u.zona_id = %s" if zona_id else ""
        params_zona = [zona_id] if zona_id else []

        if instancia == 1:
            cur.execute(f"""
                SELECT r.id, u.nombre, u.apellido, r.servicio_afectado, r.medio_fisico,
                       NULL AS escalado_a, NULL AS falla_energia, r.estado, r.prioridad, r.fecha_creacion,
                       COALESCE(ut.nombre || ' ' || ut.apellido, '— sin asignar —') AS tecnico_asignado,
                       COALESCE(r.veces_rechazado, 0) AS veces_rechazado, r.motivo_rechazo,
                       z.nombre AS zona
                FROM reclamos r
                JOIN usuarios u ON r.usuario_id = u.usuario_id
                LEFT JOIN zonas z ON u.zona_id = z.id
                LEFT JOIN tecnicos t  ON r.asignado_a = t.id
                LEFT JOIN usuarios ut ON t.usuario_id = ut.usuario_id
                WHERE r.instancia = 1
                  AND r.estado IN ('pendiente_asignacion','abierto','en_proceso')
                  {filtro_zona}
                ORDER BY
                    CASE r.prioridad WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END,
                    r.fecha_creacion ASC
                LIMIT 50
            """, params_zona)
        else:
            cur.execute(f"""
                SELECT r.id, u.nombre, u.apellido, r.servicio_afectado, r.medio_fisico,
                       r.escalado_a, r.falla_energia_refrigeracion, r.estado, r.prioridad, r.fecha_escalacion,
                       COALESCE(ut.nombre || ' ' || ut.apellido, '— sin asignar —') AS tecnico_asignado,
                       z.nombre AS zona
                FROM reclamos r
                JOIN usuarios u ON r.usuario_id = u.usuario_id
                LEFT JOIN zonas z ON u.zona_id = z.id
                LEFT JOIN tecnicos t  ON r.asignado_a = t.id
                LEFT JOIN usuarios ut ON t.usuario_id = ut.usuario_id
                WHERE r.instancia = 2
                  AND r.estado NOT IN ('liberado','cerrado','auditado')
                  {filtro_zona}
                ORDER BY
                    CASE r.prioridad WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END,
                    r.fecha_escalacion ASC
                LIMIT 50
            """, params_zona)
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_reclamos_jefe: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
def obtener_tecnicos_jefe(instancia, zona_id=None):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        filtro_zona = "AND t.zona_id = %s" if zona_id else ""
        params = [instancia] + ([zona_id] if zona_id else [])
        cur.execute(f"""
            SELECT t.id, u.nombre || ' ' || u.apellido, t.servicio_tecnico, t.medio_tecnico,
                   COUNT(r2.id) AS activos, z.nombre AS zona
            FROM tecnicos t
            JOIN usuarios u ON u.usuario_id = t.usuario_id
            LEFT JOIN zonas z ON t.zona_id = z.id
            LEFT JOIN reclamos r2 ON r2.asignado_a = t.id AND r2.estado = 'en_proceso'
            WHERE t.activo = TRUE AND t.instancia_tecnico = %s {filtro_zona}
            GROUP BY t.id, u.nombre, u.apellido, t.servicio_tecnico, t.medio_tecnico, z.nombre
            ORDER BY t.servicio_tecnico NULLS FIRST, t.medio_tecnico
        """, params)
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_tecnicos_jefe: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def obtener_trabajos_reparados(instancia=None, tecnico_id=None, limit=20):
    """Bitácora de trabajos completados (tabla trabajos_reparados)."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        where  = ["1=1"]
        params = []
        if instancia is not None:
            where.append("tr.instancia = %s")
            params.append(instancia)
        if tecnico_id is not None:
            where.append("tr.tecnico_id = %s")
            params.append(tecnico_id)
        params.append(limit)
        cur.execute(f"""
            SELECT tr.id, tr.numero_ot, u.nombre || ' ' || u.apellido AS tecnico,
                   tr.servicio, tr.medio, tr.codigo_ivr, tr.duracion_min, tr.fecha_fin
            FROM trabajos_reparados tr
            JOIN tecnicos t  ON tr.tecnico_id = t.id
            JOIN usuarios u  ON t.usuario_id = u.usuario_id
            WHERE {' AND '.join(where)}
            ORDER BY tr.fecha_fin DESC
            LIMIT %s
        """, params)
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_trabajos_reparados: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
# ------------------------------------------------------------
@app.route('/dashboard_jefe')
def dashboard_jefe():
    if 'usuario_id' not in session or not verificar_rol(
        'jefe_primera_instancia', 'jefe_segunda_instancia', 'administrador'
    ):
        flash('Acceso solo para Jefes de Instancia.', 'danger')
        return redirect(url_for('inicio_sesion'))

    rol = session.get('rol')
    if rol == 'jefe_segunda_instancia':
        instancia = 2
    elif rol == 'jefe_primera_instancia':
        instancia = 1
    else:
        instancia = int(request.args.get('instancia', 1))

    perfil_datos = obtener_perfil_completo(session['usuario_id'], rol)
    zona_id_jefe = perfil_datos['zona_id'] if perfil_datos else None
    
    zona_para_filtro = zona_id_jefe if rol != 'administrador' else None

    stats     = obtener_estadisticas_jefe(instancia, zona_para_filtro)
    reclamos  = obtener_reclamos_jefe(instancia, zona_para_filtro)
    tecnicos  = obtener_tecnicos_jefe(instancia)
    trabajos  = obtener_trabajos_reparados(instancia=instancia, limit=15)

    return render_template(
        'dashboard_jefe.html',
        instancia=instancia,
        stats=stats, reclamos=reclamos, tecnicos=tecnicos, trabajos_reparados=trabajos,
        perfil=perfil_datos,
        nombre_usuario=session.get('nombre', ''), now=datetime.now()
    )

@app.route('/api/jefe/asignar_tecnico', methods=['POST'])
def api_jefe_asignar_tecnico():
    if 'usuario_id' not in session or not verificar_rol(
        'jefe_primera_instancia', 'jefe_segunda_instancia', 'administrador'
    ):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    rol = session.get('rol')
    instancia = 2 if rol == 'jefe_segunda_instancia' else 1
 
    conn = cur = None
    try:
        data       = request.get_json()
        reclamo_id = data.get('reclamo_id')
        tecnico_id = data.get('tecnico_id')
        if not reclamo_id or not tecnico_id:
            return jsonify({'success': False, 'message': 'reclamo_id y tecnico_id son requeridos'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        
        cur.execute("SELECT medio_tecnico, instancia_tecnico FROM tecnicos WHERE id = %s", (tecnico_id,))
        trow = cur.fetchone()
        if not trow or trow[1] != instancia:
            return jsonify({'success': False, 'message': 'El técnico no pertenece a esta instancia'}), 400
        medio_tec = trow[0]
 
        cur.execute("""
            SELECT titulo, descripcion, tipo_reclamo, prioridad, usuario_id
            FROM reclamos WHERE id = %s
        """, (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404
 
        if instancia == 1:
            cur.execute("""
                UPDATE reclamos
                SET asignado_a   = %s, estado = 'en_proceso', instancia = 1,
                    medio_fisico = COALESCE(%s, medio_fisico), fecha_asignacion = NOW()
                WHERE id = %s
            """, (tecnico_id, medio_tec, reclamo_id))
        else:
            cur.execute("""
                UPDATE reclamos
                SET asignado_a = %s, estado = 'en_proceso', fecha_asignacion = NOW()
                WHERE id = %s
            """, (tecnico_id, reclamo_id))
 
        cur.execute("SELECT id FROM ordenes_trabajo WHERE reclamo_id = %s ORDER BY id DESC LIMIT 1", (reclamo_id,))
        ot_existente = cur.fetchone()
 
        if ot_existente:
            ot_id = ot_existente[0]
            cur.execute("""
                UPDATE ordenes_trabajo SET tecnico_id = %s, estado = 'pendiente', fecha_actualizacion = NOW()
                WHERE id = %s
            """, (tecnico_id, ot_id))
            numero_ot = None
        else:
            cur.execute("SELECT NEXTVAL('seq_numero_ot')")
            seq = cur.fetchone()[0]
            numero_ot = f"OT-{seq:04d}"
            etiqueta = '1ra instancia' if instancia == 1 else '2da instancia'
            cur.execute("""
                INSERT INTO ordenes_trabajo (
                    numero_ot, titulo, descripcion, tipo_trabajo, prioridad, estado,
                    tecnico_id, usuario_cliente_id, creado_por, reclamo_id,
                    fecha_creacion, fecha_actualizacion
                ) VALUES (%s,%s,%s,%s,%s,'pendiente',%s,%s,%s,%s, NOW(), NOW())
                RETURNING id
            """, (
                numero_ot, f"[{etiqueta}] {reclamo[0]}", reclamo[1] or 'Sin descripción',
                reclamo[2], reclamo[3], tecnico_id, reclamo[4], session['usuario_id'], reclamo_id
            ))
            ot_id = cur.fetchone()[0]
 
        cur.execute("""
            INSERT INTO ot_actividades (ot_id, tecnico_id, descripcion, tipo)
            VALUES (%s, %s, %s, 'nota')
        """, (ot_id, tecnico_id, f"OT asignada por el Jefe de {'1ra' if instancia==1 else '2da'} Instancia."))
 
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'en_proceso', %s)
        """, (reclamo_id, f"Asignado a técnico por el Jefe de {'1ra' if instancia==1 else '2da'} Instancia."))
 
        conn.commit()
        return jsonify({'success': True, 'numero_ot': numero_ot, 'message': 'Reclamo asignado al técnico correctamente.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_jefe_asignar_tecnico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
@app.route('/api/jefe/tecnicos_disponibles')
def api_jefe_tecnicos_disponibles():
    """

    La instancia se deduce del rol en sesión .
    """
    if 'usuario_id' not in session or not verificar_rol(
        'jefe_primera_instancia', 'jefe_segunda_instancia', 'help_desk', 'administrador'
    ):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    rol = session.get('rol')
    if rol == 'jefe_segunda_instancia':
        instancia = 2
    elif rol == 'jefe_primera_instancia':
        instancia = 1
    else:
        instancia = int(request.args.get('instancia', 1))
 
    servicio = (request.args.get('servicio') or '').strip().lower()
    medio    = (request.args.get('medio') or '').strip().lower() or None
 
    if servicio not in ('telefonia', 'tv_cable', 'internet', 'transmisiones'):
        return jsonify({'success': False, 'message': 'servicio inválido'}), 400
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT t.id, u.nombre || ' ' || u.apellido, COUNT(r2.id) AS activos
            FROM tecnicos t
            JOIN usuarios u ON u.usuario_id = t.usuario_id
            LEFT JOIN reclamos r2 ON r2.asignado_a = t.id AND r2.estado = 'en_proceso'
            WHERE t.activo = TRUE AND t.instancia_tecnico = %s
              AND t.servicio_tecnico = %s
              AND (%s IS NULL OR t.medio_tecnico = %s)
            GROUP BY t.id, u.nombre, u.apellido
            ORDER BY activos ASC
        """, (instancia, servicio, medio, medio))
        filas = cur.fetchall()
        return jsonify({
            'success': True,
            'codigo_ivr': obtener_codigo_ivr(servicio, medio) if medio else None,
            'tecnicos': [{'id': f[0], 'nombre_completo': f[1], 'reclamos_activos': f[2]} for f in filas]
        })
    except Exception as e:
        print(f"ERROR api_jefe_tecnicos_disponibles: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 



# ═══════════════════════════════════════════════════════════════
 
@app.route('/dashboard_tecnico')
def dashboard_tecnico():
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        flash('Acceso solo para técnicos.', 'danger')
        return redirect(url_for('inicio_sesion'))
 
    crear_tablas_tecnico_si_no_existen()
    asegurar_registro_tecnico(session['usuario_id'])
 
    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        flash('No se encontró tu perfil de técnico. Contacta al administrador.', 'danger')
        return redirect(url_for('inicio_sesion'))
 
    tecnico_id = tecnico[0]
    stats      = obtener_estadisticas_tecnico(tecnico_id)
    ots        = obtener_ots_tecnico(tecnico_id, estado='todas', limit=20)
 
    conn_z = cur_z = None
    mi_zona_nombre = None
    try:
        conn_z = get_db_connection()
        cur_z  = conn_z.cursor()
        cur_z.execute("""
            SELECT z.nombre FROM tecnicos t
            LEFT JOIN zonas z ON t.zona_id = z.id
            WHERE t.id = %s
        """, (tecnico_id,))
        row_z = cur_z.fetchone()
        mi_zona_nombre = row_z[0] if row_z else None
    finally:
        if cur_z:  cur_z.close()
        if conn_z: conn_z.close()
 
    return render_template(
        'dashboard_tecnico.html',
        tecnico=tecnico, stats=stats, ots=ots, mi_zona_nombre=mi_zona_nombre,
        nombre_usuario=session.get('nombre', ''), now=datetime.now(),
    )
 
 

@app.route('/tecnico/ots')
def tecnico_ots():
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        flash('Acceso solo para técnicos.', 'danger')
        return redirect(url_for('inicio_sesion'))
 
    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return redirect(url_for('inicio_sesion'))
 
    estado_filtro = request.args.get('estado', 'todas')
    ots = obtener_ots_tecnico(tecnico[0], estado=estado_filtro, limit=100)
 
    return render_template(
        'dashboard_tecnico.html',
        ots=ots, tecnico=tecnico, stats=obtener_estadisticas_tecnico(tecnico[0]),
        nombre_usuario=session.get('nombre', ''), now=datetime.now(),
    )


@app.route('/api/tecnico/registrar_informe', methods=['POST'])
def api_tecnico_registrar_informe():
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return jsonify({'success': False, 'message': 'Perfil técnico no encontrado'}), 403
 
    conn = cur = None
    try:
        data          = request.get_json()
        ot_id         = data.get('ot_id')
        tipo_informe  = int(data.get('tipo_informe') or 0)
        detalle       = (data.get('detalle') or '').strip()
 
        if tipo_informe not in (1, 2):
            return jsonify({'success': False, 'message': 'Tipo de informe inválido'}), 400
        if not detalle:
            return jsonify({'success': False, 'message': 'El detalle del informe es obligatorio'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, fecha_1er_informe, fecha_2do_informe
            FROM ordenes_trabajo WHERE id = %s AND tecnico_id = %s
        """, (ot_id, tecnico[0]))
        ot = cur.fetchone()
        if not ot:
            return jsonify({'success': False, 'message': 'OT no encontrada'}), 404
 
        if tipo_informe == 1:
            if ot[1]:
                return jsonify({'success': False, 'message': 'El 1er informe ya fue registrado.'}), 400
            cur.execute("UPDATE ordenes_trabajo SET fecha_1er_informe = NOW(), informe_1_detalle = %s WHERE id = %s", (detalle, ot_id))
        else:
            if not ot[1]:
                return jsonify({'success': False, 'message': 'Debes registrar el 1er informe primero.'}), 400
            if ot[2]:
                return jsonify({'success': False, 'message': 'El 2do informe ya fue registrado.'}), 400
            cur.execute("UPDATE ordenes_trabajo SET fecha_2do_informe = NOW(), informe_2_detalle = %s WHERE id = %s", (detalle, ot_id))
 
        cur.execute("""
            INSERT INTO ot_actividades (ot_id, tecnico_id, descripcion, tipo)
            VALUES (%s, %s, %s, 'informe')
        """, (ot_id, tecnico[0], f"{'1er' if tipo_informe == 1 else '2do'} informe registrado: {detalle}"))
 
        conn.commit()
        return jsonify({'success': True, 'message': f'{"1er" if tipo_informe == 1 else "2do"} informe registrado correctamente.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_tecnico_registrar_informe: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
@app.route('/tecnico/ot/<int:ot_id>')
def tecnico_ver_ot(ot_id):
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        flash('Acceso solo para técnicos.', 'danger')
        return redirect(url_for('inicio_sesion'))

    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return redirect(url_for('inicio_sesion'))

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                ot.id, ot.numero_ot, ot.titulo, ot.descripcion,
                ot.tipo_trabajo, ot.prioridad, ot.estado,
                ot.direccion, ot.coordenadas,
                ot.fecha_programada, ot.fecha_inicio, ot.fecha_fin,
                ot.observaciones, ot.fecha_creacion,
                u.nombre, u.apellido, u.telefono, u.correo,
                uc.nombre AS creado_nombre, uc.apellido AS creado_apellido
            FROM ordenes_trabajo ot
            LEFT JOIN usuarios u  ON ot.usuario_cliente_id = u.usuario_id
            LEFT JOIN usuarios uc ON ot.creado_por = uc.usuario_id
            WHERE ot.id = %s AND ot.tecnico_id = %s
        """, (ot_id, tecnico[0]))
        ot = cur.fetchone()
    except Exception as e:
        print(f"ERROR tecnico_ver_ot: {e}")
        ot = None
    finally:
        if cur:  cur.close()
        if conn: conn.close()

    if not ot:
        flash('Orden de trabajo no encontrada.', 'danger')
        return redirect(url_for('tecnico_ots'))

    actividades = obtener_actividades_ot(ot_id)

    return render_template(
        'tecnico_detalle_ots.html',        # ← detalle de una OT
        ot=ot,
        actividades=actividades,
        nombre_usuario=session.get('nombre', ''),
        now=datetime.now(),
    )
 
 
 
@app.route('/api/tecnico/cambiar_estado_ot', methods=['POST'])
def api_tecnico_cambiar_estado_ot():
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return jsonify({'success': False, 'message': 'Perfil técnico no encontrado'}), 403
 
    conn = cur = None
    try:
        data         = request.get_json()
        ot_id        = data.get('ot_id')
        nuevo_estado = data.get('estado')
        observacion  = (data.get('observacion') or '').strip()
        codigo_solucion_id = data.get('codigo_solucion_id') or None
 
        ESTADOS_VALIDOS = ('en_proceso', 'completado', 'pendiente')
        if nuevo_estado not in ESTADOS_VALIDOS:
            return jsonify({'success': False, 'message': 'Estado no válido'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT id, estado, reclamo_id FROM ordenes_trabajo
            WHERE id = %s AND tecnico_id = %s
        """, (ot_id, tecnico[0]))
        ot = cur.fetchone()
        if not ot:
            return jsonify({'success': False, 'message': 'OT no encontrada'}), 404
 
        if nuevo_estado == 'en_proceso' and ot[1] == 'pendiente':
            cur.execute("""
                UPDATE ordenes_trabajo
                SET estado = %s, fecha_inicio = NOW(), fecha_actualizacion = NOW()
                WHERE id = %s
            """, (nuevo_estado, ot_id))
        elif nuevo_estado == 'completado':
                cur.execute("""
                    UPDATE ordenes_trabajo
                    SET estado = %s, fecha_fin = NOW(), fecha_actualizacion = NOW(),
                        codigo_solucion_id = %s
                    WHERE id = %s
                """, (nuevo_estado, codigo_solucion_id, ot_id))
        else:
            cur.execute("""
                UPDATE ordenes_trabajo
                SET estado = %s, fecha_actualizacion = NOW()
                WHERE id = %s
            """, (nuevo_estado, ot_id))
 
        tipo_actividad = {'en_proceso':'inicio','completado':'completado','pendiente':'nota'}.get(nuevo_estado,'nota')
        desc_auto = {
            'en_proceso': 'El técnico inició el trabajo.',
            'completado': 'El técnico marcó la OT como completada. Falla liberada automáticamente vía IVR (*108).',
            'pendiente':  'El técnico pausó el trabajo.',
        }.get(nuevo_estado, 'Cambio de estado.')
        descripcion_final = f"{desc_auto} {observacion}".strip() if observacion else desc_auto
 
        cur.execute("""
            INSERT INTO ot_actividades (ot_id, tecnico_id, descripcion, tipo)
            VALUES (%s, %s, %s, %s)
        """, (ot_id, tecnico[0], descripcion_final, tipo_actividad))
 
        # ── Al completar: liberar por IVR automáticamente ──────────────
        if nuevo_estado == 'completado' and ot[2]:
             reclamo_id = ot[2]
             cur.execute("""
                 SELECT EXTRACT(EPOCH FROM (NOW() - fecha_creacion))/60,
                        servicio_afectado, medio_fisico, instancia
                 FROM reclamos WHERE id = %s
             """, (reclamo_id,))
             row_t = cur.fetchone()
             tiempo_total  = int(row_t[0]) if row_t and row_t[0] else 0
             servicio_norm = normalizar_servicio(row_t[1] if row_t else '')
             medio_reclamo = (row_t[2] if row_t else None) or 'fibra_optica'
             instancia_r   = (row_t[3] if row_t else None) or 1
             codigo_ivr    = obtener_codigo_ivr(servicio_norm, medio_reclamo)

             cur.execute("""
                 UPDATE reclamos
                 SET estado                = 'liberado',
                     liberado_ivr          = TRUE,
                     fecha_liberacion_ivr  = NOW(),
                     fecha_resolucion      = NOW(),
                     tiempo_resolucion_min = %s,
                     codigo_ivr_usado      = %s
                 WHERE id = %s
                   AND estado NOT IN ('cerrado', 'auditado')
             """, (tiempo_total, codigo_ivr, reclamo_id))

             cur.execute("""
                 INSERT INTO reclamos_seguimiento
                     (reclamo_id, empleado_id, accion, descripcion)
                 VALUES (%s, NULL, 'liberado', %s)
             """, (reclamo_id, f'Reclamo liberado automáticamente vía IVR ({codigo_ivr}) al completar la OT.'))

    
             cur.execute("""
                 INSERT INTO trabajos_reparados
                     (ot_id, reclamo_id, tecnico_id, numero_ot, servicio, medio,
                      instancia, codigo_ivr, fecha_inicio, fecha_fin, duracion_min)
                 SELECT %s, %s, %s, ot.numero_ot, %s, %s, %s, %s,
                        ot.fecha_inicio, NOW(), %s
                 FROM ordenes_trabajo ot WHERE ot.id = %s
             """, (ot_id, reclamo_id, tecnico[0], servicio_norm, medio_reclamo,
                   instancia_r, codigo_ivr, tiempo_total, ot_id))
 
        conn.commit()
 
       
        if nuevo_estado == 'completado' and ot[2]:
            mensaje_fin = (
                f'El técnico {session.get("nombre","")} finalizó y liberó el reclamo #{reclamo_id} '
                f'vía IVR ({codigo_ivr}).'
            )
            notificar_jefes_instancia(
                instancia_r, reclamo_id, mensaje_fin,
                asunto=f'COTEL RL — Reclamo #{reclamo_id} finalizado por el técnico'
            )
            notificar_jefes_especialidad(
                instancia_r, reclamo_id, mensaje_fin,
                asunto=f'COTEL RL — Reclamo #{reclamo_id} finalizado por el técnico'
            )
 
 
        labels = {'en_proceso':'En Proceso','completado':'Completado','pendiente':'Pendiente'}
        return jsonify({
            'success':      True,
            'message':      f'OT actualizada a "{labels.get(nuevo_estado)}".',
            'nuevo_estado': nuevo_estado,
            'fecha':        datetime.now().strftime('%d/%m/%Y %H:%M'),
        })
 
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_tecnico_cambiar_estado_ot: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
 
@app.route('/api/tecnico/agregar_nota_ot', methods=['POST'])
def api_tecnico_agregar_nota_ot():
    """El técnico agrega una nota/avance a su OT."""
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return jsonify({'success': False, 'message': 'Perfil no encontrado'}), 403
 
    conn = cur = None
    try:
        data        = request.get_json()
        ot_id       = data.get('ot_id')
        descripcion = (data.get('descripcion') or '').strip()
        tipo        = data.get('tipo', 'nota')
 
        if not descripcion:
            return jsonify({'success': False, 'message': 'La descripción es obligatoria'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        # Verificar pertenencia
        cur.execute("SELECT id FROM ordenes_trabajo WHERE id = %s AND tecnico_id = %s",
                    (ot_id, tecnico[0]))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'OT no encontrada'}), 404
 
        cur.execute("""
            INSERT INTO ot_actividades (ot_id, tecnico_id, descripcion, tipo)
            VALUES (%s, %s, %s, %s)
            RETURNING id, fecha
        """, (ot_id, tecnico[0], descripcion, tipo))
        row = cur.fetchone()
        conn.commit()
 
        return jsonify({
            'success':     True,
            'message':     'Nota agregada correctamente.',
            'actividad_id': row[0],
            'fecha':        row[1].strftime('%d/%m/%Y %H:%M') if row[1] else '',
        })
 
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/api/tecnico/mis_ots_json')
def api_tecnico_mis_ots_json():
    """Endpoint JSON para recargar la lista de OT sin recargar la página."""
    if 'usuario_id' not in session or session.get('rol') != 'tecnico':
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    tecnico = obtener_tecnico_por_usuario(session['usuario_id'])
    if not tecnico:
        return jsonify({'success': False, 'message': 'Perfil no encontrado'}), 403
 
    estado = request.args.get('estado', 'todas')
    ots    = obtener_ots_tecnico(tecnico[0], estado=estado, limit=100)
 
    return jsonify({
        'success': True,
        'ots': [
            {
                'id':               ot[0],
                'numero_ot':        ot[1],
                'titulo':           ot[2],
                'descripcion':      ot[3],
                'tipo_trabajo':     ot[4],
                'prioridad':        ot[5],
                'estado':           ot[6],
                'direccion':        ot[7],
                'fecha_programada': ot[8].strftime('%d/%m/%Y %H:%M') if ot[8] else None,
                'cliente_nombre':   f"{ot[13] or ''} {ot[14] or ''}".strip(),
                'cliente_telefono': ot[15],
            }
            for ot in ots
        ],
    })



# ============================================================
# API ENDPOINTS VARIOS
# ============================================================

@app.route('/api/obtener_servicios')
def obtener_servicios_api():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    servicios = obtener_servicios_usuario(session['usuario_id'])
    return jsonify({'success': True, 'servicios': [
        {'id': s[0], 'tipo': s[1], 'numero': s[2], 'plan': s[3], 'estado': s[4], 'monto': float(s[6]) if s[6] else 0}
        for s in servicios
    ]})


@app.route('/api/estadisticas_usuario')
def estadisticas_usuario():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        uid  = session['usuario_id']

        cur.execute("SELECT COUNT(*) FROM servicios WHERE usuario_id=%s AND estado='activo'", (uid,))
        servicios_activos = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM pagos
            WHERE usuario_id=%s
            AND EXTRACT(MONTH FROM fecha_pago)=EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR  FROM fecha_pago)=EXTRACT(YEAR  FROM CURRENT_DATE)
        """, (uid,))
        pagos_mes = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM tramites
            WHERE usuario_id=%s AND estado IN ('pendiente','en_proceso')
        """, (uid,))
        tramites_pendientes = cur.fetchone()[0]

        cur.execute("""
            SELECT COALESCE(SUM(monto),0) FROM pagos
            WHERE usuario_id=%s AND estado='completado'
            AND EXTRACT(YEAR FROM fecha_pago)=EXTRACT(YEAR FROM CURRENT_DATE)
        """, (uid,))
        gasto_anual = cur.fetchone()[0]

        return jsonify({'success': True, 'estadisticas': {
            'servicios_activos': servicios_activos,
            'pagos_mes': pagos_mes,
            'tramites_pendientes': tramites_pendientes,
            'gasto_anual': float(gasto_anual)
        }})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


SLA_MINUTOS_MAX = 1440   # 24 horas

SQL_FECHA_INICIO_ETAPA = """
    COALESCE(
        (SELECT MAX(rs.fecha_accion) FROM reclamos_seguimiento rs WHERE rs.reclamo_id = r.id),
        r.fecha_creacion
    )
"""
 
def _instancia_por_especialidad(especialidad):
    return 1 if especialidad == 'DRA' else 2
 
def _especialidad_de_sesion():
    rol = session.get('rol')
    return 'DRA' if rol == 'jefe_dra' else 'DRC'
 

# ============================================================
# HELPERS GENERALES DEL MÓDULO
# ============================================================

def obtener_codigos_falla(solo_activos=True):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        query = "SELECT id, codigo, nombre, descripcion, categoria FROM codigos_falla"
        if solo_activos:
            query += " WHERE activo = TRUE"
        query += " ORDER BY codigo"
        cur.execute(query)
        return cur.fetchall()
    except Exception as e:
        print(f"ERROR obtener_codigos_falla: {e}")
        return []
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def cambiar_estado_reclamo(reclamo_id, nuevo_estado, empleado_id=None, descripcion=None):
    """Cambia el estado de un reclamo y registra el seguimiento."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE reclamos SET estado = %s WHERE id = %s",
            (nuevo_estado, reclamo_id)
        )
        if descripcion:
            cur.execute("""
                INSERT INTO reclamos_seguimiento
                    (reclamo_id, empleado_id, accion, descripcion)
                VALUES (%s, %s, %s, %s)
            """, (reclamo_id, empleado_id, nuevo_estado, descripcion))
        conn.commit()
        return True
    except Exception as e:
        print(f"ERROR cambiar_estado_reclamo: {e}")
        if conn: conn.rollback()
        return False
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def obtener_empleado_id_por_usuario(usuario_id):
    """Devuelve el id de empleados_soporte para el usuario logueado."""
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id FROM empleados_soporte WHERE usuario_id = %s AND activo = TRUE",
            (usuario_id,)
        )
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"ERROR obtener_empleado_id_por_usuario: {e}")
        return None
    finally:
        if cur:  cur.close()
        if conn: conn.close()


def verificar_rol(*roles_permitidos):
    """Devuelve True si el usuario en sesión tiene uno de los roles dados."""
    rol_sesion = session.get('rol', '').strip().lower()
    return rol_sesion in [r.lower() for r in roles_permitidos]


# ============================================================
# API PÚBLICA — CATÁLOGO DE CÓDIGOS DE FALLA
# ============================================================

@app.route('/api/codigos_falla')
def api_codigos_falla():
    """Lista de códigos de falla para dropdowns (acceso con sesión)."""
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    filas = obtener_codigos_falla()
    return jsonify({
        'success': True,
        'codigos': [
            {'id': f[0], 'codigo': f[1], 'nombre': f[2],
             'descripcion': f[3], 'categoria': f[4]}
            for f in filas
        ]
    })


@app.route('/api/elementos_red')
def api_elementos_red():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id, codigo, nombre FROM elementos_red WHERE activo = TRUE ORDER BY codigo")
        filas = cur.fetchall()
        return jsonify({'success': True, 'elementos': [{'id': f[0], 'codigo': f[1], 'nombre': f[2]} for f in filas]})
    except Exception as e:
        print(f"ERROR api_elementos_red: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/api/codigos_solucion')
def api_codigos_solucion():
    if 'usuario_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT id, codigo, nombre, descripcion FROM codigos_solucion WHERE activo = TRUE ORDER BY id")
        filas = cur.fetchall()
        return jsonify({'success': True, 'soluciones': [
            {'id': f[0], 'codigo': f[1], 'nombre': f[2], 'descripcion': f[3]} for f in filas
        ]})
    except Exception as e:
        print(f"ERROR api_codigos_solucion: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 

# ============================================================
# DIAGNÓSTICO REMOTO (Help Desk / Soporte)
# ============================================================

@app.route('/api/soporte/iniciar_diagnostico/<int:reclamo_id>', methods=['POST'])
def api_iniciar_diagnostico(reclamo_id):
    """
    Help Desk inicia el diagnóstico remoto.
    Cambia el estado del reclamo a 'en_diagnostico'.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id, estado FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404

        ESTADOS_BLOQUEADOS = ('en_diagnostico', 'pendiente_asignacion', 'en_proceso',
                              'resuelto_remoto', 'resuelto', 'resuelto_tecnico',
                              'cerrado', 'auditado')
        if reclamo[1] in ESTADOS_BLOQUEADOS:
            return jsonify({
                'success': False,
                'message': f'El reclamo ya está en estado "{reclamo[1]}" y no puede diagnosticarse de nuevo. Ya fue enviado a instancia superior.'
            }), 400

        empleado_id = obtener_empleado_id_por_usuario(session['usuario_id'])

        # Crear registro de diagnóstico
        cur.execute("""
            INSERT INTO diagnosticos_remotos
                (reclamo_id, operador_id, fecha_inicio)
            VALUES (%s, %s, NOW())
            RETURNING id
        """, (reclamo_id, session['usuario_id']))
        diagnostico_id = cur.fetchone()[0]

        # Actualizar reclamo
        cur.execute("""
            UPDATE reclamos
            SET estado = 'en_diagnostico',
                fecha_diagnostico_inicio = NOW()
            WHERE id = %s
        """, (reclamo_id,))

        cur.execute("""
            INSERT INTO reclamos_seguimiento
                (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, %s, 'en_diagnostico', 'Help Desk inició diagnóstico remoto')
        """, (reclamo_id, empleado_id))

        conn.commit()
        return jsonify({
            'success': True,
            'diagnostico_id': diagnostico_id,
            'message': 'Diagnóstico remoto iniciado.'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_iniciar_diagnostico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/guardar_diagnostico', methods=['POST'])
def api_guardar_diagnostico():
    """
    Guarda los procedimientos marcados durante el diagnóstico remoto.
    El front envía checkboxes + observaciones en JSON.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        data           = request.get_json()
        diagnostico_id = data.get('diagnostico_id')
        reclamo_id     = data.get('reclamo_id')
        if not diagnostico_id or not reclamo_id:
            return jsonify({'success': False, 'message': 'diagnostico_id y reclamo_id son requeridos'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE diagnosticos_remotos SET
                reinicio_onu        = %s, validacion_potencia = %s, reconfiguracion  = %s,
                reinicio_puerto     = %s, sincronizacion      = %s, cambio_perfil    = %s,
                otros               = %s, descripcion_otros   = %s, observaciones    = %s,
                codigo_falla_id     = %s, elemento_afectado_id = %s
            WHERE id = %s AND reclamo_id = %s
        """, (
            data.get('reinicio_onu', False), data.get('validacion_potencia', False),
            data.get('reconfiguracion', False), data.get('reinicio_puerto', False),
            data.get('sincronizacion', False), data.get('cambio_perfil', False),
            data.get('otros', False), data.get('descripcion_otros', ''), data.get('observaciones', ''),
            data.get('codigo_falla_id') or None, data.get('elemento_afectado_id') or None,
            diagnostico_id, reclamo_id
        ))
 
        if data.get('codigo_falla_id'):
            cur.execute(
                "UPDATE reclamos SET codigo_falla_id = %s, elemento_afectado_id = %s WHERE id = %s",
                (data.get('codigo_falla_id'), data.get('elemento_afectado_id'), reclamo_id)
            )
 
        conn.commit()
        return jsonify({'success': True, 'message': 'Diagnóstico guardado.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_guardar_diagnostico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/finalizar_diagnostico', methods=['POST'])
def api_finalizar_diagnostico():
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        data            = request.get_json()
        diagnostico_id  = data.get('diagnostico_id')
        reclamo_id      = data.get('reclamo_id')
        resultado       = data.get('resultado')
        observaciones   = (data.get('observaciones') or '').strip()
        codigo_falla_id = data.get('codigo_falla_id')
 
        if resultado not in ('resuelto', 'no_interno', 'no_externo', 'masiva'):
            return jsonify({'success': False, 'message': 'Resultado no válido.'}), 400
        if not codigo_falla_id:
            return jsonify({'success': False, 'message': 'Selecciona el motivo de falla (código) antes de finalizar.'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        empleado_id = obtener_empleado_id_por_usuario(session['usuario_id'])
 
        cur.execute("""
            SELECT EXTRACT(EPOCH FROM (NOW() - fecha_inicio))/60
            FROM diagnosticos_remotos WHERE id = %s
        """, (diagnostico_id,))
        row = cur.fetchone()
        duracion_min = int(row[0]) if row and row[0] else 0
 
        solucionado = (resultado == 'resuelto')
 
        cur.execute("""
            UPDATE diagnosticos_remotos SET
                solucionado      = %s,
                fecha_fin        = NOW(),
                duracion_minutos = %s,
                codigo_falla_id  = %s,
                observaciones    = COALESCE(NULLIF(%s,''), observaciones)
            WHERE id = %s
        """, (solucionado, duracion_min, codigo_falla_id, observaciones, diagnostico_id))
 
        cur.execute("UPDATE reclamos SET codigo_falla_id = %s WHERE id = %s", (codigo_falla_id, reclamo_id))
 
        if resultado == 'resuelto':
            nuevo_estado = 'resuelto_remoto'
            desc_seg = f'Falla solucionada remotamente por Help Desk. Duración: {duracion_min} min.'
            cur.execute("""
                UPDATE reclamos SET
                    estado = 'resuelto_remoto', resuelto_remotamente = TRUE,
                    fecha_diagnostico_fin = NOW(), tiempo_diagnostico_min = %s,
                    fecha_resolucion = NOW()
                WHERE id = %s
            """, (duracion_min, reclamo_id))
 
        elif resultado == 'masiva':
            nuevo_estado = 'falla_masiva'
            desc_seg = 'No solucionado remotamente. Identificada como falla masiva.'
            cur.execute("""
                UPDATE reclamos SET estado = %s, fecha_diagnostico_fin = NOW(), tiempo_diagnostico_min = %s
                WHERE id = %s
            """, (nuevo_estado, duracion_min, reclamo_id))
 
        elif resultado == 'no_interno':
            nuevo_estado = 'pendiente_triage'
            desc_seg = f'No solucionado remotamente. Falla interna (red COTEL) — pendiente de triage por Jefe Help Desk. Duración diagnóstico: {duracion_min} min.'
            cur.execute("""
                UPDATE reclamos SET estado = %s, instancia = 1,
                    fecha_diagnostico_fin = NOW(), tiempo_diagnostico_min = %s
                WHERE id = %s
            """, (nuevo_estado, duracion_min, reclamo_id))
 
        else:  # no_externo
            nuevo_estado = 'pendiente_triage'
            cur.execute("SELECT servicio_afectado FROM reclamos WHERE id = %s", (reclamo_id,))
            srow = cur.fetchone()
            escalado_a = normalizar_servicio(srow[0] if srow else '')
            desc_seg = f'No solucionado remotamente. Falla externa (equipo/energía del cliente) — pendiente de triage por Jefe Help Desk. Duración diagnóstico: {duracion_min} min.'
            cur.execute("""
                UPDATE reclamos SET estado = %s, instancia = 1, escalado_a = %s,
                    fecha_diagnostico_fin = NOW(), tiempo_diagnostico_min = %s
                WHERE id = %s
            """, (nuevo_estado, escalado_a, duracion_min, reclamo_id)) 
        cur.execute("""
            INSERT INTO reclamos_seguimiento (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, %s, %s, %s)
        """, (reclamo_id, empleado_id, nuevo_estado, desc_seg))
 
        conn.commit()
     
 
        return jsonify({
            'success': True, 'nuevo_estado': nuevo_estado, 'resultado': resultado,
            'duracion_min': duracion_min, 'message': desc_seg
        })
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_finalizar_diagnostico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 


@app.route('/api/soporte/diagnostico/<int:reclamo_id>')
def api_obtener_diagnostico(reclamo_id):
    """Devuelve el diagnóstico activo de un reclamo (para rellenar el modal)."""
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT d.id, d.fecha_inicio, d.solucionado,
                   d.reinicio_onu, d.validacion_potencia, d.reconfiguracion,
                   d.reinicio_puerto, d.sincronizacion, d.cambio_perfil,
                   d.otros, d.descripcion_otros, d.observaciones,
                   d.codigo_falla_id, cf.codigo, cf.nombre,
                   d.duracion_minutos
            FROM diagnosticos_remotos d
            LEFT JOIN codigos_falla cf ON d.codigo_falla_id = cf.id
            WHERE d.reclamo_id = %s
            ORDER BY d.fecha_creacion DESC
            LIMIT 1
        """, (reclamo_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': True, 'diagnostico': None})
        return jsonify({
            'success': True,
            'diagnostico': {
                'id': row[0], 'fecha_inicio': str(row[1]),
                'solucionado': row[2],
                'reinicio_onu': row[3], 'validacion_potencia': row[4],
                'reconfiguracion': row[5], 'reinicio_puerto': row[6],
                'sincronizacion': row[7], 'cambio_perfil': row[8],
                'otros': row[9], 'descripcion_otros': row[10],
                'observaciones': row[11], 'codigo_falla_id': row[12],
                'codigo_falla': row[13], 'nombre_falla': row[14],
                'duracion_minutos': row[15]
            }
        })
    except Exception as e:
        print(f"ERROR api_obtener_diagnostico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


# ============================================================
# LIBERACIÓN IVR SIMULADA (*108)
# ============================================================

@app.route('/api/soporte/liberar_ivr/<int:reclamo_id>', methods=['POST'])
def api_liberar_ivr(reclamo_id):
    """
    Simula la liberación del reclamo vía IVR (*108).
    Cambia el estado de 'reparado' → 'liberado'.
    Puede llamarse desde soporte o desde el dashboard del técnico
    cuando completa la OT.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'tecnico'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id, estado FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404

        ESTADOS_VALIDOS_PARA_LIBERAR = ('reparado', 'resuelto_tecnico', 'en_reparacion')
        if reclamo[1] not in ESTADOS_VALIDOS_PARA_LIBERAR:
            return jsonify({
                'success': False,
                'message': f'El reclamo está en estado "{reclamo[1]}" y no puede liberarse por IVR aún.'
            }), 400

        empleado_id = obtener_empleado_id_por_usuario(session['usuario_id'])

        cur.execute("""
            UPDATE reclamos SET
                estado               = 'liberado',
                liberado_ivr         = TRUE,
                fecha_liberacion_ivr = NOW()
            WHERE id = %s
        """, (reclamo_id,))

        cur.execute("""
            INSERT INTO reclamos_seguimiento
                (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, %s, 'liberado',
                    'Reclamo liberado automáticamente vía IVR (*108). Pendiente confirmación Help Desk.')
        """, (reclamo_id, empleado_id))

        conn.commit()
        return jsonify({
            'success': True,
            'message': f'Reclamo #{reclamo_id} liberado vía IVR. Help Desk debe confirmar el cierre.',
            'nuevo_estado': 'liberado'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_liberar_ivr: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/confirmar_cierre/<int:reclamo_id>', methods=['POST'])
def api_confirmar_cierre(reclamo_id):
    """
    Help Desk confirma el cierre definitivo del reclamo
    después de verificar con el cliente.
    Estado: 'liberado' → 'cerrado'
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data        = request.get_json() or {}
        observacion = (data.get('observacion') or '').strip()
        reabrir     = data.get('reabrir', False)

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id, estado FROM reclamos WHERE id = %s", (reclamo_id,))
        reclamo = cur.fetchone()
        if not reclamo:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404

        empleado_id = obtener_empleado_id_por_usuario(session['usuario_id'])

        if reabrir:
            nuevo_estado = 'pendiente_asignacion'
            desc = f'Help Desk reabrió el reclamo. Motivo: {observacion}'
        else:
            nuevo_estado = 'cerrado'
            # Calcular tiempo total de resolución
            cur.execute("""
                SELECT EXTRACT(EPOCH FROM (NOW() - fecha_creacion))/60
                FROM reclamos WHERE id = %s
            """, (reclamo_id,))
            row = cur.fetchone()
            tiempo_total = int(row[0]) if row and row[0] else 0
            cur.execute(
                "UPDATE reclamos SET tiempo_resolucion_min = %s WHERE id = %s",
                (tiempo_total, reclamo_id)
            )
            desc = f'Help Desk confirmó cierre. {observacion}'

        cur.execute(
            "UPDATE reclamos SET estado = %s, fecha_resolucion = NOW() WHERE id = %s",
            (nuevo_estado, reclamo_id)
        )
        cur.execute("""
            INSERT INTO reclamos_seguimiento
                (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, %s, %s, %s)
        """, (reclamo_id, empleado_id, nuevo_estado, desc))

        conn.commit()
        return jsonify({
            'success': True,
            'nuevo_estado': nuevo_estado,
            'message': desc
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_confirmar_cierre: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


# ============================================================
# FALLAS MASIVAS
# ============================================================

def generar_codigo_falla_masiva():
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT NEXTVAL('seq_numero_fm')")
        n = cur.fetchone()[0]
        conn.commit()
        return f"FM-{datetime.now().year}-{n:03d}"
    except Exception as e:
        print(f"ERROR generar_codigo_fm: {e}")
        return f"FM-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/crear_falla_masiva', methods=['POST'])
def api_crear_falla_masiva():
    """Help Desk o Nodo Internet registra una nueva falla masiva."""
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'nodo_internet'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data = request.get_json()
        nombre          = (data.get('nombre') or '').strip()
        nodo            = (data.get('nodo') or '').strip()
        sector          = (data.get('sector') or '').strip()
        descripcion     = (data.get('descripcion') or '').strip()
        codigo_falla_id = data.get('codigo_falla_id') or None

        if not nombre:
            return jsonify({'success': False, 'message': 'El nombre de la falla es obligatorio'}), 400

        codigo_fm = generar_codigo_falla_masiva()

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("""
            INSERT INTO fallas_masivas
                (codigo, nombre, nodo, sector, descripcion,
                 codigo_falla_id, estado, creado_por, fecha_inicio)
            VALUES (%s, %s, %s, %s, %s, %s, 'activa', %s, NOW())
            RETURNING id
        """, (codigo_fm, nombre, nodo, sector, descripcion,
              codigo_falla_id, session['usuario_id']))
        fm_id = cur.fetchone()[0]

        # Si enviaron reclamos para asociar
        reclamos_ids = data.get('reclamos_ids', [])
        for rid in reclamos_ids:
            cur.execute("""
                INSERT INTO reclamos_fallas_masivas (reclamo_id, falla_masiva_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (rid, fm_id))
            cur.execute("""
                UPDATE reclamos SET estado = 'falla_masiva', falla_masiva_id = %s
                WHERE id = %s
            """, (fm_id, rid))

        # Actualizar contador de clientes afectados
        cur.execute("""
            UPDATE fallas_masivas SET clientes_afectados = %s WHERE id = %s
        """, (len(reclamos_ids), fm_id))

        conn.commit()
        return jsonify({
            'success': True,
            'falla_masiva_id': fm_id,
            'codigo': codigo_fm,
            'message': f'Falla masiva {codigo_fm} creada. {len(reclamos_ids)} reclamos asociados.'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_crear_falla_masiva: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/asociar_reclamo_falla_masiva', methods=['POST'])
def api_asociar_reclamo_falla_masiva():
    """Asocia un reclamo existente a una falla masiva."""
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'nodo_internet'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data            = request.get_json()
        reclamo_id      = data.get('reclamo_id')
        falla_masiva_id = data.get('falla_masiva_id')

        if not reclamo_id or not falla_masiva_id:
            return jsonify({'success': False, 'message': 'reclamo_id y falla_masiva_id son requeridos'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("""
            INSERT INTO reclamos_fallas_masivas (reclamo_id, falla_masiva_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (reclamo_id, falla_masiva_id))

        cur.execute("""
            UPDATE reclamos
            SET estado = 'falla_masiva', falla_masiva_id = %s
            WHERE id = %s
        """, (falla_masiva_id, reclamo_id))

        # Actualizar contador
        cur.execute("""
            UPDATE fallas_masivas SET
                clientes_afectados = (
                    SELECT COUNT(*) FROM reclamos_fallas_masivas
                    WHERE falla_masiva_id = %s
                )
            WHERE id = %s
        """, (falla_masiva_id, falla_masiva_id))

        conn.commit()
        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} asociado a la falla masiva.'})

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_asociar_reclamo_falla_masiva: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/nodo/actualizar_falla_masiva/<int:fm_id>', methods=['POST'])
def api_actualizar_falla_masiva(fm_id):
    """Nodo Internet actualiza el estado y datos de una falla masiva."""
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'nodo_internet'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data          = request.get_json()
        nuevo_estado  = data.get('estado')
        cuadrilla     = data.get('cuadrilla', '')
        observaciones = data.get('observaciones', '')
        fecha_estimada = data.get('fecha_estimada')

        ESTADOS_FM = ('activa', 'en_reparacion', 'resuelta')
        if nuevo_estado and nuevo_estado not in ESTADOS_FM:
            return jsonify({'success': False, 'message': 'Estado no válido'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()

        sets = ["responsable_id = %s"]
        vals = [session['usuario_id']]

        if nuevo_estado:
            sets.append("estado = %s"); vals.append(nuevo_estado)
        if cuadrilla:
            sets.append("cuadrilla = %s"); vals.append(cuadrilla)
        if observaciones:
            sets.append("observaciones = %s"); vals.append(observaciones)
        if fecha_estimada:
            sets.append("fecha_estimada = %s"); vals.append(fecha_estimada)
        if nuevo_estado == 'resuelta':
            sets.append("fecha_resolucion = NOW()")

        vals.append(fm_id)
        cur.execute(
            f"UPDATE fallas_masivas SET {', '.join(sets)} WHERE id = %s",
            vals
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Falla masiva actualizada.'})

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_actualizar_falla_masiva: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/nodo/resolver_falla_masiva/<int:fm_id>', methods=['POST'])
def api_resolver_falla_masiva(fm_id):
    """
    Nodo Internet marca la falla masiva como resuelta.
    Libera todos los reclamos asociados (simulación IVR).
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'nodo_internet'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data          = request.get_json() or {}
        observaciones = (data.get('observaciones') or '').strip()

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id, estado FROM fallas_masivas WHERE id = %s", (fm_id,))
        fm = cur.fetchone()
        if not fm:
            return jsonify({'success': False, 'message': 'Falla masiva no encontrada'}), 404
        if fm[1] == 'resuelta':
            return jsonify({'success': False, 'message': 'La falla masiva ya está resuelta'}), 400

        # Resolver falla masiva
        cur.execute("""
            UPDATE fallas_masivas SET
                estado           = 'resuelta',
                fecha_resolucion = NOW(),
                ivr_notificado   = TRUE,
                fecha_ivr        = NOW(),
                observaciones    = COALESCE(NULLIF(%s,''), observaciones)
            WHERE id = %s
        """, (observaciones, fm_id))

        # Liberar todos los reclamos asociados
        cur.execute("""
            SELECT reclamo_id FROM reclamos_fallas_masivas WHERE falla_masiva_id = %s
        """, (fm_id,))
        reclamos_asociados = [r[0] for r in cur.fetchall()]

        for rid in reclamos_asociados:
            cur.execute("""
                UPDATE reclamos SET
                    estado               = 'liberado',
                    liberado_ivr         = TRUE,
                    fecha_liberacion_ivr = NOW(),
                    fecha_resolucion     = NOW()
                WHERE id = %s
                  AND estado NOT IN ('cerrado', 'auditado')
            """, (rid,))
            cur.execute("""
                INSERT INTO reclamos_seguimiento
                    (reclamo_id, empleado_id, accion, descripcion)
                VALUES (%s, NULL, 'liberado',
                        'Liberado automáticamente al resolver falla masiva vía IVR (*108)')
            """, (rid,))

        conn.commit()
        return jsonify({
            'success': True,
            'reclamos_liberados': len(reclamos_asociados),
            'message': f'Falla masiva resuelta. {len(reclamos_asociados)} reclamos liberados vía IVR.'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_resolver_falla_masiva: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()

##JEFE NOTIFICACIONES DEESDE CORREOS Y MENSAJES 
@app.route('/api/jefe/notificaciones')
def api_jefe_notificaciones():
    if 'usuario_id' not in session or not verificar_rol('jefe_primera_instancia', 'jefe_segunda_instancia'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, reclamo_id, mensaje, leida, fecha_creacion
            FROM notificaciones_jefe
            WHERE usuario_id = %s
            ORDER BY fecha_creacion DESC
            LIMIT 30
        """, (session['usuario_id'],))
        filas = cur.fetchall()
        return jsonify({
            'success': True,
            'no_leidas': sum(1 for f in filas if not f[3]),
            'notificaciones': [
                {'id': f[0], 'reclamo_id': f[1], 'mensaje': f[2], 'leida': f[3],
                 'fecha': f[4].strftime('%d/%m/%Y %H:%M') if f[4] else None}
                for f in filas
            ]
        })
    except Exception as e:
        print(f"ERROR api_jefe_notificaciones: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/jefe/notificaciones/marcar_leida/<int:notif_id>', methods=['POST'])
def api_jefe_marcar_leida(notif_id):
    if 'usuario_id' not in session or not verificar_rol('jefe_primera_instancia', 'jefe_segunda_instancia'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE notificaciones_jefe SET leida = TRUE
            WHERE id = %s AND usuario_id = %s
        """, (notif_id, session['usuario_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()




@app.route('/api/fallas_masivas')
def api_listar_fallas_masivas():
    """Lista fallas masivas con sus métricas."""
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'nodo_internet', 'calidad'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        estado_filtro = request.args.get('estado', 'todas')
        conn = get_db_connection()
        cur  = conn.cursor()

        where = "" if estado_filtro == 'todas' else "WHERE fm.estado = %s"
        params = [] if estado_filtro == 'todas' else [estado_filtro]

        cur.execute(f"""
            SELECT
                fm.id, fm.codigo, fm.nombre, fm.nodo, fm.sector,
                fm.estado, fm.clientes_afectados,
                fm.fecha_inicio, fm.fecha_resolucion,
                fm.cuadrilla, fm.ivr_notificado,
                cf.codigo AS cod_falla, cf.nombre AS nom_falla,
                u.nombre || ' ' || u.apellido AS responsable,
                ROUND(EXTRACT(EPOCH FROM (
                    COALESCE(fm.fecha_resolucion, NOW()) - fm.fecha_inicio
                ))/60) AS duracion_min
            FROM fallas_masivas fm
            LEFT JOIN codigos_falla cf ON fm.codigo_falla_id = cf.id
            LEFT JOIN usuarios u       ON fm.responsable_id = u.usuario_id
            {where}
            ORDER BY fm.fecha_inicio DESC
            LIMIT 50
        """, params)

        filas = cur.fetchall()
        return jsonify({
            'success': True,
            'fallas': [
                {
                    'id': f[0], 'codigo': f[1], 'nombre': f[2],
                    'nodo': f[3], 'sector': f[4], 'estado': f[5],
                    'clientes_afectados': f[6],
                    'fecha_inicio': str(f[7]) if f[7] else None,
                    'fecha_resolucion': str(f[8]) if f[8] else None,
                    'cuadrilla': f[9], 'ivr_notificado': f[10],
                    'codigo_falla': f[11], 'nombre_falla': f[12],
                    'responsable': f[13], 'duracion_min': int(f[14]) if f[14] else 0
                }
                for f in filas
            ]
        })

    except Exception as e:
        print(f"ERROR api_listar_fallas_masivas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


# ============================================================
# DASHBOARD NODO INTERNET
# ============================================================

@app.route('/dashboard_nodo_internet')
def dashboard_nodo_internet():
    if 'usuario_id' not in session or not verificar_rol('nodo_internet', 'help_desk'):
        flash('Acceso solo para Nodo Internet.', 'danger')
        return redirect(url_for('inicio_sesion'))

    conn = cur = None
    stats = {}
    fallas_activas = fallas_en_reparacion = fallas_resueltas = []

    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        # Estadísticas generales
        cur.execute("""
            SELECT
                COUNT(*)                                               AS total,
                COUNT(CASE WHEN estado = 'activa'        THEN 1 END)  AS activas,
                COUNT(CASE WHEN estado = 'en_reparacion' THEN 1 END)  AS en_reparacion,
                COUNT(CASE WHEN estado = 'resuelta'      THEN 1 END)  AS resueltas,
                COALESCE(SUM(clientes_afectados), 0)                  AS total_clientes
            FROM fallas_masivas
        """)
        row = cur.fetchone()
        stats = {
            'total': row[0], 'activas': row[1],
            'en_reparacion': row[2], 'resueltas': row[3],
            'total_clientes': row[4]
        }

        # Fallas activas
        cur.execute("""
            SELECT fm.id, fm.codigo, fm.nombre, fm.nodo, fm.sector,
                   fm.clientes_afectados, fm.fecha_inicio, fm.cuadrilla,
                   cf.codigo AS cod_falla
            FROM fallas_masivas fm
            LEFT JOIN codigos_falla cf ON fm.codigo_falla_id = cf.id
            WHERE fm.estado = 'activa'
            ORDER BY fm.fecha_inicio DESC
        """)
        fallas_activas = cur.fetchall()

        # En reparación
        cur.execute("""
            SELECT fm.id, fm.codigo, fm.nombre, fm.nodo, fm.sector,
                   fm.clientes_afectados, fm.fecha_inicio, fm.cuadrilla,
                   fm.fecha_estimada,
                   ROUND(EXTRACT(EPOCH FROM (NOW()-fm.fecha_inicio))/60) AS duracion_min
            FROM fallas_masivas fm
            WHERE fm.estado = 'en_reparacion'
            ORDER BY fm.fecha_inicio ASC
        """)
        fallas_en_reparacion = cur.fetchall()

        # Resueltas últimas 24h
        cur.execute("""
            SELECT fm.id, fm.codigo, fm.nombre, fm.nodo,
                   fm.clientes_afectados, fm.fecha_inicio, fm.fecha_resolucion,
                   ROUND(EXTRACT(EPOCH FROM (fm.fecha_resolucion-fm.fecha_inicio))/60) AS duracion_min
            FROM fallas_masivas fm
            WHERE fm.estado = 'resuelta'
              AND fm.fecha_resolucion >= NOW() - INTERVAL '24 hours'
            ORDER BY fm.fecha_resolucion DESC
        """)
        fallas_resueltas = cur.fetchall()

        # Reclamos pendientes de asociar (estado falla_masiva sin fm asignada)
        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE estado IN ('pendiente_asignacion', 'nuevo', 'en_diagnostico', 'falla_masiva')
              AND falla_masiva_id IS NULL
        """)
        reclamos_sin_asignar = cur.fetchone()[0]
        stats['reclamos_sin_asignar'] = reclamos_sin_asignar

    except Exception as e:
        print(f"ERROR dashboard_nodo_internet: {e}")
        flash('Error al cargar el dashboard.', 'danger')
    finally:
        if cur:  cur.close()
        if conn: conn.close()

    return render_template(
        'dashboard_nodo_internet.html',
        stats=stats,
        fallas_activas=fallas_activas,
        fallas_en_reparacion=fallas_en_reparacion,
        fallas_resueltas=fallas_resueltas,
        nombre_usuario=session.get('nombre', ''),
        now=datetime.now()
    )


# ============================================================
# TURNO PLANTA INTERNA (reclamos nocturnos / fin de
# semana / feriados).
# ============================================================

@app.route('/dashboard_planta_interna')
def dashboard_planta_interna():
    if 'usuario_id' not in session or not verificar_rol('turno_planta_interna', 'administrador'):
        flash('Acceso solo para el turno de Planta Interna.', 'danger')
        return redirect(url_for('inicio_sesion'))

    conn = cur = None
    stats = {'pendientes': 0, 'resueltos_turno': 0, 'escalados_turno': 0}
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE es_turno_nocturno = TRUE AND estado = 'abierto' AND escalado_a IS NULL
        """)
        stats['pendientes'] = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE es_turno_nocturno = TRUE AND estado = 'resuelto'
              AND fecha_resolucion >= NOW() - INTERVAL '12 hours'
        """)
        stats['resueltos_turno'] = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE es_turno_nocturno = TRUE AND escalado_a = 'help_desk'
              AND fecha_escalacion >= NOW() - INTERVAL '12 hours'
        """)
        stats['escalados_turno'] = cur.fetchone()[0]
    except Exception as e:
        print(f"ERROR dashboard_planta_interna: {e}")
    finally:
        if cur:  cur.close()
        if conn: conn.close()

    return render_template('dashboard_planta_interna.html',
                            stats=stats, nombre_usuario=session.get('nombre', ''))


def _fila_reclamo_planta_interna(f):
    """Convierte una fila de reclamos (columnas fijas, ver SELECTs de abajo) a dict para el frontend."""
    return {
        'id': f[0], 'titulo': f[1], 'descripcion': f[2],
        'cliente_nombre': f"{f[3]} {f[4]}".strip(), 'numero_cliente': f[5],
        'prioridad': f[6], 'estado': f[7],
        'fecha_creacion': f[8].isoformat() if f[8] else None,
        'ubicacion_cliente': f[9], 'telefono_referencia': f[10],
    }


@app.route('/api/planta_interna/reclamos')
def api_planta_interna_reclamos():
    if 'usuario_id' not in session or not verificar_rol('turno_planta_interna', 'administrador'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        campos = """
            r.id, r.titulo, r.descripcion, u.nombre, u.apellido, r.numero_cliente,
            r.prioridad, r.estado, r.fecha_creacion, r.ubicacion_cliente, r.telefono_referencia
        """

        cur.execute(f"""
            SELECT {campos}
            FROM reclamos r JOIN usuarios u ON r.usuario_id = u.usuario_id
            WHERE r.es_turno_nocturno = TRUE AND r.estado = 'abierto' AND r.escalado_a IS NULL
            ORDER BY CASE r.prioridad WHEN 'alta' THEN 1 WHEN 'media' THEN 2 ELSE 3 END,
                     r.fecha_creacion ASC
        """)
        pendientes = [_fila_reclamo_planta_interna(f) for f in cur.fetchall()]

        cur.execute(f"""
            SELECT {campos}
            FROM reclamos r JOIN usuarios u ON r.usuario_id = u.usuario_id
            WHERE r.es_turno_nocturno = TRUE AND r.estado = 'resuelto'
              AND r.fecha_resolucion >= NOW() - INTERVAL '24 hours'
            ORDER BY r.fecha_resolucion DESC
        """)
        resueltos = [_fila_reclamo_planta_interna(f) for f in cur.fetchall()]

        cur.execute(f"""
            SELECT {campos}
            FROM reclamos r JOIN usuarios u ON r.usuario_id = u.usuario_id
            WHERE r.es_turno_nocturno = TRUE AND r.escalado_a = 'help_desk'
              AND r.fecha_escalacion >= NOW() - INTERVAL '24 hours'
            ORDER BY r.fecha_escalacion DESC
        """)
        escalados = [_fila_reclamo_planta_interna(f) for f in cur.fetchall()]

        return jsonify({'success': True, 'pendientes': pendientes,
                         'resueltos': resueltos, 'escalados': escalados})
    except Exception as e:
        print(f"ERROR api_planta_interna_reclamos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/planta_interna/resolver/<int:reclamo_id>', methods=['POST'])
def api_planta_interna_resolver(reclamo_id):
    if 'usuario_id' not in session or not verificar_rol('turno_planta_interna', 'administrador'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    data = request.get_json(silent=True) or {}
    solucion = (data.get('solucion') or '').strip()
    if not solucion:
        return jsonify({'success': False, 'message': 'Describe cómo se solucionó.'}), 400

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE reclamos
            SET estado = 'resuelto', solucion = %s, fecha_resolucion = NOW()
            WHERE id = %s AND es_turno_nocturno = TRUE AND estado = 'abierto' AND escalado_a IS NULL
            RETURNING id
        """, (solucion, reclamo_id))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False,
                             'message': 'El reclamo no existe o ya no está pendiente en este turno.'}), 404

        registrar_seguimiento_reclamo(reclamo_id, obtener_empleado_soporte_id(session['usuario_id']), 'resuelto',
                                       f'Resuelto por Turno Planta Interna: {solucion}')
        conn.commit()
        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} resuelto.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_planta_interna_resolver: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/planta_interna/enviar_helpdesk/<int:reclamo_id>', methods=['POST'])
def api_planta_interna_enviar_helpdesk(reclamo_id):
    if 'usuario_id' not in session or not verificar_rol('turno_planta_interna', 'administrador'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    data = request.get_json(silent=True) or {}
    motivo = (data.get('motivo') or '').strip()
    if not motivo:
        return jsonify({'success': False, 'message': 'Indica el motivo del envío a Help Desk.'}), 400

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
      
        cur.execute("""
            UPDATE reclamos
            SET escalado_a = 'help_desk', fecha_escalacion = NOW(), nota_tecnico = %s
            WHERE id = %s AND es_turno_nocturno = TRUE AND estado = 'abierto' AND escalado_a IS NULL
            RETURNING id
        """, (motivo, reclamo_id))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False,
                             'message': 'El reclamo no existe o ya no está pendiente en este turno.'}), 404

        registrar_seguimiento_reclamo(reclamo_id, obtener_empleado_soporte_id(session['usuario_id']), 'enviado_helpdesk',
                                       f'Enviado a Help Desk desde Planta Interna: {motivo}')
        conn.commit()
        return jsonify({'success': True, 'message': f'Reclamo #{reclamo_id} enviado a Help Desk.'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_planta_interna_enviar_helpdesk: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


# ============================================================
#  GESTIÓN DE CALIDAD
# ============================================================

@app.route('/dashboard_calidad')
def dashboard_calidad():
    if 'usuario_id' not in session or not verificar_rol('calidad', 'help_desk'):
        flash('Acceso solo para Gestión de Calidad.', 'danger')
        return redirect(url_for('inicio_sesion'))

    conn = cur = None
    stats = {}
    reclamos_pendientes_auditoria = []
    auditorias_recientes = []

    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        # Reclamos cerrados en últimas 24h SIN auditar
        cur.execute("""
            SELECT
                r.id, u.nombre, u.apellido,
                r.tipo_reclamo, r.titulo, r.estado,
                r.fecha_creacion, r.fecha_resolucion,
                r.tiempo_resolucion_min,
                cf.codigo AS cod_falla, cf.nombre AS nom_falla,
                r.resuelto_remotamente, r.falla_masiva_id,
                CASE
                    WHEN r.tiempo_resolucion_min IS NOT NULL
                         AND r.tiempo_resolucion_min <= %s THEN TRUE
                    ELSE FALSE
                END AS dentro_sla,
                ut.nombre || ' ' || COALESCE(ut.apellido,'') AS tecnico_nombre
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN codigos_falla cf ON r.codigo_falla_id = cf.id
            LEFT JOIN ordenes_trabajo ot ON ot.reclamo_id = r.id
            LEFT JOIN tecnicos t         ON ot.tecnico_id  = t.id
            LEFT JOIN usuarios ut        ON t.usuario_id   = ut.usuario_id
            WHERE r.estado IN ('cerrado', 'liberado')
              AND r.fecha_resolucion >= NOW() - INTERVAL '24 hours'
              AND r.id NOT IN (SELECT reclamo_id FROM auditorias_calidad)
            ORDER BY r.fecha_resolucion DESC
        """, (SLA_MINUTOS_MAX,))
        reclamos_pendientes_auditoria = cur.fetchall()

        
        cur.execute("""
            SELECT
                COUNT(*)                                                     AS total_auditados,
                COUNT(CASE WHEN resultado = 'conforme'       THEN 1 END)     AS conformes,
                COUNT(CASE WHEN resultado = 'reincidencia'   THEN 1 END)     AS reincidencias,
                COUNT(CASE WHEN resultado = 'mala_atencion'  THEN 1 END)     AS mala_atencion,
                COUNT(CASE WHEN resultado = 'fuera_tiempo'   THEN 1 END)     AS fuera_tiempo,
                COUNT(CASE WHEN dentro_sla = TRUE            THEN 1 END)     AS dentro_sla,
                ROUND(AVG(tiempo_atencion_min))                              AS tiempo_prom
            FROM auditorias_calidad
            WHERE fecha_auditoria >= NOW() - INTERVAL '24 hours'
        """)
        row = cur.fetchone()
        stats = {
            'pendientes_auditoria': len(reclamos_pendientes_auditoria),
            'total_auditados':  row[0] or 0,
            'conformes':        row[1] or 0,
            'reincidencias':    row[2] or 0,
            'mala_atencion':    row[3] or 0,
            'fuera_tiempo':     row[4] or 0,
            'dentro_sla':       row[5] or 0,
            'tiempo_prom':      int(row[6]) if row[6] else 0,
            'sla_minutos':      SLA_MINUTOS_MAX,
        }

        
        cur.execute("""
            SELECT
                aq.id, aq.reclamo_id, aq.resultado,
                aq.tiempo_atencion_min, aq.dentro_sla,
                aq.observaciones, aq.fecha_auditoria,
                aq.tecnico_nombre, aq.codigo_falla,
                u.nombre || ' ' || u.apellido AS auditor
            FROM auditorias_calidad aq
            JOIN usuarios u ON aq.auditor_id = u.usuario_id
            ORDER BY aq.fecha_auditoria DESC
            LIMIT 20
        """)
        auditorias_recientes = cur.fetchall()

    except Exception as e:
        print(f"ERROR dashboard_calidad: {e}")
        flash('Error al cargar el dashboard de calidad.', 'danger')
    finally:
        if cur:  cur.close()
        if conn: conn.close()

    return render_template(
        'dashboard_calidad.html',
        stats=stats,
        reclamos_pendientes=reclamos_pendientes_auditoria,
        auditorias_recientes=auditorias_recientes,
        nombre_usuario=session.get('nombre', ''),
        now=datetime.now()
    )


@app.route('/api/calidad/auditar_reclamo', methods=['POST'])
def api_auditar_reclamo():
    """
    Gestión de Calidad registra la auditoría de un reclamo cerrado.
    resultado: conforme | reincidencia | mala_atencion | fuera_tiempo
    """
    if 'usuario_id' not in session or not verificar_rol('calidad', 'help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data          = request.get_json()
        reclamo_id    = data.get('reclamo_id')
        resultado     = data.get('resultado')
        observaciones = (data.get('observaciones') or '').strip()

        RESULTADOS_VALIDOS = ('conforme', 'reincidencia', 'mala_atencion', 'fuera_tiempo')
        if not reclamo_id or resultado not in RESULTADOS_VALIDOS:
            return jsonify({'success': False, 'message': 'Datos incompletos o resultado no válido'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()

       
        cur.execute(
            "SELECT id FROM auditorias_calidad WHERE reclamo_id = %s",
            (reclamo_id,)
        )
        if cur.fetchone():
            return jsonify({'success': False, 'message': 'Este reclamo ya fue auditado'}), 400

        # Obtener datos del reclamo 
        cur.execute("""
            SELECT
                r.fecha_creacion, r.fecha_resolucion,
                r.tiempo_resolucion_min, r.codigo_falla_id,
                cf.codigo AS cod_falla,
                ut.nombre || ' ' || COALESCE(ut.apellido,'') AS tecnico_nombre,
                us.nombre || ' ' || COALESCE(us.apellido,'') AS operador_nombre
            FROM reclamos r
            LEFT JOIN codigos_falla cf ON r.codigo_falla_id = cf.id
            LEFT JOIN ordenes_trabajo ot ON ot.reclamo_id = r.id
            LEFT JOIN tecnicos tc        ON ot.tecnico_id  = tc.id
            LEFT JOIN usuarios ut        ON tc.usuario_id  = ut.usuario_id
            LEFT JOIN empleados_soporte es ON r.asignado_a = es.id
            LEFT JOIN usuarios us        ON es.usuario_id  = us.usuario_id
            WHERE r.id = %s
            LIMIT 1
        """, (reclamo_id,))
        snap = cur.fetchone()

        if not snap:
            return jsonify({'success': False, 'message': 'Reclamo no encontrado'}), 404

        tiempo_min = snap[2]
        dentro_sla = (tiempo_min is not None and tiempo_min <= SLA_MINUTOS_MAX)

        cur.execute("""
            INSERT INTO auditorias_calidad (
                reclamo_id, auditor_id, resultado,
                tiempo_atencion_min, dentro_sla, observaciones,
                tecnico_nombre, operador_nombre, codigo_falla,
                fecha_creacion_reclamo, fecha_cierre_reclamo,
                fecha_auditoria
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            RETURNING id
        """, (
            reclamo_id, session['usuario_id'], resultado,
            tiempo_min, dentro_sla, observaciones,
            snap[5], snap[6], snap[4],
            snap[0], snap[1]
        ))
        auditoria_id = cur.fetchone()[0]

        
        cur.execute(
            "UPDATE reclamos SET estado = 'auditado' WHERE id = %s",
            (reclamo_id,)
        )
        cur.execute("""
            INSERT INTO reclamos_seguimiento
                (reclamo_id, empleado_id, accion, descripcion)
            VALUES (%s, NULL, 'auditado',
                    'Gestión de Calidad auditó el reclamo. Resultado: ' || %s)
        """, (reclamo_id, resultado))

        conn.commit()
        return jsonify({
            'success': True,
            'auditoria_id': auditoria_id,
            'dentro_sla': dentro_sla,
            'tiempo_atencion_min': tiempo_min,
            'message': f'Auditoría registrada: {resultado}.'
        })

    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_auditar_reclamo: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/calidad/estadisticas')
def api_calidad_estadisticas():
    """Estadísticas para el dashboard de Gestión de Calidad."""
    if 'usuario_id' not in session or not verificar_rol('calidad', 'help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        
        cur.execute("""
            SELECT cf.codigo, cf.nombre, COUNT(*) AS total,
                   ROUND(AVG(r.tiempo_resolucion_min)) AS tiempo_prom
            FROM reclamos r
            JOIN codigos_falla cf ON r.codigo_falla_id = cf.id
            WHERE r.fecha_creacion >= NOW() - INTERVAL '7 days'
            GROUP BY cf.id, cf.codigo, cf.nombre
            ORDER BY total DESC
        """)
        por_codigo = [
            {'codigo': r[0], 'nombre': r[1], 'total': r[2], 'tiempo_prom': int(r[3]) if r[3] else 0}
            for r in cur.fetchall()
        ]

        cur.execute("""
            SELECT DATE(fecha_resolucion) AS dia,
                   COUNT(*) AS total,
                   COUNT(CASE WHEN tiempo_resolucion_min <= %s THEN 1 END) AS dentro_sla
            FROM reclamos
            WHERE estado IN ('cerrado','auditado')
              AND fecha_resolucion >= NOW() - INTERVAL '7 days'
            GROUP BY dia ORDER BY dia
        """, (SLA_MINUTOS_MAX,))
        tendencia = [
            {'dia': str(r[0]), 'total': r[1], 'dentro_sla': r[2]}
            for r in cur.fetchall()
        ]

        
        cur.execute("""
            SELECT COUNT(*) FROM auditorias_calidad
            WHERE resultado = 'reincidencia'
              AND fecha_auditoria >= NOW() - INTERVAL '7 days'
        """)
        reincidencias_semana = cur.fetchone()[0]

        return jsonify({
            'success': True,
            'por_codigo': por_codigo,
            'tendencia': tendencia,
            'reincidencias_semana': reincidencias_semana,
            'sla_minutos': SLA_MINUTOS_MAX
        })

    except Exception as e:
        print(f"ERROR api_calidad_estadisticas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()



def api_reclamos_pendientes_asignacion():
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'nodo_internet'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT
                r.id, u.nombre, u.apellido,
                r.tipo_reclamo, r.titulo, r.prioridad,
                r.fecha_creacion, r.servicio_afectado,
                r.problema_especifico, r.ubicacion_cliente,
                cf.codigo AS cod_falla, cf.nombre AS nom_falla,
                r.zona_nodo, r.zona_olt, r.tiempo_diagnostico_min,
                r.estado
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            LEFT JOIN codigos_falla cf ON r.codigo_falla_id = cf.id
            WHERE r.estado IN ('pendiente_asignacion', 'abierto', 'nuevo', 'falla_masiva')
              AND r.falla_masiva_id IS NULL
            ORDER BY
                CASE r.prioridad
                    WHEN 'critica' THEN 1 WHEN 'alta' THEN 2
                    WHEN 'media'   THEN 3 WHEN 'baja' THEN 4
                END,
                r.fecha_creacion ASC
        """)
        filas = cur.fetchall()
        return jsonify({
            'success': True,
            'reclamos': [
                {
                    'id': f[0], 'nombre': f[1], 'apellido': f[2],
                    'tipo_reclamo': f[3], 'titulo': f[4], 'prioridad': f[5],
                    'fecha_creacion': str(f[6]), 'servicio_afectado': f[7],
                    'problema_especifico': f[8], 'ubicacion_cliente': f[9],
                    'codigo_falla': f[10], 'nombre_falla': f[11],
                    'zona_nodo': f[12], 'zona_olt': f[13],
                    'tiempo_diagnostico_min': f[14], 'estado': f[15]
                }
                for f in filas
            ]
        })
    except Exception as e:
        print(f"ERROR api_reclamos_pendientes_asignacion: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()


@app.route('/api/soporte/reclamos_resueltos')
def api_soporte_reclamos_resueltos():
    """
    Historial permanente de reclamos resueltos/cerrados. A diferencia del
    panel "Fallas ingresadas" (que solo muestra resueltos de las últimas
    24h para no saturar la cola activa), esta lista no tiene límite de
    tiempo.
    """
    if 'usuario_id' not in session or not verificar_rol('help_desk'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    try:
        pagina = max(int(request.args.get('pagina', 1)), 1)
    except (TypeError, ValueError):
        pagina = 1
    tam_pagina = 15
    offset = (pagina - 1) * tam_pagina

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()

        ESTADOS_RESUELTOS_HD = (
            'resuelto', 'resuelto_remoto', 'resuelto_tecnico',
            'liberado', 'cerrado', 'auditado'
        )

        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE estado IN %s AND NOT (es_turno_nocturno = TRUE AND escalado_a IS NULL)
        """, (ESTADOS_RESUELTOS_HD,))
        total = cur.fetchone()[0]

        cur.execute("""
            SELECT r.id, u.nombre, u.apellido, r.titulo, r.estado, r.prioridad,
                   r.servicio_afectado, r.fecha_creacion, r.fecha_resolucion
            FROM reclamos r
            JOIN usuarios u ON r.usuario_id = u.usuario_id
            WHERE r.estado IN %s
              AND NOT (r.es_turno_nocturno = TRUE AND r.escalado_a IS NULL)
            ORDER BY COALESCE(r.fecha_resolucion, r.fecha_creacion) DESC
            LIMIT %s OFFSET %s
        """, (ESTADOS_RESUELTOS_HD, tam_pagina, offset))
        filas = cur.fetchall()

        return jsonify({
            'success': True,
            'total': total,
            'pagina': pagina,
            'tam_pagina': tam_pagina,
            'reclamos': [
                {
                    'id': f[0], 'cliente': f'{f[1]} {f[2]}', 'titulo': f[3],
                    'estado': f[4], 'prioridad': f[5], 'servicio': f[6] or '—',
                    'fecha_creacion': f[7].strftime('%d/%m/%Y %H:%M') if f[7] else None,
                    'fecha_resolucion': f[8].strftime('%d/%m/%Y %H:%M') if f[8] else None,
                }
                for f in filas
            ]
        })
    except Exception as e:
        print(f"ERROR api_soporte_reclamos_resueltos: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()

@app.route('/api/soporte/historial_estados/<int:reclamo_id>')
def api_historial_estados(reclamo_id):
    """Timeline completo de estados de un reclamo."""
    if 'usuario_id' not in session or not verificar_rol('help_desk', 'calidad', 'nodo_internet'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT rs.accion, rs.descripcion, rs.fecha_accion,
                   COALESCE(u.nombre || ' ' || u.apellido, 'Sistema') AS actor
            FROM reclamos_seguimiento rs
            LEFT JOIN empleados_soporte es ON rs.empleado_id = es.id
            LEFT JOIN usuarios u           ON es.usuario_id  = u.usuario_id
            WHERE rs.reclamo_id = %s
            ORDER BY rs.fecha_accion ASC
        """, (reclamo_id,))
        filas = cur.fetchall()
        return jsonify({
            'success': True,
            'historial': [
                {
                    'accion': f[0], 'descripcion': f[1],
                    'fecha': str(f[2]), 'actor': f[3]
                }
                for f in filas
            ]
        })
    except Exception as e:
        print(f"ERROR api_historial_estados: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()

# ============================================================
# ROL DE ADMINISTRADOR 

 
def obtener_estadisticas_admin():
    """Métricas globales del sistema para el panel de administrador."""
    conn = cur = None
    stats = {}
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT r.rol, COUNT(u.usuario_id)
            FROM roles r
            LEFT JOIN usuarios u ON u.id_rol = r.id_rol
            GROUP BY r.rol ORDER BY r.rol
        """)
        stats['usuarios_por_rol'] = cur.fetchall()
 
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = TRUE")
        stats['usuarios_activos'] = cur.fetchone()[0]
 
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE activo = FALSE")
        stats['usuarios_inactivos'] = cur.fetchone()[0]
 
        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE estado IN ('abierto','en_proceso','pendiente_asignacion','en_diagnostico','falla_masiva')
        """)
        stats['reclamos_activos'] = cur.fetchone()[0]
 
        cur.execute("""
            SELECT COUNT(*) FROM reclamos
            WHERE estado IN ('cerrado','auditado','resuelto','resuelto_tecnico','resuelto_remoto','liberado')
        """)
        stats['reclamos_resueltos'] = cur.fetchone()[0]
 
        cur.execute("""
            SELECT COUNT(*) FROM tramites_digitales
            WHERE activo = TRUE AND estado NOT IN ('completado','rechazado')
        """)
        stats['tramites_pendientes'] = cur.fetchone()[0]
 
        cur.execute("SELECT COUNT(*) FROM fallas_masivas WHERE estado IN ('activa','en_reparacion')")
        stats['fallas_masivas_activas'] = cur.fetchone()[0]
 
        return stats
    except Exception as e:
        print(f"ERROR obtener_estadisticas_admin: {e}")
        return stats
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
 
@app.route('/dashboard_admin')
def dashboard_admin():
    if 'usuario_id' not in session or not verificar_rol('administrador', 'admin'):
        flash('Acceso solo para administradores.', 'danger')
        return redirect(url_for('inicio_sesion'))
 
    conn = cur = None
    usuarios = []
    roles_disponibles = []
    stats = {}
    try:
        stats = obtener_estadisticas_admin()
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("""
            SELECT u.usuario_id, u.nombre, u.apellido, u.correo, u.telefono,
                   r.rol, u.activo, u.verificado, u.fecha_registro,
                   t.tipo_tecnico
            FROM usuarios u
            JOIN roles r ON u.id_rol = r.id_rol
            LEFT JOIN tecnicos t ON t.usuario_id = u.usuario_id
            ORDER BY u.fecha_registro DESC
            LIMIT 300
        """)
        usuarios = cur.fetchall()
 
        cur.execute("SELECT id_rol, rol FROM roles WHERE activo = TRUE ORDER BY rol")
        roles_disponibles = cur.fetchall()
 
    except Exception as e:
        print(f"ERROR dashboard_admin: {e}")
        flash('Error al cargar el panel de administrador.', 'danger')
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
    return render_template(
        'dashboard_admin.html',
        stats=stats,
        usuarios=usuarios,
        roles_disponibles=roles_disponibles,
        nombre_usuario=session.get('nombre', ''),
    )
 
 
@app.route('/api/admin/toggle_usuario/<int:usuario_id>', methods=['POST'])
def api_admin_toggle_usuario(usuario_id):
    """Activa o desactiva una cuenta de usuario."""
    if 'usuario_id' not in session or not verificar_rol('administrador', 'admin'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    if usuario_id == session['usuario_id']:
        return jsonify({'success': False, 'message': 'No puedes desactivar tu propia cuenta'}), 400
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE usuarios SET activo = NOT activo
            WHERE usuario_id = %s
            RETURNING activo
        """, (usuario_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Usuario no encontrado'}), 404
        conn.commit()
        nuevo_estado = row[0]
        return jsonify({
            'success': True,
            'activo': nuevo_estado,
            'message': 'Cuenta activada' if nuevo_estado else 'Cuenta desactivada'
        })
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_admin_toggle_usuario: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
@app.route('/api/admin/asignar_zona_empleado/<int:usuario_id>', methods=['POST'])
def api_admin_asignar_zona_empleado(usuario_id):
    if 'usuario_id' not in session or not verificar_rol('administrador', 'admin'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    conn = cur = None
    try:
        data    = request.get_json()
        zona_id = data.get('zona_id')
        if not zona_id:
            return jsonify({'success': False, 'message': 'Selecciona una zona.'}), 400

        conn = get_db_connection()
        cur  = conn.cursor()

        cur.execute("SELECT id, nombre FROM zonas WHERE id = %s AND activo = TRUE", (zona_id,))
        zona = cur.fetchone()
        if not zona:
            return jsonify({'success': False, 'message': 'Zona no válida.'}), 400

        cur.execute("""
            SELECT u.zona_id, r.rol
            FROM usuarios u JOIN roles r ON u.id_rol = r.id_rol
            WHERE u.usuario_id = %s
        """, (usuario_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404

        zona_anterior_id, rol_usuario = row[0], row[1].strip().lower()

        cur.execute("UPDATE usuarios SET zona_id = %s WHERE usuario_id = %s", (zona_id, usuario_id))
        if rol_usuario == 'tecnico':
            cur.execute("UPDATE tecnicos SET zona_id = %s WHERE usuario_id = %s AND activo = TRUE",
                        (zona_id, usuario_id))

        cur.execute("""
            INSERT INTO historial_zona (usuario_id, zona_anterior_id, zona_nueva_id, modificado_por, tipo_accion)
            VALUES (%s, %s, %s, %s, 'asignado_admin')
        """, (usuario_id, zona_anterior_id, zona_id, session['usuario_id']))

        conn.commit()
        return jsonify({
            'success': True,
            'zona_nombre': zona[1],
            'message': f'Zona "{zona[1]}" asignada correctamente.'
        })
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_admin_asignar_zona_empleado: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()

@app.route('/api/admin/crear_staff', methods=['POST'])
def api_admin_crear_staff():
    if 'usuario_id' not in session or not verificar_rol('administrador', 'admin'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        data = request.get_json()
        nombre       = (data.get('nombre') or '').strip()
        apellido     = (data.get('apellido') or '').strip()
        correo       = (data.get('correo') or '').strip()
        telefono     = (data.get('telefono') or '').strip()
        contraseña   = data.get('contraseña') or ''
        id_rol       = data.get('id_rol')
        tipo_tecnico = (data.get('tipo_tecnico') or '').strip().upper() or None
 
        if not all([nombre, apellido, correo, telefono, contraseña, id_rol]):
            return jsonify({'success': False, 'message': 'Todos los campos son obligatorios'}), 400
 
        if not validar_contraseña(contraseña):
            return jsonify({
                'success': False,
                'message': 'La contraseña debe tener 8+ caracteres, mayúscula, minúscula, número y símbolo'
            }), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE correo = %s", (correo,))
        if cur.fetchone()[0] > 0:
            return jsonify({'success': False, 'message': 'Este correo ya está registrado'}), 400
 
        cur.execute("SELECT rol FROM roles WHERE id_rol = %s", (id_rol,))
        rol_row = cur.fetchone()
        if not rol_row:
            return jsonify({'success': False, 'message': 'Rol no válido'}), 400
        rol_nombre = rol_row[0].strip().lower()
 
        if rol_nombre == 'tecnico' and tipo_tecnico not in ('RA', 'RC'):
            return jsonify({'success': False, 'message': 'Indica si el técnico es RA o RC'}), 400
 
        # busca un código disponible de ese rol ANTES de crear la cuenta
        cur.execute("""
            SELECT id, codigo FROM codigos_registro_empleado
            WHERE rol = %s AND activo = TRUE AND usado = FALSE
            ORDER BY id LIMIT 1
        """, (rol_nombre,))
        fila_codigo = cur.fetchone()
        if not fila_codigo:
            return jsonify({
                'success': False,
                'message': f'No quedan códigos disponibles para el rol "{rol_nombre}". Agrega más en codigos_registro_empleado.'
            }), 400
        codigo_id, codigo_asignado = fila_codigo
 
        contraseña_hash = generate_password_hash(contraseña)
 
        cur.execute("""
            INSERT INTO usuarios
                (nombre, apellido, correo, contraseña, telefono,
                 codigo_verificacion, verificado, fecha_registro, activo, id_rol)
            VALUES (%s,%s,%s,%s,%s,%s,TRUE,NOW(),TRUE,%s)
            RETURNING usuario_id
        """, (nombre, apellido, correo, contraseña_hash, telefono, generar_codigo(), id_rol))
        nuevo_id = cur.fetchone()[0]
 
        cur.execute("""
            UPDATE codigos_registro_empleado
            SET usado = TRUE, usuario_id = %s, fecha_uso = NOW()
            WHERE id = %s
        """, (nuevo_id, codigo_id))
 
        conn.commit()
 
        if rol_nombre == 'help_desk':
            asegurar_registro_empleado_soporte(nuevo_id)
        elif rol_nombre == 'tecnico':
            asegurar_registro_tecnico(nuevo_id, tipo_tecnico=tipo_tecnico)
 
        return jsonify({
            'success': True,
            'usuario_id': nuevo_id,
            'codigo_acceso': codigo_asignado,
            'message': f'Cuenta de {rol_nombre} creada para {nombre} {apellido}. '
                       f'Su código de acceso es {codigo_asignado} — entrégaselo junto con la contraseña temporal.'
        })
 
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_admin_crear_staff: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()
 
@app.route('/api/admin/actualizar_tipo_tecnico/<int:usuario_id>', methods=['POST'])
def api_admin_actualizar_tipo_tecnico(usuario_id):
    """Clasifica o corrige el tipo (RA/RC) de un técnico ya existente."""
    if 'usuario_id' not in session or not verificar_rol('administrador', 'admin'):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
 
    conn = cur = None
    try:
        data = request.get_json()
        tipo_tecnico = (data.get('tipo_tecnico') or '').strip().upper()
        if tipo_tecnico not in ('RA', 'RC'):
            return jsonify({'success': False, 'message': 'tipo_tecnico debe ser RA o RC'}), 400
 
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE tecnicos SET tipo_tecnico = %s
            WHERE usuario_id = %s
            RETURNING id
        """, (tipo_tecnico, usuario_id))
        row = cur.fetchone()
        if not row:
            return jsonify({'success': False, 'message': 'Este usuario no tiene un registro de técnico'}), 404
        conn.commit()
        return jsonify({'success': True, 'tipo_tecnico': tipo_tecnico, 'message': f'Técnico marcado como {tipo_tecnico}'})
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR api_admin_actualizar_tipo_tecnico: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cur:  cur.close()
        if conn: conn.close()



import click 
@app.cli.command('crear-admin')
def crear_admin_cli():
    """Crea el primer administrador y le asigna un código de acceso disponible."""
    click.echo("=" * 60)
    click.echo(" COTEL RL — Creación del primer administrador")
    click.echo("=" * 60)
 
    conn = cur = None
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
 
        cur.execute("SELECT id_rol FROM roles WHERE LOWER(rol) = 'administrador'")
        row = cur.fetchone()
        if not row:
            click.echo("\n No existe el rol 'administrador' en la tabla roles.")
            click.echo("   Corre primero la migración de roles y vuelve a intentar.")
            return
        id_rol_admin = row[0]
 
        cur.execute("""
            SELECT id, codigo FROM codigos_registro_empleado
            WHERE rol = 'administrador' AND activo = TRUE AND usado = FALSE
            ORDER BY id LIMIT 1
        """)
        fila_codigo = cur.fetchone()
        if not fila_codigo:
            click.echo("\n No quedan códigos de administrador disponibles.")
            click.echo("   Agrega uno: INSERT INTO codigos_registro_empleado (codigo, rol) VALUES ('XXXX','administrador');")
            return
        codigo_id, codigo_asignado = fila_codigo
 
        nombre   = click.prompt("Nombres")
        apellido = click.prompt("Apellidos")
 
        while True:
            correo = click.prompt("Correo electrónico")
            if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
                break
            click.echo("Correo inválido, intenta de nuevo.")
 
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE correo = %s", (correo,))
        if cur.fetchone()[0] > 0:
            click.echo(f"\n Ya existe una cuenta registrada con el correo {correo}.")
            return
 
        telefono = click.prompt("Teléfono")
 
        while True:
            contraseña   = click.prompt("Contraseña (8+ car., mayúscula, minúscula, número, símbolo)", hide_input=True)
            confirmacion = click.prompt("Confirma la contraseña", hide_input=True)
            if contraseña != confirmacion:
                click.echo("Las contraseñas no coinciden, intenta de nuevo.\n")
                continue
            if not validar_contraseña(contraseña):
                click.echo("La contraseña no cumple los requisitos, intenta de nuevo.\n")
                continue
            break
 
        contraseña_hash = generate_password_hash(contraseña)
 
        cur.execute("""
            INSERT INTO usuarios
                (nombre, apellido, correo, contraseña, telefono,
                 codigo_verificacion, verificado, fecha_registro, activo, id_rol)
            VALUES (%s,%s,%s,%s,%s,'0000',TRUE,NOW(),TRUE,%s)
            RETURNING usuario_id
        """, (nombre, apellido, correo, contraseña_hash, telefono, id_rol_admin))
        nuevo_id = cur.fetchone()[0]
 
        cur.execute("""
            UPDATE codigos_registro_empleado
            SET usado = TRUE, usuario_id = %s, fecha_uso = NOW()
            WHERE id = %s
        """, (nuevo_id, codigo_id))
 
        conn.commit()
 
        click.echo("\n Administrador creado correctamente.")
        click.echo(f"   usuario_id:       {nuevo_id}")
        click.echo(f"   correo:           {correo}")
        click.echo(f"   código de acceso: {codigo_asignado}   <-- para iniciar sesión")
        click.echo("\nEntra en /inicio_sesion con ese código de acceso + tu contraseña.")
 
    except Exception as e:
        if conn: conn.rollback()
        click.echo(f"\n Error: {e}")
    finally:
        if cur:  cur.close()
        if conn: conn.close()
# 


# ============================================================
# INICIO
# ============================== ==============================

if __name__ == '__main__':
    app.run(debug=True)