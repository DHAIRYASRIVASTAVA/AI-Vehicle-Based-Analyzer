"""Known models with approx. new (ex-showroom) price in INR. Users can also type ANY model;
for unknown ones the base price comes from the optional 'new price' field or a per-type default."""
CATALOG = {
    # cars
    "Honda City": (1400000, "car"), "Maruti Swift": (750000, "car"), "Maruti Wagon R": (600000, "car"),
    "Maruti Alto": (450000, "car"), "Maruti Baleno": (870000, "car"), "Maruti Brezza": (1000000, "car"),
    "Maruti Ertiga": (1000000, "car"), "Hyundai i20": (900000, "car"), "Hyundai Venue": (1000000, "car"),
    "Hyundai Creta": (1500000, "car"), "Hyundai Verna": (1300000, "car"), "Tata Punch": (700000, "car"),
    "Tata Nexon": (1100000, "car"), "Kia Seltos": (1300000, "car"), "Mahindra Scorpio": (1700000, "car"),
    "Toyota Innova Crysta": (2200000, "car"), "Toyota Fortuner": (3800000, "car"),
    # bikes
    "Royal Enfield Classic 350": (220000, "bike"), "Bajaj Pulsar 150": (125000, "bike"),
    "Hero Splendor Plus": (80000, "bike"), "Honda Shine": (85000, "bike"),
    "TVS Apache RTR 160": (120000, "bike"), "Yamaha FZ-S": (125000, "bike"), "KTM Duke 200": (200000, "bike"),
    # scooters
    "Honda Activa 6G": (85000, "scooter"), "TVS Jupiter": (80000, "scooter"),
    "Suzuki Access 125": (85000, "scooter"), "TVS NTorq 125": (90000, "scooter"),
}
KM_PER_YEAR = {"car": 12000, "bike": 8000, "scooter": 6000}
DEFAULT_BASE = {"car": 900000, "bike": 120000, "scooter": 90000}
KINDS = ["car", "bike", "scooter"]


def names_for(kind):
    return [n for n, (_, k) in CATALOG.items() if k == kind]


def resolve(name, kind, new_price=None):
    """-> (base_price, kind). Known model overrides kind; custom model uses new_price or default."""
    key = (name or "").strip().lower()
    base = None
    for n, (p, k) in CATALOG.items():
        if n.lower() == key:
            base, kind = p, k
            break
    if base is None:
        base = DEFAULT_BASE[kind]
    if new_price and float(new_price) >= 10000:
        base = float(new_price)
    return float(base), kind
