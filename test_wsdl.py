import requests
from lxml import etree

wsdl = requests.get("https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL").content
root = etree.fromstring(wsdl)
ns = {'s': 'http://www.w3.org/2001/XMLSchema', 'wsdl': 'http://schemas.xmlsoap.org/wsdl/'}
elements = root.findall('.//s:complexType[@name="FECAEDetRequest"]//s:element', namespaces=ns)
for e in elements:
    if "CbtesAsoc" in e.get('name', ''):
        print(etree.tostring(e))
