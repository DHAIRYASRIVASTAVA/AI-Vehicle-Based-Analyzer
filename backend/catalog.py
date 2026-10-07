"""Approx. new-vehicle prices (INR) used as base for the price model.
Replace/extend with a real dataset (CarDekho / Kaggle) for production."""
CATALOG = {
    "Honda City": (1400000, "car"), "Maruti Swift": (750000, "car"),
    "Hyundai i20": (900000, "car"), "Hyundai Creta": (1500000, "car"),
    "Maruti Baleno": (870000, "car"), "Tata Nexon": (1100000, "car"),
    "Toyota Innova Crysta": (2200000, "car"), "Maruti Alto": (450000, "car"),
    "Mahindra Scorpio": (1700000, "car"), "Hyundai Verna": (1300000, "car"),
    "Royal Enfield Classic 350": (220000, "bike"), "Honda Activa 6G": (85000, "bike"),
    "Bajaj Pulsar 150": (125000, "bike"), "Hero Splendor Plus": (80000, "bike"),
    "TVS Apache RTR 160": (120000, "bike"), "Yamaha FZ-S": (125000, "bike"),
}
KM_PER_YEAR = {"car": 12000, "bike": 8000}
