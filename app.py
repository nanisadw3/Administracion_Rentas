from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
from collections import defaultdict
from decimal import Decimal

app = Flask(__name__)
# --- Configuración ---
app.secret_key = os.environ.get("SECRET_KEY", "tu_clave_secreta_muy_dificil_de_adivinar")

# Conexión a la base de datos PostgreSQL
# Lee la URL de la base de datos desde la variable de entorno DATABASE_URL.
# Esto es estándar en plataformas como Railway y Heroku.
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    # Fallback para desarrollo local si DATABASE_URL no está configurada
    # Si corres localmente, asegúrate de que estas credenciales son correctas.
    print("ADVERTENCIA: DATABASE_URL no encontrada. Usando credenciales locales.")
    db_user = "postgres"
    db_pass = "usUegONwWMqTBaJFsbShELFArhkICbjT"
    db_host = "interchange.proxy.rlwy.net"
    db_port = "25545"
    db_name = "railway"
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# --- Modelos de la Base de Datos ---
class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    contratos = relationship(
        "Contrato", back_populates="inquilino", cascade="all, delete-orphan"
    )


class Propiedad(db.Model):
    __tablename__ = "propiedades"
    id = db.Column(db.Integer, primary_key=True)
    nombre_casa = db.Column(db.String(100), nullable=True)
    direccion = db.Column(db.String(255), nullable=False)
    ciudad = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    tipo_propiedad = db.Column(db.String(50))
    precio_renta_base = db.Column(db.Numeric(10, 2), nullable=False)
    estado = db.Column(db.String(50), nullable=False)
    fecha_disponible = db.Column(db.Date)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    contratos = relationship("Contrato", back_populates="propiedad")


class Contrato(db.Model):
    __tablename__ = "contratos"
    id = db.Column(db.Integer, primary_key=True)
    propiedad_id = db.Column(
        db.Integer, db.ForeignKey("propiedades.id"), nullable=False
    )
    inquilino_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    monto_renta_mensual = db.Column(db.Numeric(10, 2), nullable=False)
    estado_contrato = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    intencion_renovar = db.Column(db.Boolean, nullable=True)
    comentario_renovacion = db.Column(db.Text, nullable=True)
    inquilino = relationship("Usuario", back_populates="contratos")
    propiedad = relationship("Propiedad", back_populates="contratos")
    pagos = relationship(
        "Pago", back_populates="contrato", cascade="all, delete-orphan"
    )


class Pago(db.Model):
    __tablename__ = "pagos"
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey("contratos.id"), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    monto_pagado = db.Column(db.Numeric(10, 2), nullable=False)
    mes_correspondiente = db.Column(db.String(100), nullable=False)
    metodo_pago = db.Column(db.String(50))
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    contrato = relationship("Contrato", back_populates="pagos")


# --- Rutas de Autenticación ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Usuario.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["user_role"] = user.role
            session["user_name"] = user.nombre_completo
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Username o contraseña incorrectos.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado la sesión.", "info")
    return redirect(url_for("login"))


