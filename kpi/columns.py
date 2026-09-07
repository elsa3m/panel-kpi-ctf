"""
Mapa de columnas de la hoja MOV-FIBRA (archivo DRIVE TIENDAS ... .xlsx).

La hoja tiene encabezados duplicados (varias columnas "META", "REAL", "FALTA"),
por eso el panel ubica cada dato por POSICIÓN de columna (1 = A, 2 = B, ...)
y valida al cargar que el encabezado de la fila 6 sea el esperado.

Si en algún mes cambia la estructura de la hoja, este es el único archivo que
hay que ajustar: cambia el número de columna y/o el texto esperado.
"""

# Fila donde están los encabezados "definitivos" (PDV, EJECUTIVO, META, REAL...)
HEADER_ROW = 6
# Primera fila con datos
FIRST_DATA_ROW = 7

# Celdas sueltas con parámetros del corte
CELL_FECHA_CORTE = (4, 2)        # fila 4, col B  -> fecha del corte (03/09/2026)
CELL_AVANCE_ESPERADO = (3, 2)    # fila 3, col B  -> % de avance esperado (días trabajados / días del mes)
ROW_PESOS_FICHA = 5              # fila 5, cols 145..151 -> peso de cada KPI en la ficha
ROW_TOPES_FICHA = 4              # fila 4, cols 145..151 -> tope de cada KPI (peso x 130 %)
ROW_ESTANDARES = 4               # fila 4 -> estándares mínimos (conv., attach, etc.)

