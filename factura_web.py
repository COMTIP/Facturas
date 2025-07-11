import streamlit as st
import requests
from datetime import datetime

st.title("Emisión de Factura Electrónica")

st.header("Datos del Cliente")
nombre = st.text_input("Nombre")
ruc = st.text_input("RUC")
dv = st.text_input("DV")
telefono = st.text_input("Teléfono")
direccion = st.text_input("Dirección")
correo = st.text_input("Correo")
factura_no = st.text_input("Factura No.")
fecha_emision = st.date_input("Fecha Emisión", value=datetime.today())

st.header("Items")
items = []
if 'items' not in st.session_state:
    st.session_state['items'] = []

with st.form("Agregar Ítem"):
    codigo = st.text_input("Código")
    descripcion = st.text_input("Descripción")
    cantidad = st.number_input("Cantidad", min_value=1.0, step=1.0)
    precio_unitario = st.number_input("Precio Unitario", min_value=0.0)
    itbms = st.number_input("ITBMS", min_value=0.0)
    submitted = st.form_submit_button("Agregar Ítem")
    if submitted:
        st.session_state['items'].append({
            "codigo": codigo,
            "descripcion": descripcion,
            "cantidad": cantidad,
            "precioUnitario": precio_unitario,
            "valorITBMS": itbms
        })

if st.session_state['items']:
    st.write("### Lista de Ítems")
    for idx, i in enumerate(st.session_state['items']):
        st.write(f"{idx+1}. {i['codigo']} | {i['descripcion']} | {i['cantidad']} | {i['precioUnitario']} | {i['valorITBMS']}")
    eliminar = st.number_input("Eliminar Ítem (número)", min_value=1, max_value=len(st.session_state['items']), step=1, key="eliminar")
    if st.button("Eliminar Ítem"):
        st.session_state['items'].pop(eliminar-1)
        st.experimental_rerun()

total_neto = sum(i["cantidad"] * i["precioUnitario"] for i in st.session_state['items'])
total_itbms = sum(i["valorITBMS"] for i in st.session_state['items'])
total_factura = total_neto + total_itbms

st.write(f"**Total Neto:** {total_neto:.2f}   **ITBMS:** {total_itbms:.2f}   **Total a Pagar:** {total_factura:.2f}")

medio_pago = st.selectbox("Medio de Pago", ["Efectivo", "Débito", "Crédito"])

if st.button("Enviar Factura"):
    forma_pago = {
        "formaPagoFact": {"Efectivo": "01", "Débito": "02", "Crédito": "03"}[medio_pago],
        "valorCuotaPagada": f"{total_factura:.2f}"
    }
    payload = {
        "documento": {
            "codigoSucursalEmisor": "0000",
            "tipoSucursal": "1",
            "datosTransaccion": {
                "tipoEmision": "01",
                "tipoDocumento": "01",
                "numeroDocumentoFiscal": factura_no,
                "puntoFacturacionFiscal": "001",
                "naturalezaOperacion": "01",
                "tipoOperacion": 1,
                "destinoOperacion": 1,
                "formatoCAFE": 1,
                "entregaCAFE": 1,
                "envioContenedor": 1,
                "procesoGeneracion": 1,
                "tipoVenta": 1,
                "fechaEmision": str(fecha_emision) + "T09:00:00-05:00",
                "cliente": {
                    "tipoClienteFE": "02",
                    "tipoContribuyente": 1,
                    "numeroRUC": ruc.replace("-", ""),
                    "digitoVerificadorRUC": dv,
                    "razonSocial": nombre,
                    "direccion": direccion,
                    "codigoUbicacion": "",
                    "provincia": "",
                    "distrito": "",
                    "corregimiento": "",
                    "tipoIdentificacion": "",
                    "telefono1": telefono,
                    "telefono2": "",
                    "telefono3": "",
                    "correoElectronico1": correo,
                    "correoElectronico2": "",
                    "correoElectronico3": "",
                    "pais": "PA",
                    "paisOtro": ""
                }
            },
            "listaItems": {
                "item": [
                    {
                        "codigo": i["codigo"],
                        "descripcion": i["descripcion"],
                        "codigoGTIN": "0",
                        "cantidad": f"{i['cantidad']:.2f}",
                        "precioUnitario": f"{i['precioUnitario']:.2f}",
                        "precioUnitarioDescuento": "0.00",
                        "precioItem": f"{i['cantidad'] * i['precioUnitario']:.2f}",
                        "valorTotal": f"{i['cantidad'] * i['precioUnitario'] + i['valorITBMS']:.2f}",
                        "cantGTINCom": f"{i['cantidad']:.2f}",
                        "codigoGTINInv": "0",
                        "tasaITBMS": "01" if i["valorITBMS"] > 0 else "00",
                        "valorITBMS": f"{i['valorITBMS']:.2f}",
                        "cantGTINComInv": f"{i['cantidad']:.2f}"
                    } for i in st.session_state['items']
                ]
            },
            "totalesSubTotales": {
                "totalPrecioNeto": f"{total_neto:.2f}",
                "totalITBMS": f"{total_itbms:.2f}",
                "totalMontoGravado": f"{total_itbms:.2f}",
                "totalDescuento": "0.00",
                "totalAcarreoCobrado": "0.00",
                "valorSeguroCobrado": "0.00",
                "totalFactura": f"{total_factura:.2f}",
                "totalValorRecibido": f"{total_factura:.2f}",
                "vuelto": "0.00",
                "tiempoPago": "1",
                "nroItems": str(len(st.session_state['items'])),
                "totalTodosItems": f"{total_factura:.2f}",
                "listaFormaPago": {
                    "formaPago": [forma_pago]
                }
            }
        }
    }
    st.write("JSON enviado:")
    st.json(payload)
    url = "https://ninox-factory-server.onrender.com/enviar-factura"
    try:
        response = requests.post(url, json=payload)
        st.success(f"Respuesta: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
