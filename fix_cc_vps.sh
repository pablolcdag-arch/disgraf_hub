#!/bin/bash
sqlite3 /opt/disgraf_hub/data/disgraf_hub.db "UPDATE comprobantes SET impacta_cc = 1 WHERE tipo_comprobante IN ('Factura Electrónica A', 'Factura Electrónica B', 'Nota de Crédito A', 'Nota de Crédito B', 'Nota de Débito A', 'Nota de Débito B');"
