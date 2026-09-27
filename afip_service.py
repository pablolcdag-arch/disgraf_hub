import os
import json
import base64
import requests
import io
import qrcode
from datetime import datetime, timezone, timedelta
from lxml import etree
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7
from cryptography import x509
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


# ---------------------------------------------------------------------------
# Adaptador SSL para servidores AFIP/ARCA con claves DH pequeñas (legacy)
# Soluciona: [SSL: DH_KEY_TOO_SMALL] en Python 3.10+
# ---------------------------------------------------------------------------
class AFIPSSLAdapter(HTTPAdapter):
    """Adaptador SSL que permite las claves DH pequeñas de los servidores de AFIP/ARCA."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        super().init_poolmanager(*args, **kwargs)


def _make_afip_session() -> requests.Session:
    """Crea un requests.Session configurado para los servidores legacy SSL de AFIP."""
    session = requests.Session()
    session.mount("https://", AFIPSSLAdapter())
    return session


# ---------------------------------------------------------------------------
# URLs de producción AFIP/ARCA
# ---------------------------------------------------------------------------
WSAA_URL = "https://wsaa.afip.gov.ar/ws/services/LoginCms"
WSFE_URL = "https://servicios1.afip.gov.ar/wsfev1/service.asmx"
TA_CACHE_PATH = "data/afip_ta.json"

CUIT = int(os.environ.get("AFIP_CUIT", "20302544469"))
PTO_VTA = int(os.environ.get("AFIP_PTO_VTA", "10"))
CERT_PATH = "afip_certs/certificado.crt"
KEY_PATH = "afip_certs/private.key"


# ---------------------------------------------------------------------------
# Función 1: Construir el TRA (Ticket de Requerimiento de Acceso)
# ---------------------------------------------------------------------------
def _build_tra() -> bytes:
    """Construye el XML del Ticket de Requerimiento de Acceso para WSAA."""
    now_utc = datetime.now(timezone.utc)
    generation_time = now_utc.isoformat()
    expiration_time = (now_utc + timedelta(minutes=10)).isoformat()
    unique_id = int(now_utc.timestamp())

    tra_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<loginTicketRequest version="1.0">\n'
        "  <header>\n"
        f"    <uniqueId>{unique_id}</uniqueId>\n"
        f"    <generationTime>{generation_time}</generationTime>\n"
        f"    <expirationTime>{expiration_time}</expirationTime>\n"
        "  </header>\n"
        "  <service>wsfe</service>\n"
        "</loginTicketRequest>"
    )
    return tra_xml.encode("utf-8")


# ---------------------------------------------------------------------------
# Función 2: Firmar el TRA con el certificado y clave privada
# ---------------------------------------------------------------------------
def _sign_tra(tra_bytes: bytes) -> str:
    """
    Firma el TRA usando PKCS7/CMS con SHA-256.
    Retorna el CMS firmado en base64 (para enviar al WSAA).
    Usa la librería `cryptography` (incluida como dependencia de pyOpenSSL).
    """
    try:
        with open(KEY_PATH, "rb") as f:
            private_key = serialization.load_pem_private_key(f.read(), password=None)
        with open(CERT_PATH, "rb") as f:
            certificate = x509.load_pem_x509_certificate(f.read())

        builder = pkcs7.PKCS7SignatureBuilder()
        builder = builder.set_data(tra_bytes)
        builder = builder.add_signer(certificate, private_key, hashes.SHA256())
        cms_der = builder.sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.Binary])
        return base64.b64encode(cms_der).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Error al firmar el TRA: {e}")


# ---------------------------------------------------------------------------
# Función 3: Obtener Ticket de Acceso (con caché)
# ---------------------------------------------------------------------------
def get_ticket_acceso() -> tuple:
    """
    Devuelve (token, sign) para operar con WSFE.
    Usa caché en data/afip_ta.json; renueva el ticket si está por vencer
    (menos de 10 minutos de vida útil restante).
    """
    now_utc = datetime.now(timezone.utc)
    margen = timedelta(minutes=10)

    # Intentar usar el caché
    if os.path.exists(TA_CACHE_PATH):
        try:
            with open(TA_CACHE_PATH, "r", encoding="utf-8") as f:
                ta_data = json.load(f)
            expiration_str = ta_data.get("expiration", "")
            expiration_dt = datetime.fromisoformat(expiration_str)
            # Asegurar que tenga tzinfo
            if expiration_dt.tzinfo is None:
                expiration_dt = expiration_dt.replace(tzinfo=timezone.utc)
            if expiration_dt > now_utc + margen:
                return ta_data["token"], ta_data["sign"]
        except Exception:
            pass  # Cache corrupto → generar uno nuevo

    # Construir y firmar el TRA
    tra_bytes = _build_tra()
    cms_b64 = _sign_tra(tra_bytes)

    # Llamada SOAP al WSAA
    soap_body = (
        '<soapenv:Envelope '
        'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:wsaa="http://wsaa.view.sua.dvadac.desein.afip.gov">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<wsaa:loginCms>"
        f"<wsaa:in0>{cms_b64}</wsaa:in0>"
        "</wsaa:loginCms>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '""',
    }

    try:
        session = _make_afip_session()
        response = session.post(WSAA_URL, data=soap_body.encode("utf-8"), headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        raise ValueError(f"Error AFIP WSAA (HTTP): {e}")

    # Parsear respuesta XML
    try:
        root = etree.fromstring(response.content)
        ns = {"soapenv": "http://schemas.xmlsoap.org/soap/envelope/"}
        # El loginCmsReturn contiene el XML del ticket de acceso
        login_return_nodes = root.findall(".//{*}loginCmsReturn")
        if not login_return_nodes:
            raise ValueError("No se encontró loginCmsReturn en la respuesta del WSAA.")
        ticket_xml_str = login_return_nodes[0].text
        ticket_root = etree.fromstring(ticket_xml_str.encode("utf-8"))

        token = ticket_root.findtext(".//{*}token") or ticket_root.findtext(".//token")
        sign = ticket_root.findtext(".//{*}sign") or ticket_root.findtext(".//sign")
        expiration = (
            ticket_root.findtext(".//{*}expirationTime")
            or ticket_root.findtext(".//expirationTime")
        )

        if not token or not sign:
            raise ValueError("Respuesta WSAA no contiene token o sign válidos.")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error AFIP WSAA (parseo XML): {e}")

    # Guardar en caché
    ta_data = {"token": token, "sign": sign, "expiration": expiration or ""}
    try:
        os.makedirs(os.path.dirname(TA_CACHE_PATH), exist_ok=True)
        with open(TA_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(ta_data, f, ensure_ascii=False)
    except Exception as e:
        # No crítico: continuar aunque no se pueda guardar el caché
        print(f"Advertencia: no se pudo guardar el caché del ticket AFIP: {e}")

    return token, sign


# ---------------------------------------------------------------------------
# Función 4: Obtener el último comprobante autorizado en WSFE
# ---------------------------------------------------------------------------
def _get_ultimo_comprobante(token: str, sign: str, pto_vta: int, tipo_cbte: int) -> int:
    """Consulta a WSFE el último número de comprobante autorizado."""
    soap_body = (
        '<soapenv:Envelope '
        'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ar="http://ar.gov.afip.dif.FEV1/">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<ar:FECompUltimoAutorizado>"
        "<ar:Auth>"
        f"<ar:Token>{token}</ar:Token>"
        f"<ar:Sign>{sign}</ar:Sign>"
        f"<ar:Cuit>{CUIT}</ar:Cuit>"
        "</ar:Auth>"
        f"<ar:PtoVta>{pto_vta}</ar:PtoVta>"
        f"<ar:CbteTipo>{tipo_cbte}</ar:CbteTipo>"
        "</ar:FECompUltimoAutorizado>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"http://ar.gov.afip.dif.FEV1/FECompUltimoAutorizado"',
    }

    try:
        session = _make_afip_session()
        response = session.post(WSFE_URL, data=soap_body.encode("utf-8"), headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        raise ValueError(f"Error AFIP WSFE (FECompUltimoAutorizado HTTP): {e}")

    try:
        root = etree.fromstring(response.content)
        cbte_nro_node = root.findall(".//{*}CbteNro")
        if not cbte_nro_node:
            raise ValueError("No se encontró CbteNro en la respuesta de WSFE.")
        return int(cbte_nro_node[0].text)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error AFIP WSFE (FECompUltimoAutorizado parseo): {e}")


# ---------------------------------------------------------------------------
# Función 5: Emitir factura electrónica
# ---------------------------------------------------------------------------
def emitir_factura(cliente_nro, total: float, tipo_factura: str, iva_reducido: bool = False) -> dict:
    """
    Emite una factura electrónica ante AFIP/ARCA vía SOAP directo.

    tipo_factura valores soportados:
      - "Factura Electrónica A" → tipo_cbte=1
      - "Factura Electrónica B" → tipo_cbte=6
      - "Nota de Crédito A"     → tipo_cbte=3
      - "Nota de Crédito B"     → tipo_cbte=8

    Retorna dict con: cae, cae_vto, numero_afip, pto_vta, doc_tipo, doc_nro,
                      tipo_cbte, fecha, total
    """
    pto_vta = PTO_VTA

    # Determinar tipo de comprobante
    tipo_map = {
        "Factura Electrónica A": 1,
        "Factura Electrónica B": 6,
        "Nota de Crédito A": 3,
        "Nota de Crédito B": 8,
    }
    tipo_cbte = tipo_map.get(tipo_factura)
    if tipo_cbte is None:
        raise ValueError(f"Tipo de factura no reconocido: '{tipo_factura}'")

    # Determinar tipo y número de documento del receptor
    doc_nro_str = str(cliente_nro).strip() if cliente_nro else ""
    if doc_nro_str.isdigit() and int(doc_nro_str) > 0:
        doc_nro = int(doc_nro_str)
        if len(doc_nro_str) == 11:
            doc_tipo = 80  # CUIT
        else:
            doc_tipo = 96  # DNI
    else:
        doc_tipo = 99  # Consumidor Final
        doc_nro = 0

    # Regla AFIP: Factura A (tipo_cbte=1) solo puede emitirse con CUIT válido (DocTipo=80)
    if tipo_cbte == 1 and (doc_tipo != 80 or doc_nro == 0):
        raise ValueError(
            "Factura A requiere un cliente Responsable Inscripto con CUIT válido. "
            "No se puede emitir Factura A a Consumidor Final."
        )

    # Calcular montos de IVA
    alicuota_pct = 10.5 if iva_reducido else 21.0
    id_alicuota = 4 if iva_reducido else 5  # 4=10.5%, 5=21%
    neto = round(total / (1 + alicuota_pct / 100), 2)
    iva = round(total - neto, 2)

    # Obtener ticket de acceso
    try:
        token, sign = get_ticket_acceso()
    except Exception as e:
        raise ValueError(f"Error AFIP WSAA: {e}")

    # Obtener último comprobante y calcular próximo número
    try:
        ultimo = _get_ultimo_comprobante(token, sign, pto_vta, tipo_cbte)
    except Exception as e:
        raise ValueError(f"Error AFIP WSFE (último comprobante): {e}")

    numero_cbte = ultimo + 1
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    # Construir SOAP FECAESolicitar
    soap_body = (
        '<soapenv:Envelope '
        'xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" '
        'xmlns:ar="http://ar.gov.afip.dif.FEV1/">'
        "<soapenv:Header/>"
        "<soapenv:Body>"
        "<ar:FECAESolicitar>"
        "<ar:Auth>"
        f"<ar:Token>{token}</ar:Token>"
        f"<ar:Sign>{sign}</ar:Sign>"
        f"<ar:Cuit>{CUIT}</ar:Cuit>"
        "</ar:Auth>"
        "<ar:FeCAEReq>"
        "<ar:FeCabReq>"
        "<ar:CantReg>1</ar:CantReg>"
        f"<ar:PtoVta>{pto_vta}</ar:PtoVta>"
        f"<ar:CbteTipo>{tipo_cbte}</ar:CbteTipo>"
        "</ar:FeCabReq>"
        "<ar:FeDetReq>"
        "<ar:FECAEDetRequest>"
        "<ar:Concepto>1</ar:Concepto>"
        f"<ar:DocTipo>{doc_tipo}</ar:DocTipo>"
        f"<ar:DocNro>{doc_nro}</ar:DocNro>"
        f"<ar:CbteDesde>{numero_cbte}</ar:CbteDesde>"
        f"<ar:CbteHasta>{numero_cbte}</ar:CbteHasta>"
        f"<ar:CbteFch>{date_str}</ar:CbteFch>"
        f"<ar:ImpTotal>{total:.2f}</ar:ImpTotal>"
        "<ar:ImpTotConc>0.00</ar:ImpTotConc>"
        f"<ar:ImpNeto>{neto:.2f}</ar:ImpNeto>"
        "<ar:ImpOpEx>0.00</ar:ImpOpEx>"
        "<ar:ImpTrib>0.00</ar:ImpTrib>"
        f"<ar:ImpIVA>{iva:.2f}</ar:ImpIVA>"
        "<ar:MonId>PES</ar:MonId>"
        "<ar:MonCotiz>1</ar:MonCotiz>"
        "<ar:Iva>"
        "<ar:AlicIva>"
        f"<ar:Id>{id_alicuota}</ar:Id>"
        f"<ar:BaseImp>{neto:.2f}</ar:BaseImp>"
        f"<ar:Importe>{iva:.2f}</ar:Importe>"
        "</ar:AlicIva>"
        "</ar:Iva>"
        "</ar:FECAEDetRequest>"
        "</ar:FeDetReq>"
        "</ar:FeCAEReq>"
        "</ar:FECAESolicitar>"
        "</soapenv:Body>"
        "</soapenv:Envelope>"
    )

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": '"http://ar.gov.afip.dif.FEV1/FECAESolicitar"',
    }

    try:
        session = _make_afip_session()
        response = session.post(WSFE_URL, data=soap_body.encode("utf-8"), headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        raise ValueError(f"Error AFIP WSFE (FECAESolicitar HTTP): {e}")

    # Parsear respuesta
    try:
        root = etree.fromstring(response.content)

        # Verificar resultado global
        resultado_node = root.findall(".//{*}Resultado")
        if resultado_node:
            resultado = resultado_node[0].text
            if resultado != "A":
                # Extraer observaciones/errores de AFIP
                obs_msgs = []
                for obs in root.findall(".//{*}Obs"):
                    code = obs.findtext("{*}Code") or obs.findtext("Code") or ""
                    msg = obs.findtext("{*}Msg") or obs.findtext("Msg") or ""
                    obs_msgs.append(f"[{code}] {msg}")
                for err in root.findall(".//{*}Err"):
                    code = err.findtext("{*}Code") or err.findtext("Code") or ""
                    msg = err.findtext("{*}Msg") or err.findtext("Msg") or ""
                    obs_msgs.append(f"Error [{code}] {msg}")
                detalle = " | ".join(obs_msgs) if obs_msgs else "Sin detalle."
                raise ValueError(f"AFIP rechazó el comprobante. Resultado={resultado}. {detalle}")

        cae_node = root.findall(".//{*}CAE")
        cae_vto_node = root.findall(".//{*}CAEFchVto")

        if not cae_node or not cae_vto_node:
            raise ValueError("La respuesta de AFIP no contiene CAE o CAEFchVto.")

        cae = cae_node[0].text
        cae_vto_raw = cae_vto_node[0].text  # formato YYYYMMDD

        # Normalizar fecha de vencimiento a YYYY-MM-DD
        if cae_vto_raw and len(cae_vto_raw) == 8:
            cae_vto = f"{cae_vto_raw[:4]}-{cae_vto_raw[4:6]}-{cae_vto_raw[6:8]}"
        else:
            cae_vto = cae_vto_raw

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error AFIP WSFE (FECAESolicitar parseo): {e}")

    return {
        "cae": cae,
        "cae_vto": cae_vto,
        "numero_afip": numero_cbte,
        "pto_vta": pto_vta,
        "doc_tipo": doc_tipo,
        "doc_nro": doc_nro,
        "tipo_cbte": tipo_cbte,
        "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "total": total,
    }


# ---------------------------------------------------------------------------
# Función 6: Generar QR AFIP (sin modificaciones)
# ---------------------------------------------------------------------------
def generar_qr_afip(cae, numero_afip, pto_vta, doc_tipo, doc_nro, tipo_cbte, fecha, total):
    cuit = int(os.environ.get("AFIP_CUIT", "20302544469"))

    qr_data = {
        "ver": 1,
        "fecha": fecha,
        "cuit": cuit,
        "ptoVta": pto_vta,
        "tipoCmp": tipo_cbte,
        "nroCmp": numero_afip,
        "importe": total,
        "moneda": "PES",
        "ctz": 1,
        "tipoDocRec": doc_tipo,
        "nroDocRec": doc_nro,
        "tipoCodAut": "E",
        "codAut": int(cae),
    }

    json_str = json.dumps(qr_data)
    b64 = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    url = f"https://www.afip.gob.ar/fe/qr/?p={b64}"

    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
