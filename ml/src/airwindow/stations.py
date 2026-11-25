"""CAMS station metadata.

Coordinates are approximate site locations (city/landmark level, roughly
within 2 km). They are good enough for matching to a ~10 km weather grid and
for showing a pin on a map; they are not surveyed sensor positions.
"""
STATIONS = {
    "dhk_barc":       {"name": "Dhaka – BARC, Farmgate", "name_bn": "ঢাকা – বিএআরসি, ফার্মগেট", "city": "Dhaka", "lat": 23.759, "lon": 90.389},
    "dhk_darussalam": {"name": "Dhaka – Darussalam", "name_bn": "ঢাকা – দারুস সালাম", "city": "Dhaka", "lat": 23.781, "lon": 90.356},
    "dhk_doe":        {"name": "Dhaka – DoE, Agargaon", "name_bn": "ঢাকা – পরিবেশ অধিদপ্তর, আগারগাঁও", "city": "Dhaka", "lat": 23.778, "lon": 90.379},
    "dhk_sangsad":    {"name": "Dhaka – Sangsad Bhaban", "name_bn": "ঢাকা – সংসদ ভবন", "city": "Dhaka", "lat": 23.762, "lon": 90.378},
    "gazipur":        {"name": "Gazipur", "name_bn": "গাজীপুর", "city": "Gazipur", "lat": 23.994, "lon": 90.420},
    "narayanganj":    {"name": "Narayanganj", "name_bn": "নারায়ণগঞ্জ", "city": "Narayanganj", "lat": 23.631, "lon": 90.508},
    "savar":          {"name": "Savar", "name_bn": "সাভার", "city": "Savar", "lat": 23.858, "lon": 90.267},
    "narsingdi":      {"name": "Narsingdi", "name_bn": "নরসিংদী", "city": "Narsingdi", "lat": 23.921, "lon": 90.717},
    "ctg_agrabad":    {"name": "Chattogram – Agrabad", "name_bn": "চট্টগ্রাম – আগ্রাবাদ", "city": "Chattogram", "lat": 22.323, "lon": 91.812},
    "ctg_tv":         {"name": "Chattogram – TV Station, Khulshi", "name_bn": "চট্টগ্রাম – টিভি স্টেশন, খুলশী", "city": "Chattogram", "lat": 22.356, "lon": 91.807},
    "rajshahi":       {"name": "Rajshahi", "name_bn": "রাজশাহী", "city": "Rajshahi", "lat": 24.369, "lon": 88.625},
    "khulna":         {"name": "Khulna", "name_bn": "খুলনা", "city": "Khulna", "lat": 22.816, "lon": 89.565},
    "sylhet":         {"name": "Sylhet", "name_bn": "সিলেট", "city": "Sylhet", "lat": 24.889, "lon": 91.867},
    "barishal":       {"name": "Barishal", "name_bn": "বরিশাল", "city": "Barishal", "lat": 22.700, "lon": 90.365},
    "mymensingh":     {"name": "Mymensingh", "name_bn": "ময়মনসিংহ", "city": "Mymensingh", "lat": 24.757, "lon": 90.408},
    "cumilla":        {"name": "Cumilla", "name_bn": "কুমিল্লা", "city": "Cumilla", "lat": 23.461, "lon": 91.180},
    "rangpur":        {"name": "Rangpur", "name_bn": "রংপুর", "city": "Rangpur", "lat": 25.746, "lon": 89.250},
}