# clave interna -> (número de columna, encabezado esperado en fila 6)
COLS = {
    # --- identificación -----------------------------------------------------
    "pdv":              (2,  "PDV"),
    "clave":            (3,  None),            # concatenación tienda+nombre (sin encabezado fijo)
    "ejecutivo":        (4,  "EJECUTIVO"),
    "dias_trab":        (5,  "DÍAS TRABAJADOS"),
    "dias_rest":        (6,  "DÍAS RESTANTES"),
    "atenciones":       (7,  "ATENCIONES"),
    "meta_rut":         (8,  "META RUT"),
    "cump_rut":         (9,  "CUMP %"),
    "rut_proy":         (10, "RUT PROY%"),
    # --- ENTEL MOVILIDAD: total móvil -----------------------------------------
    "mov_meta":         (12, "META"),
    "mov_real":         (13, "REAL"),
    "mov_falta":        (14, "FALTA"),
    "mov_deben":        (15, "DEBEN LLEVAR"),
    "mov_cump":         (16, "CUMP. TOTAL MOV"),
    "mov_conv":         (17, "CONV. MÓVIL"),
    # --- suscripción ----------------------------------------------------------
    "sus_meta":         (18, "META"),
    "sus_real":         (19, "REAL"),
    "sus_falta":        (20, "FALTA"),
    "sus_deben":        (21, "DEBEN LLEVAR"),
    "sus_cump":         (22, "CUMP. TOTAL SS"),
    "sus_conv":         (23, "CONV. SUS"),
    # --- migraciones (MIS) ----------------------------------------------------
    "mis_meta":         (24, "META"),
    "mis_real":         (25, "REAL"),
    "mis_falta":        (26, "FALTA"),
    "mis_cump":         (27, "CUMP. MIS"),
    # --- 1ra línea ------------------------------------------------------------
    "l1_meta":          (28, "META"),
    "l1_real":          (29, "REAL"),
    "l1_falta":         (30, "FALTA"),
    "l1_cump":          (31, "CUMP. PRIMERA LÍNEA"),
    # --- 2da línea ------------------------------------------------------------
    "l2_meta":          (32, "META"),
    "l2_real":          (33, "REAL"),
    "l2_falta":         (34, "FALTA"),
    "l2_cump":          (35, "CUMP. SEGUNDA LÍNEA"),
    # --- CVM campaña ----------------------------------------------------------
    "cvm_llegadas":     (36, "LLEGADAS"),
    "cvm_ventas":       (37, "VENTAS"),
    "cvm_50":           (38, "CVM 50%"),
    # --- 1ra + 2da ------------------------------------------------------------
    "l12_meta":         (39, "META"),
    "l12_real":         (40, "REAL"),
    "l12_falta":        (41, "FALTA"),
    "l12_cump":         (42, "CUMP. 1RAS + 2DAS"),
    # --- portabilidad ---------------------------------------------------------
    "porta_meta":       (43, "META"),
    "porta_real":       (44, "REAL"),
    "porta_falta":      (45, "FALTA"),
    "porta_deben":      (46, "DEBEN LLEVAR"),
    "porta_cump":       (47, "CUMP. PORTA"),
    "porta_conv":       (48, "CONV. PORTA"),
    "porta_peso":       (49, "PESO PORTA"),
    # --- FIBRA (real Entel) ---------------------------------------------------
    "fib_meta":         (52, "META FIBRA"),
    "fib_real":         (53, "REAL FIBRA"),
    "fib_falta":        (54, "FALTA"),
    "fib_deben":        (55, "DEBEN LLEVAR"),
    "fib_cump":         (56, "CUMP. FIBRA"),
    "tv_meta":          (57, "META TV"),
    "tv_real":          (58, "REAL TV"),
    "tv_falta":         (59, "FALTA"),
    "att_tv":           (60, "ATT TV-FIBRA"),
    "q_valid":          (61, "Q VALIDAC."),
    "pct_valid":        (62, "% VALIDAC."),
    "valid_inc":        (63, "VALID. INCORRECTAS"),
    "factibles":        (64, "FACTIBLES"),
    "pct_fact":         (65, "% FACT"),
    "conv_fibra":       (66, "CONV. FIBRA"),
    "factor_prod":      (67, "FACTOR DE PROD."),
    "tasa_inst":        (68, "TASA DE INSTALACIÓN"),
    "meta_sol":         (69, "META SOL"),
    "fib_sol":          (70, "FIBRA SOLICITUDES"),
    "sol_falta":        (71, "FALTA"),
    "fib_pend":         (72, "FIBRAS PENDIENTES"),
    # --- EQUIPOS --------------------------------------------------------------
    "eq_meta":          (86, "META"),
    "eq_tt":            (87, "$ EQUIPOS TT VENDIDOS"),
    "eq_anul":          (88, "$ EQUIPOS ANULADOS"),
    "eq_real":          (89, "REAL"),
    "eq_falta":         (90, "FALTA"),
    "eq_deben":         (91, "DEBEN LLEVAR"),
    "eq_cump":          (92, "CUMPL. EQ."),
    "eq_conv":          (93, "CONV. EQUIPOS"),
    "eq_meta_q":        (94, "META SMARTPHONES"),
    "eq_q":             (95, "Q EQ VENDIDOS"),
    "eq_con_linea":     (96, "VENTA CON LINEA"),
    "att_eq_linea":     (97, "ATT EQ - LINEA"),
    # --- SEGUROS --------------------------------------------------------------
    "seg_meta":         (98,  "META"),
    "seg_real":         (99,  "REAL"),
    "seg_falta":        (100, "FALTA"),
    "seg_deben":        (101, "DEBEN LLEVAR"),
    "seg_cump":         (102, "CUMPL. SEG."),
    "att_seg":          (103, "ATT EQ - SEGURO"),
    # --- ACCESORIOS -----------------------------------------------------------
    "acc_meta":         (104, "META"),
    "acc_tt":           (105, "$ ACC TT VENDIDOS"),
    "acc_anul":         (106, "$ ACC ANULADOS"),
    "acc_real":         (107, "REAL"),
    "acc_falta":        (108, "FALTA"),
    "acc_deben":        (109, "DEBEN LLEVAR"),
    "acc_cump":         (110, "CUMPL. ACC."),
    "acc_conv":         (111, "CONV. ACC"),
    "acc_meta_q":       (112, "META Q ACC"),
    "acc_q":            (113, "Q ACC VENDIDOS"),
    # --- ENERGÍA / PROTECCIÓN -------------------------------------------------
    "ene_usd":          (114, "$ Energía"),
    "ene_q":            (115, "Q ENERGÍA"),
    "ene_conv":         (116, "CONV ENERGIA"),
    "ene_att":          (117, "ATT ENERGÍA"),
    "prot_usd":         (118, "$ Proteccion"),
    "prot_q":           (119, "Q PROTEC."),
    "prot_conv":        (120, "CONV PROT."),
    "prot_att":         (121, "ATT PROTEC."),
    "prom_att_ene_prot":(122, "PROM ATT ENE - PROT"),
    # --- EPA ------------------------------------------------------------------
    "epa_meta":         (124, "META"),
    "epa":              (125, "EPA"),
    # --- FICHA (cumplimiento ponderado) ---------------------------------------
    "ficha_mis":        (145, "MIS"),
    "ficha_l12":        (146, "1RAS + 2DAS"),
    "ficha_port":       (147, "PORT"),
    "ficha_fibra":      (148, "FIBRA"),
    "ficha_epa":        (149, "EPA"),
    "ficha_eq":         (150, "$ EQ"),
    "ficha_acc":        (151, "$ ACC"),
    "cump_ficha":       (152, "TOTAL CUMP POND FICHA"),
    "tramo":            (153, "TRAMO"),
    "proy_pond":        (154, "% Proy Pond"),
    # --- BONO FOCO ------------------------------------------------------------
    "bf_cump_sus":      (156, "CUMP SUSC"),
    "bf_cump_fib":      (157, "CUMP FIBRA"),
    "bf_pct":           (158, "BONO FOCO %"),
    "bf_estado":        (159, "BONO FOCO $$$"),
    # --- BONO PORTABILIDAD ----------------------------------------------------
    "bp_meta":          (161, "META BONO PORTA"),
    "bp_real":          (162, "REAL PORTA + AF"),
    "bp_cump":          (163, "CUMP%"),
    "bp_bono":          (164, "$60.000 / $30.000"),
    # --- BONO WINNER ----------------------------------------------------------
    "bw_att_seg":       (166, "ATT EQ - SEGURO"),
    "bw_att_ene_prot":  (167, "ATT ENERGIA Y PROTECCIÓN"),
    "bw_att_tv":        (168, "ATT TV FULL"),
    "bw_cump":          (169, "% ACUM BONO WINNER"),
    "bw_bono":          (170, "$40.000 / $20.000"),
}

