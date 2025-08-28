from datetime import date

mock_permits = [
    {
        "id": 1,
        "company_name": "PT. Contoh Satu",
        "permit_type": "Izin Lingkungan",
        "status": "Aktif",
        "issued_date": date(2023, 1, 15),
        "expired_date": date(2026, 1, 14)
    },
    {
        "id": 2,
        "company_name": "PT. Contoh Dua",
        "permit_type": "Izin Limbah",
        "status": "Tidak Aktif",
        "issued_date": date(2020, 6, 1),
        "expired_date": date(2025, 5, 31)
    }
]
