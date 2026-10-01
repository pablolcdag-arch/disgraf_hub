from lxml import etree
xml = """
<ar:CbtesAsoc xmlns:ar="http://ar.gov.afip.dif.FEV1/">
    <ar:CbteAsoc>
        <ar:Tipo>1</ar:Tipo>
        <ar:PtoVta>10</ar:PtoVta>
        <ar:Nro>81</ar:Nro>
    </ar:CbteAsoc>
</ar:CbtesAsoc>
"""
print("XML is valid?", etree.fromstring(xml) is not None)