# Columnas de la fila 4 con los ESTÁNDARES mínimos usados por las alertas
ESTANDARES = {
    "mov_conv":     17,   # conversión móvil mínima (26 %)
    "sus_conv":     23,   # conversión suscripción mínima (24 %)
    "cvm_50":       38,   # CVM 50 % (16 %)
    "porta_conv":   48,   # conversión portabilidad (8 %)
    "porta_peso":   49,   # peso porta (35 %)
    "pct_valid":    62,   # % validación (85 %)
    "conv_fibra":   66,   # conversión fibra (12 %)
    "eq_conv":      93,   # conversión equipos (24 %)
    "att_eq_linea": 97,   # attach equipo-línea (27 %)
    "att_seg":      103,  # attach seguro (32 %)
    "acc_conv":     111,  # conversión accesorios (35 %)
    "ene_att":      117,  # attach energía (30 %)
    "prot_att":     121,  # attach protección (30 %)
}

# KPI de la ficha: (clave de peso, etiqueta)
FICHA_KPIS = [
    ("ficha_mis",   "MIS"),
    ("ficha_l12",   "1ra + 2da línea"),
    ("ficha_port",  "Portado"),
    ("ficha_fibra", "Fibra"),
    ("ficha_epa",   "EPA"),
    ("ficha_eq",    "$ Equipos"),
    ("ficha_acc",   "$ Accesorios"),
]