# --- Panel de Control ---
@app.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user_role = session["user_role"]
    if user_role == "administrador":
        ganancias_mensuales = defaultdict(float)
        pagos_activos = (
            db.session.query(Pago)
            .join(Contrato)
            .filter(Contrato.estado_contrato == "activo")
            .all()
        )
        for pago in pagos_activos:
            mes_del_pago = pago.fecha_pago.strftime("%Y-%m")
            ganancias_mensuales[mes_del_pago] += float(pago.monto_pagado)
        ganancias_ordenadas = sorted(
            ganancias_mensuales.items(), key=lambda item: item[0], reverse=True
        )

        propiedades = Propiedad.query.order_by(Propiedad.id).all()
        inquilinos = (
            Usuario.query.filter_by(role="inquilino").order_by(Usuario.id).all()
        )
        administradores = (
            Usuario.query.filter_by(role="administrador").order_by(Usuario.id).all()
        )
        return render_template(
            "dashboard_admin.html",
            propiedades=propiedades,
            inquilinos=inquilinos,
            administradores=administradores,
            ganancias=ganancias_ordenadas,
        )
    elif user_role == "inquilino":
        user_id = session["user_id"]
        contrato_activo = Contrato.query.filter_by(
            inquilino_id=user_id, estado_contrato="activo"
        ).first()
        contratos_inactivos = (
            Contrato.query.filter(
                Contrato.inquilino_id == user_id, Contrato.estado_contrato != "activo"
            )
            .order_by(Contrato.fecha_fin.desc())
            .all()
        )

        pagos = []
        num_pagos_actual = 0
        if contrato_activo:
            pagos = (
                Pago.query.filter_by(contrato_id=contrato_activo.id)
                .order_by(Pago.fecha_pago.desc())
                .all()
            )
            num_pagos_actual = len(pagos)

        return render_template(
            "dashboard_inquilino.html",
            contrato=contrato_activo,
            pagos=pagos,
            contratos_inactivos=contratos_inactivos,
            num_pagos_actual=num_pagos_actual,
        )
    else:
        flash("Rol de usuario no reconocido.", "danger")
        return redirect(url_for("login"))


