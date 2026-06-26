# config.py
# ============================================================
# CONFIGURACIÓN GLOBAL – ARQUITECTURA MULTIESTRATEGIA
# VERSIÓN CON CONFIGURACIÓN INDIVIDUAL POR ACTIVO Y UNIVERSO AMPLIADO
# ============================================================

# ---- Símbolos y operativa (UNIVERSO AMPLIADO A 10 ACTIVOS) ----
SYMBOLS = [
    'BTC', 'ETH', 'SOL', 'ADA', 'XRP',   # 5 originales
    'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI' # 5 nuevos (alta liquidez OKX)
]
TRADE_NOTIONAL = 1000.0          # USDT por operación (se ajusta dinámicamente en main)
LEVERAGE = 10                    # Apalancamiento fijo

# ---- Parámetros de estrategia (OPTIMIZADOS - GLOBAL) ----
# Estos valores se usan como fallback si no hay configuración específica por activo
TP_MULT = 1.0                    # Take Profit = ATR * 1.0 (óptimo)
SL_MULT = 1.2                    # Stop Loss = ATR * 1.2 (óptimo)
ATR_PERIOD = 14
BE_GAIN = 0.0005                 # Breakeven con ganancia mínima
BE_UMBRAL = 0.25                 # Activación BE al 25% del TP (optimizado)

# ---- Trailing Stop ----
TRAILING_ENABLED = True
TRAILING_MODE = 'native'
TRAILING_DISTANCE_ATR = 0.6      # Optimizado (antes 0.8)
TRAILING_ACTIVATION_PROFIT = 0.6 # Optimizado (antes 0.8)

# ---- Niveles de velocidad (AutoSpeed) ----
SPEED_LEVELS = [
    {"nivel": 1, "raw_min": 0.45, "roc_min": 0.30},
    {"nivel": 2, "raw_min": 0.40, "roc_min": 0.25},
    {"nivel": 3, "raw_min": 0.35, "roc_min": 0.20},
    {"nivel": 4, "raw_min": 0.30, "roc_min": 0.15},
    {"nivel": 5, "raw_min": 0.25, "roc_min": 0.10},
    {"nivel": 6, "raw_min": 0.20, "roc_min": 0.05},
]
DEFAULT_SPEED_LEVEL = SPEED_LEVELS[1]   # N2 (óptimo global)

