# Verified against live Uzbekistan Airways / O'zbekiston Temir Yo'llari booking
# backends (api.aerotur.aero top-airports and eticket.railway.uz station list).

FLIGHT_CITIES = [
    {"code": "TAS", "name": "Toshkent"},
    {"code": "MOW", "name": "Moskva"},
    {"code": "LED", "name": "Sankt-Peterburg"},
    {"code": "SKD", "name": "Samarqand"},
    {"code": "UGC", "name": "Urganch"},
    {"code": "KZN", "name": "Qozon"},
    {"code": "NMA", "name": "Namangan"},
    {"code": "BHK", "name": "Buxoro"},
    {"code": "FEG", "name": "Farg'ona"},
    {"code": "SVX", "name": "Yekaterinburg"},
    {"code": "OVB", "name": "Novosibirsk"},
    {"code": "AER", "name": "Sochi"},
    {"code": "IST", "name": "Istanbul"},
    {"code": "UFA", "name": "Ufa"},
    {"code": "NCU", "name": "Nukus"},
    {"code": "TMJ", "name": "Termiz"},
    {"code": "AZN", "name": "Andijon"},
    {"code": "DEL", "name": "Dehli"},
    {"code": "NYC", "name": "Nyu-York"},
]

TRAIN_STATIONS = [
    {"code": "2900000", "name": "Toshkent"},
    {"code": "2900700", "name": "Samarqand"},
    {"code": "2900800", "name": "Buxoro"},
    {"code": "2900172", "name": "Xiva"},
    {"code": "2900790", "name": "Urganch"},
    {"code": "2900970", "name": "Nukus"},
    {"code": "2900930", "name": "Navoiy"},
    {"code": "2900680", "name": "Andijon"},
    {"code": "2900750", "name": "Qarshi"},
    {"code": "2900720", "name": "Jizzax"},
    {"code": "2900255", "name": "Termiz"},
    {"code": "2900850", "name": "Guliston"},
    {"code": "2900880", "name": "Qo'qon"},
    {"code": "2900920", "name": "Marg'ilon"},
    {"code": "2900693", "name": "Pop"},
    {"code": "2900940", "name": "Namangan"},
]


def flight_city_name(code: str) -> str:
    for c in FLIGHT_CITIES:
        if c["code"] == code:
            return c["name"]
    return code


def train_station_name(code: str) -> str:
    for s in TRAIN_STATIONS:
        if s["code"] == code:
            return s["name"]
    return code
