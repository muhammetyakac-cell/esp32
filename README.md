# DZY Panel (ESP32 Çoklu Müşteri Telemetri Yönetimi)

Bu repoda, ESP32 cihazı satan bir işletme için **tek panelden çoklu müşteri yönetimi** yaklaşımı uygulanmıştır:

- Admin panelinden yeni müşteri kullanıcıları oluşturulur.
- Her kullanıcıya özel `supabase_url` ve `supabase_anon_key` atanır.
- Kullanıcı giriş yaptığında dashboard yalnızca kendi Supabase projesinden veri çeker.
- ESP32 firmware'e müşteriye özel Supabase bilgileri gömülerek cihaz doğrudan müşterinin veritabanına log atar.

## Mimari

- **Control plane (bu web uygulaması):**
  - Admin girişi
  - Müşteri kullanıcı oluşturma
  - Kullanıcı kimlik doğrulama
  - Kullanıcıya özel Supabase bağlantı bilgileriyle telemetri okuma
- **Data plane (müşteri Supabase projesi):**
  - ESP32'nin yazdığı `telemetry` tablosu
  - Müşteri verisi izole (proje bazlı ayrım)

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

## Ortam değişkenleri

- `APP_SECRET_KEY`: Flask session secret
- `ADMIN_USERNAME`: Admin giriş kullanıcı adı
- `ADMIN_PASSWORD`: Admin giriş şifresi
- `DATABASE_PATH`: SQLite dosya yolu (default: `dzy_panel.db`)

## Akış

1. Admin `/login` üzerinden giriş yapar.
2. `/admin` sayfasından yeni kullanıcı oluşturur:
   - kullanıcı adı
   - başlangıç şifresi
   - müşteri adı
   - müşteriye özel Supabase URL
   - müşteriye özel anon key
3. Kullanıcı `/login` üzerinden giriş yaptığında `/dashboard` ekranında kendi Supabase verisini görür.
4. ESP32 cihazında `esp32/customer_config_template.h` içindeki alanlar müşteriye göre doldurulur ve firmware yüklenir.

## Güvenlik notları (üretime çıkmadan önce)

- HTTPS zorunlu kullanın.
- Admin ve kullanıcı şifre politikası + MFA ekleyin.
- Rate limit ve login deneme limiti ekleyin.
- Kayıt/denetim logları (audit log) ekleyin.
- Anon key yerine tercihen servis proxy modeli değerlendirin.
- Üretimde SQLite yerine PostgreSQL önerilir.