# ---- CONFIGURACIÓN INDIVIDUAL POR ACTIVO (NUEVO) ----
# Permite sobrescribir parámetros globales para activos específicos.
# Si un activo no está en este diccionario, usa los valores globales.
# Estructura: { 'ACTIVO': {'speed_level': dict, 'tp_mult': float, 'sl_mult': float, 'be_umbral': float, 'trailing_dist': float, 'trailing_act': float} }
PER_ASSET_CONFIG = {
    'BTC': {
        'speed_level': SPEED_LEVELS[1],      # N2
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.25,
        'trailing_dist': 0.6,
        'trailing_act': 0.6,
    },
    'ETH': {
        'speed_level': SPEED_LEVELS[1],      # N2
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.25,
        'trailing_dist': 0.6,
        'trailing_act': 0.6,
    },
    'SOL': {
        'speed_level': SPEED_LEVELS[2],      # N3 (más laxo para generar señales)
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
    'ADA': {
        'speed_level': SPEED_LEVELS[2],      # N3
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
    'XRP': {
        'speed_level': SPEED_LEVELS[3],      # N4 (más laxo)
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
    'DOT': {
        'speed_level': SPEED_LEVELS[2],      # N3
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
    'AVAX': {
        'speed_level': SPEED_LEVELS[2],      # N3
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
    'MATIC': {
        'speed_level': SPEED_LEVELS[3],      # N4
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
    'LINK': {
        'speed_level': SPEED_LEVELS[2],      # N3
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
    'UNI': {
        'speed_level': SPEED_LEVELS[3],      # N4
        'tp_mult': 1.0,
        'sl_mult': 1.2,
        'be_umbral': 0.30,
        'trailing_dist': 0.5,
        'trailing_act': 0.5,
    },
}

# ---- Niveles optimizados por activo (para compatibilidad con main.py) ----
# Se construye automáticamente a partir de PER_ASSET_CONFIG, pero se mantiene
# por si algún módulo lo espera.
OPTIMIZED_LEVELS = {
    symbol: {'Long': cfg['speed_level'], 'Short': cfg['speed_level']}
    for symbol, cfg in PER_ASSET_CONFIG.items()
}

# ---- Filtros horarios (DESACTIVADO – 24/7) ----
TIME_FILTER_ENABLED = False
TIME_FILTER_START = 12
TIME_FILTER_END = 18
TIME_FILTER_WEEKDAYS = [0, 1, 2, 3, 4]

# ---- Filtros por activo (AMPLIADOS PARA 10 ACTIVOS) ----
FILTERS = {
    'BTC': {'Long': {'ker_min': 0.55, 'zscore_min': 1.2},
            'Short': {'zscore_max': -1.8, 'vol_rel_min': 1.8}},
    'ETH': {'Long': {'ker_min': 0.50, 'atr_percent_min': 0.75},
            'Short': {'zscore_max': -1.5, 'ker_min': 0.50}},
    'SOL': {'Long': {'vol_rel_min': 1.8, 'ema_pend_min': 0.0015},
            'Short': {'ker_min': 0.60, 'zscore_max': -1.2}},
    'ADA': {'Long': {'ker_min': 0.45, 'vol_rel_min': 1.5, 'atr_percent_min': 0.80},
            'Short': {'ker_min': 0.45, 'zscore_max': -1.0, 'vol_rel_min': 1.5}},
    'XRP': {'Long': {'ker_min': 0.40, 'vol_rel_min': 1.5, 'zscore_min': 0.8},
            'Short': {'ker_min': 0.40, 'zscore_max': -0.8, 'vol_rel_min': 1.5}},
    # NUEVOS ACTIVOS (filtros genéricos adaptados a su comportamiento)
    'DOT': {'Long': {'ker_min': 0.45, 'vol_rel_min': 1.5, 'atr_percent_min': 0.75},
            'Short': {'ker_min': 0.45, 'zscore_max': -1.0, 'vol_rel_min': 1.5}},
    'AVAX': {'Long': {'ker_min': 0.45, 'vol_rel_min': 1.5, 'atr_percent_min': 0.75},
             'Short': {'ker_min': 0.45, 'zscore_max': -1.0, 'vol_rel_min': 1.5}},
    'MATIC': {'Long': {'ker_min': 0.40, 'vol_rel_min': 1.5, 'atr_percent_min': 0.70},
              'Short': {'ker_min': 0.40, 'zscore_max': -0.8, 'vol_rel_min': 1.5}},
    'LINK': {'Long': {'ker_min': 0.45, 'vol_rel_min': 1.5, 'atr_percent_min': 0.75},
             'Short': {'ker_min': 0.45, 'zscore_max': -1.0, 'vol_rel_min': 1.5}},
    'UNI': {'Long': {'ker_min': 0.40, 'vol_rel_min': 1.5, 'atr_percent_min': 0.70},
            'Short': {'ker_min': 0.40, 'zscore_max': -0.8, 'vol_rel_min': 1.5}},
}

# ---- Recuperación y reintentos ----
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_BACKOFF = 5
BACKOFF_BASE = 5
MAX_RETRIES_PER_ORDER = 3
ORDER_TIMEOUT = 15
LOCK_FILE = '.lock'
LOCK_TIMEOUT = 10
SYNC_TIME_ENABLED = True
MAX_CONSECUTIVE_ERRORS = 5
MAX_REPAIR_ATTEMPTS = 3

# ---- Control de Riesgo ----
MAX_DAILY_LOSS_PERCENT = 2.0
MAX_WEEKLY_LOSS_PERCENT = 4.0
MAX_OPEN_POSITIONS = 3

# ---- Backtesting (RÁPIDO) ----
BACKTEST_DAYS = 5
BACKTEST_FEE_MAKER = 0.0005
BACKTEST_FEE_TAKER = 0.0007
BACKTEST_SLIPPAGE = 0.0002

# ---- Logging ----
LOG_DIR = 'logs'
LOG_LEVEL = 'INFO'
LOG_CONSOLE = True
LOG_FILE = True
LOG_JSON = True
MAX_LOG_SIZE_MB = 10
MAX_LOG_FILES = 5

# ---- Modo demo ----
OKX_DEMO = True

# ============================================================
# MODO DE PRUEBA (VALIDACIÓN FUNCIONAL)
# ============================================================
TEST_MODE = False                  # Desactivado (producción)
TEST_IGNORE_FILTERS = True
TEST_SPEED_LEVEL = {"nivel": 6, "raw_min": 0.05, "roc_min": 0.01}
CYCLE_INTERVAL_TEST = 10

# ============================================================
# SELECCIÓN DE ESTRATEGIA (MULTIESTRATEGIA)
# ============================================================
ACTIVE_STRATEGY = 'production'     # 'production' | 'test_fast' | 'test_simple' | 'experimental'
STRATEGY_MODULES = {
    'production': 'strategy_production',
    'test_fast': 'strategy_test_fast',
    'test_simple': 'strategy_test_simple',
    'experimental': 'strategy_experimental',
}

# ============================================================
# VERIFICACIÓN DE CONFIGURACIÓN
# ============================================================
if __name__ == "__main__":
    required = [
        'SYMBOLS', 'TRADE_NOTIONAL', 'LEVERAGE',
        'TP_MULT', 'SL_MULT', 'ATR_PERIOD',
        'DEFAULT_SPEED_LEVEL', 'OPTIMIZED_LEVELS', 'PER_ASSET_CONFIG',
        'FILTERS',
        'MAX_REPAIR_ATTEMPTS', 'BACKOFF_BASE', 'SYNC_TIME_ENABLED',
        'BACKTEST_DAYS', 'LOG_DIR',
        'TEST_MODE', 'ACTIVE_STRATEGY', 'STRATEGY_MODULES'
    ]
    for var in required:
        assert var in globals(), f"❌ Falta: {var}"
        print(f"✅ {var}")
    print("✅ Configuración completa y correcta")