# --- Gestión de Contratos ---
@app.route("/renovar_contrato/<int:contrato_id>", methods=["GET", "POST"])
def renovar_contrato(contrato_id):
    if "user_id" not in session or session.get("user_role") != "inquilino":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    contrato = Contrato.query.get_or_404(contrato_id)

    # Asegurarse de que el inquilino solo pueda ver sus propios contratos
    if contrato.inquilino_id != session["user_id"]:
        flash("Acceso no autorizado a este contrato.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        intencion = request.form.get("intencion_renovar")
        comentario = request.form.get("comentario_renovacion")

        if intencion == "si":
            contrato.intencion_renovar = True
        elif intencion == "no":
            contrato.intencion_renovar = False
        else:
            contrato.intencion_renovar = None  # Por si acaso se envía algo inesperado

        contrato.comentario_renovacion = comentario
        db.session.commit()
        flash("Tu intención de renovación ha sido registrada.", "success")
        return redirect(url_for("dashboard"))

    return render_template("renovar_contrato.html", contrato=contrato)


# --- Gestión de Propiedades ---
@app.route("/propiedad/agregar", methods=["GET", "POST"])
def agregar_propiedad():
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        nueva_propiedad = Propiedad(
            nombre_casa=request.form.get("nombre_casa"),
            direccion=request.form.get("direccion"),
            ciudad=request.form.get("ciudad"),
            descripcion=request.form.get("descripcion"),
            tipo_propiedad=request.form.get("tipo_propiedad"),
            precio_renta_base=Decimal(request.form.get("precio_renta_base")),
            estado=request.form.get("estado"),
            fecha_disponible=datetime.datetime.strptime(
                request.form.get("fecha_disponible"), "%Y-%m-%d"
            ).date()
            if request.form.get("fecha_disponible")
            else None,
        )
        db.session.add(nueva_propiedad)
        db.session.commit()
        flash("Propiedad agregada exitosamente.", "success")
        return redirect(url_for("dashboard"))

    return render_template("agregar_propiedad.html")


@app.route("/propiedad/editar/<int:propiedad_id>", methods=["GET", "POST"])
def propiedad_editar(propiedad_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    propiedad_a_editar = Propiedad.query.get_or_404(propiedad_id)

    if request.method == "POST":
        propiedad_a_editar.nombre_casa = request.form.get("nombre_casa")
        propiedad_a_editar.direccion = request.form.get("direccion")
        propiedad_a_editar.ciudad = request.form.get("ciudad")
        propiedad_a_editar.descripcion = request.form.get("descripcion")
        propiedad_a_editar.tipo_propiedad = request.form.get("tipo_propiedad")
        propiedad_a_editar.precio_renta_base = Decimal(
            request.form.get("precio_renta_base")
        )
        propiedad_a_editar.estado = request.form.get("estado")

        fecha_disponible_str = request.form.get("fecha_disponible")
        propiedad_a_editar.fecha_disponible = (
            datetime.datetime.strptime(fecha_disponible_str, "%Y-%m-%d").date()
            if fecha_disponible_str
            else None
        )

        db.session.commit()
        flash("Propiedad actualizada exitosamente.", "success")
        return redirect(
            url_for("propiedad_detalle", propiedad_id=propiedad_a_editar.id)
        )

    return render_template("propiedad_editar.html", propiedad=propiedad_a_editar)


@app.route("/propiedad/borrar/<int:propiedad_id>", methods=["POST"])
def propiedad_borrar(propiedad_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    propiedad_a_borrar = Propiedad.query.get_or_404(propiedad_id)

    # Check for active contracts before deleting
    if Contrato.query.filter_by(
        propiedad_id=propiedad_a_borrar.id, estado_contrato="activo"
    ).first():
        flash("No se puede borrar una propiedad con un contrato activo.", "danger")
        return redirect(
            url_for("propiedad_detalle", propiedad_id=propiedad_a_borrar.id)
        )

    db.session.delete(propiedad_a_borrar)
    db.session.commit()
    flash("Propiedad borrada exitosamente.", "success")
    return redirect(url_for("dashboard"))


@app.route("/propiedad/<int:propiedad_id>")
def propiedad_detalle(propiedad_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    propiedad = Propiedad.query.get_or_404(propiedad_id)
    contrato_activo = Contrato.query.filter_by(
        propiedad_id=propiedad.id, estado_contrato="activo"
    ).first()
    contratos_inactivos = (
        Contrato.query.filter(
            Contrato.propiedad_id == propiedad.id, Contrato.estado_contrato != "activo"
        )
        .order_by(Contrato.fecha_fin.desc())
        .all()
    )

    lista_meses = []
    if contrato_activo:
        import locale

        try:
            locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
        except locale.Error:
            locale.setlocale(locale.LC_TIME, "")

        pagos_realizados = {pago.mes_correspondiente for pago in contrato_activo.pagos}
        start_date = contrato_activo.fecha_inicio
        for i in range(12):
            current_year = start_date.year + (start_date.month + i - 1) // 12
            current_month = (start_date.month + i - 1) % 12 + 1

            month_name = (
                datetime.date(current_year, current_month, 1)
                .strftime("%B %Y")
                .capitalize()
            )
            month_param = f"{current_year}-{current_month:02d}"

            estado_pago = "Pagado" if month_param in pagos_realizados else "Pendiente"

            lista_meses.append(
                {"nombre": month_name, "param": month_param, "estado": estado_pago}
            )

    return render_template(
        "propiedad_detalle.html",
        propiedad=propiedad,
        contrato_activo=contrato_activo,
        lista_meses=lista_meses,
        contratos_inactivos=contratos_inactivos,
    )


# --- Gestión de Administradores ---
@app.route("/admin/restablecer_password/<int:user_id>", methods=["GET", "POST"])
def restablecer_password_admin(user_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    if session["user_id"] == user_id:
        flash(
            "No puedes restablecer tu propia contraseña desde esta interfaz.", "warning"
        )
        return redirect(url_for("dashboard"))

    admin_a_editar = Usuario.query.get_or_404(user_id)

    if admin_a_editar.role != "administrador":
        flash("Este usuario no es un administrador.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return render_template(
                "restablecer_password_admin.html", admin=admin_a_editar
            )

        if not password:
            flash("La contraseña no puede estar vacía.", "danger")
            return render_template(
                "restablecer_password_admin.html", admin=admin_a_editar
            )

        admin_a_editar.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256"
        )
        db.session.commit()

        flash(
            f"La contraseña para el administrador {admin_a_editar.username} ha sido actualizada.",
            "success",
        )
        return redirect(url_for("dashboard"))

    return render_template("restablecer_password_admin.html", admin=admin_a_editar)


# --- CRUD de Inquilinos ---
@app.route("/inquilino/<int:user_id>")
def inquilino_detalle(user_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))
    inquilino = Usuario.query.get_or_404(user_id)
    return render_template("inquilino_detalle.html", inquilino=inquilino)


@app.route("/inquilino/editar/<int:user_id>", methods=["GET", "POST"])
def inquilino_editar(user_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    inquilino_a_editar = Usuario.query.get_or_404(user_id)

    if request.method == "POST":
        nuevo_username = request.form["username"]
        nuevo_email = request.form["email"]

        if Usuario.query.filter(
            Usuario.id != user_id, Usuario.username == nuevo_username
        ).first():
            flash("Ese nombre de usuario ya está en uso por otra cuenta.", "danger")
            return redirect(url_for("inquilino_editar", user_id=user_id))

        if Usuario.query.filter(
            Usuario.id != user_id, Usuario.email == nuevo_email
        ).first():
            flash("Ese correo electrónico ya está en uso por otra cuenta.", "danger")
            return redirect(url_for("inquilino_editar", user_id=user_id))

        inquilino_a_editar.username = nuevo_username
        inquilino_a_editar.nombre_completo = request.form["nombre_completo"]
        inquilino_a_editar.email = nuevo_email
        inquilino_a_editar.telefono = request.form["telefono"]

        password = request.form["password"]
        if password:
            inquilino_a_editar.password_hash = generate_password_hash(
                password, method="pbkdf2:sha256"
            )

        db.session.commit()
        flash("Inquilino actualizado exitosamente.", "success")
        return redirect(url_for("inquilino_detalle", user_id=user_id))

    return render_template("inquilino_editar.html", inquilino=inquilino_a_editar)


@app.route("/inquilino/borrar/<int:user_id>", methods=["POST"])
def inquilino_borrar(user_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    inquilino_a_borrar = Usuario.query.get_or_404(user_id)
    db.session.delete(inquilino_a_borrar)
    db.session.commit()
    flash("Inquilino borrado exitosamente.", "success")
    return redirect(url_for("dashboard"))


# --- Agregar Inquilino ---
@app.route("/agregar_inquilino", methods=["GET", "POST"])
def agregar_inquilino():
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"]
        nombre_completo = request.form["nombre_completo"]
        email = request.form["email"]
        telefono = request.form["telefono"]
        password = request.form["password"]

        if Usuario.query.filter_by(username=username).first():
            flash("El nombre de usuario ya existe.", "danger")
            return redirect(url_for("agregar_inquilino"))
        if Usuario.query.filter_by(email=email).first():
            flash("El correo electrónico ya está en uso.", "danger")
            return redirect(url_for("agregar_inquilino"))

        nuevo_inquilino = Usuario(
            username=username,
            nombre_completo=nombre_completo,
            email=email,
            telefono=telefono,
            password_hash=generate_password_hash(password, method="pbkdf2:sha256"),
            role="inquilino",
        )
        db.session.add(nuevo_inquilino)
        db.session.commit()
        flash("Inquilino agregado exitosamente.", "success")
        return redirect(url_for("dashboard"))

    return render_template("agregar_inquilino.html")


# --- Gestión de Pagos ---
@app.route("/pago/registrar/<int:contrato_id>", methods=["GET", "POST"])
def registrar_pago(contrato_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    contrato = Contrato.query.get_or_404(contrato_id)
    mes_param = request.args.get("mes")
    if not mes_param:
        flash("Mes no especificado.", "danger")
        return redirect(
            url_for("propiedad_detalle", propiedad_id=contrato.propiedad_id)
        )

    try:
        year, month = map(int, mes_param.split("-"))
        mes_nombre = datetime.date(year, month, 1).strftime("%B %Y").capitalize()
    except:
        flash("Formato de mes inválido.", "danger")
        return redirect(
            url_for("propiedad_detalle", propiedad_id=contrato.propiedad_id)
        )

    if request.method == "POST":
        fecha_pago = datetime.datetime.strptime(
            request.form["fecha_pago"], "%Y-%m-%d"
        ).date()
        monto_pagado = request.form["monto_pagado"]
        metodo_pago = request.form["metodo_pago"]

        nuevo_pago = Pago(
            contrato_id=contrato.id,
            fecha_pago=fecha_pago,
            monto_pagado=monto_pagado,
            mes_correspondiente=mes_param,
            metodo_pago=metodo_pago,
        )
        db.session.add(nuevo_pago)
        db.session.commit()
        flash(f"Pago para {mes_nombre} registrado exitosamente.", "success")

        # Comprobar si es el 8º pago para solicitar intención de renovación
        num_pagos_actual = Pago.query.filter_by(contrato_id=contrato.id).count()
        if num_pagos_actual == 8 and contrato.intencion_renovar is None:
            flash("Se ha solicitado la intención de renovación al inquilino.", "info")

        # Comprobar si es el último pago
        num_pagos = Pago.query.filter_by(contrato_id=contrato.id).count()
        if num_pagos >= 12:
            contrato.estado_contrato = "finalizado"
            contrato.propiedad.estado = "disponible"
            db.session.commit()
            flash(
                f"Este fue el último pago. El contrato ha sido finalizado y la propiedad está disponible de nuevo.",
                "info",
            )

        return redirect(
            url_for("propiedad_detalle", propiedad_id=contrato.propiedad_id)
        )

    today = datetime.date.today().strftime("%Y-%m-%d")
    return render_template(
        "registrar_pago.html",
        contrato=contrato,
        mes_param=mes_param,
        mes_nombre=mes_nombre,
        today=today,
    )


# --- Gestión de Contratos ---
@app.route("/propiedad/<int:propiedad_id>/asignar_contrato", methods=["GET", "POST"])
def asignar_contrato(propiedad_id):
    if "user_id" not in session or session.get("user_role") != "administrador":
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for("login"))

    propiedad = Propiedad.query.get_or_404(propiedad_id)
    if propiedad.estado != "disponible":
        flash("Esta propiedad no está disponible para asignar un contrato.", "danger")
        return redirect(url_for("propiedad_detalle", propiedad_id=propiedad.id))

    if request.method == "POST":
        inquilino_id = request.form["inquilino_id"]
        fecha_inicio = datetime.datetime.strptime(
            request.form["fecha_inicio"], "%Y-%m-%d"
        ).date()
        fecha_fin = datetime.datetime.strptime(
            request.form["fecha_fin"], "%Y-%m-%d"
        ).date()
        monto_renta_mensual_str = request.form["monto_renta_mensual"]
        estado_contrato = request.form["estado_contrato"]

        monto_renta_mensual = Decimal(monto_renta_mensual_str)

        if monto_renta_mensual > propiedad.precio_renta_base:
            propiedad.precio_renta_base = monto_renta_mensual
            flash(
                "El precio de renta base de la propiedad ha sido actualizado al nuevo monto.",
                "info",
            )

        nuevo_contrato = Contrato(
            propiedad_id=propiedad.id,
            inquilino_id=inquilino_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            monto_renta_mensual=monto_renta_mensual,
            estado_contrato=estado_contrato,
        )

        propiedad.estado = "rentada"

        db.session.add(nuevo_contrato)
        db.session.commit()

        flash("Contrato asignado exitosamente.", "success")
        return redirect(url_for("propiedad_detalle", propiedad_id=propiedad.id))

    # GET request
    inquilinos = Usuario.query.filter_by(role="inquilino").all()
    return render_template(
        "asignar_contrato.html", propiedad=propiedad, inquilinos=inquilinos
    )


@app.cli.command("create-admin")
def create_admin():
    """Crea un usuario administrador inicial."""
    print("Creando usuario administrador...")
    try:
        # Revisa si el usuario ya existe
        if Usuario.query.filter_by(username='admin').first():
            print("El usuario 'admin' ya existe.")
            return

        # Crea el nuevo usuario
        admin = Usuario(
            username='admin',
            nombre_completo='Administrador',
            email='admin@example.com',
            password_hash=generate_password_hash('admin', method='pbkdf2:sha256'),
            role='administrador'
        )
        db.session.add(admin)
        db.session.commit()
        print("¡Usuario administrador 'admin' creado exitosamente!")
        print("Contraseña: admin")
    except Exception as e:
        print(f"Error al crear el usuario: {e}")
        db.session.rollback()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

