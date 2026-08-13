import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash
from app import app, db, Usuario, Propiedad, Contrato, Pago

def seed_data():
    print("Iniciando inserción de datos de ejemplo...")
    
    # 1. Crear Inquilinos
    inquilinos_data = [
        {
            "username": "juan_perez",
            "nombre_completo": "Juan Pérez Gómez",
            "email": "juan.perez@example.com",
            "telefono": "555-0192",
            "password": "inquilino_juan",
            "role": "inquilino"
        },
        {
            "username": "maria_lopez",
            "nombre_completo": "María López Torres",
            "email": "maria.lopez@example.com",
            "telefono": "555-0143",
            "password": "inquilino_maria",
            "role": "inquilino"
        },
        {
            "username": "carlos_sanchez",
            "nombre_completo": "Carlos Sánchez Ruiz",
            "email": "carlos.sanchez@example.com",
            "telefono": "555-0187",
            "password": "inquilino_carlos",
            "role": "inquilino"
        }
    ]
    
    inquilinos = []
    for data in inquilinos_data:
        user = Usuario.query.filter_by(username=data["username"]).first()
        if not user:
            user = Usuario(
                username=data["username"],
                nombre_completo=data["nombre_completo"],
                email=data["email"],
                telefono=data["telefono"],
                password_hash=generate_password_hash(data["password"], method="pbkdf2:sha256"),
                role=data["role"]
            )
            db.session.add(user)
            inquilinos.append(user)
            print(f"Inquilino creado: {data['username']} (clave: {data['password']})")
        else:
            inquilinos.append(user)
            print(f"El inquilino {data['username']} ya existe.")
            
    db.session.commit()
    
    # 2. Crear Propiedades
    propiedades_data = [
        {
            "nombre_casa": "Departamento Vista Alegre",
            "direccion": "Av. Reforma 405, Dpto 3B",
            "ciudad": "Ciudad de México",
            "descripcion": "Hermoso departamento de 2 habitaciones, 1 baño y balcón con excelente vista panorámica.",
            "tipo_propiedad": "Departamento",
            "precio_renta_base": Decimal("8500.00"),
            "estado": "Ocupado",
            "fecha_disponible": datetime.date(2026, 8, 1)
        },
        {
            "nombre_casa": "Casa Las Palmas",
            "direccion": "Calle Tulipanes 12, Col. Del Valle",
            "ciudad": "Guadalajara",
            "descripcion": "Casa amplia de 3 recámaras, 2.5 baños, patio trasero y cochera para 2 autos.",
            "tipo_propiedad": "Casa",
            "precio_renta_base": Decimal("15000.00"),
            "estado": "Ocupado",
            "fecha_disponible": datetime.date(2026, 8, 15)
        },
        {
            "nombre_casa": "Estudio Coyoacán",
            "direccion": "Callejón de los Milagros 8",
            "ciudad": "Ciudad de México",
            "descripcion": "Estudio acogedor amueblado, ideal para estudiantes o profesionistas individuales. Incluye servicios básicos.",
            "tipo_propiedad": "Estudio",
            "precio_renta_base": Decimal("6000.00"),
            "estado": "Disponible",
            "fecha_disponible": datetime.date(2026, 8, 20)
        }
    ]
    
    propiedades = []
    for data in propiedades_data:
        prop = Propiedad.query.filter_by(direccion=data["direccion"]).first()
        if not prop:
            prop = Propiedad(
                nombre_casa=data["nombre_casa"],
                direccion=data["direccion"],
                ciudad=data["ciudad"],
                descripcion=data["descripcion"],
                tipo_propiedad=data["tipo_propiedad"],
                precio_renta_base=data["precio_renta_base"],
                estado=data["estado"],
                fecha_disponible=data["fecha_disponible"]
            )
            db.session.add(prop)
            propiedades.append(prop)
            print(f"Propiedad creada: {data['nombre_casa']}")
        else:
            propiedades.append(prop)
            print(f"La propiedad en {data['direccion']} ya existe.")
            
    db.session.commit()
    
    # 3. Crear Contratos
    contratos_data = [
        {
            "propiedad_idx": 0, # Departamento Vista Alegre
            "inquilino_idx": 0, # Juan Perez
            "fecha_inicio": datetime.date(2026, 1, 1),
            "fecha_fin": datetime.date(2026, 12, 31),
            "monto_renta_mensual": Decimal("8500.00"),
            "estado_contrato": "Activo"
        },
        {
            "propiedad_idx": 1, # Casa Las Palmas
            "inquilino_idx": 1, # Maria Lopez
            "fecha_inicio": datetime.date(2026, 3, 15),
            "fecha_fin": datetime.date(2027, 3, 14),
            "monto_renta_mensual": Decimal("15000.00"),
            "estado_contrato": "Activo"
        }
    ]
    
    contratos = []
    for data in contratos_data:
        prop = propiedades[data["propiedad_idx"]]
        inquilino = inquilinos[data["inquilino_idx"]]
        
        contrato_exist = Contrato.query.filter_by(propiedad_id=prop.id, inquilino_id=inquilino.id).first()
        if not contrato_exist:
            contrato = Contrato(
                propiedad_id=prop.id,
                inquilino_id=inquilino.id,
                fecha_inicio=data["fecha_inicio"],
                fecha_fin=data["fecha_fin"],
                monto_renta_mensual=data["monto_renta_mensual"],
                estado_contrato=data["estado_contrato"]
            )
            db.session.add(contrato)
            contratos.append(contrato)
            print(f"Contrato creado para {inquilino.nombre_completo} en {prop.nombre_casa}")
        else:
            contratos.append(contrato_exist)
            print(f"El contrato para {inquilino.nombre_completo} ya existe.")
            
    db.session.commit()
    
    # 4. Crear Pagos
    # Vamos a registrar algunos pagos para los contratos
    if len(contratos) >= 2:
        pagos_data = [
            # Pagos de Juan Pérez (Contrato 0)
            {
                "contrato": contratos[0],
                "fecha_pago": datetime.date(2026, 1, 5),
                "monto_pagado": Decimal("8500.00"),
                "mes_correspondiente": "Enero 2026",
                "metodo_pago": "Transferencia"
            },
            {
                "contrato": contratos[0],
                "fecha_pago": datetime.date(2026, 2, 4),
                "monto_pagado": Decimal("8500.00"),
                "mes_correspondiente": "Febrero 2026",
                "metodo_pago": "Transferencia"
            },
            {
                "contrato": contratos[0],
                "fecha_pago": datetime.date(2026, 3, 5),
                "monto_pagado": Decimal("8500.00"),
                "mes_correspondiente": "Marzo 2026",
                "metodo_pago": "Efectivo"
            },
            # Pagos de María López (Contrato 1)
            {
                "contrato": contratos[1],
                "fecha_pago": datetime.date(2026, 3, 15),
                "monto_pagado": Decimal("15000.00"),
                "mes_correspondiente": "Marzo 2026",
                "metodo_pago": "Transferencia"
            },
            {
                "contrato": contratos[1],
                "fecha_pago": datetime.date(2026, 4, 14),
                "monto_pagado": Decimal("15000.00"),
                "mes_correspondiente": "Abril 2026",
                "metodo_pago": "Tarjeta de Crédito"
            }
        ]
        
        for data in pagos_data:
            pago_exist = Pago.query.filter_by(contrato_id=data["contrato"].id, mes_correspondiente=data["mes_correspondiente"]).first()
            if not pago_exist:
                pago = Pago(
                    contrato_id=data["contrato"].id,
                    fecha_pago=data["fecha_pago"],
                    monto_pagado=data["monto_pagado"],
                    mes_correspondiente=data["mes_correspondiente"],
                    metodo_pago=data["metodo_pago"]
                )
                db.session.add(pago)
                print(f"Pago registrado para {data['mes_correspondiente']}: {data['monto_pagado']}")
        
        db.session.commit()
    
    print("¡Proceso de datos de ejemplo terminado con éxito!")

if __name__ == "__main__":
    with app.app_context():
        seed_data()
