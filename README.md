# BLM3522 Ders Projesi Akıllı Video Analiz Sistemi

Bu proje, yerel ortamdan yüklenen video dosyalarının bulut depolama katmanına aktarılarak AWS Rekognition API'leri aracılığıyla makine öğrenmesi destekli nesne tanıma işlemlerinden geçirilmesini ve elde edilen verilerin NoSQL mimarisinde saklanmasını sağlayan multi-region bir bulut bilişim uygulamasıdır.

## Mimari ve Çalışma Mantığı

- **Geliştirme Ortamı:** Python / Flask
- **Dosya Depolama (S3):** AWS Ohio (`us-east-2`) bölgesinde izole ve dış dünyaya kapalı bir S3 Bucket üzerinde videolar barındırılır.
- **Video Analizi (Rekognition):** S3'e yüklenen videolar %75 güven eşiğiyle asenkron olarak işlenir. Nesne etiketleri kare kare analiz edilir.
- **Veri Filtreleme (Deduplication):** AWS Rekognition'dan dönen tekrarlı nesne etiketleri, Python `set()` veri yapısı kullanılarak tekilleştirilir.
- **Bulut Veritabanı (MongoDB Atlas):** Filtrelenmiş eşsiz nesne etiketleri, AWS N. Virginia (`us-east-1`) bölgesindeki döküman tabanlı NoSQL veritabanına JSON formatında asenkron olarak kaydedilir.
- **Güvenlik Sıkılaştırması:** AWS Access/Secret Key ve MongoDB URI bağlantı bilgileri kaynak koda gömülmemiş, `.env` çevresel değişkenler kasasıyla sistem güvenliği sağlanmıştır.

## Proje Yapısı

```text
bulut_projesi/
├── templates/
│   ├── index.html        # Video yükleme arayüzü
│   └── result.html       # Analiz sonuçları ekranı
├── app.py                # Ana Flask backend kodu
├── requirements.txt      # Gerekli bağımlılıklar listesi
└── .gitignore            # Hassas veri koruma filtresi
```

## Kurulum ve Çalıştırma

1. Proje bağımlılıklarını kurun:
   ```bash
   pip install -r requirements.txt
   ```

2. Ana dizinde bir `.env` dosyası oluşturup bulut bilgilerinizi ekleyin:
   ```text
   AWS_ACCESS_KEY_ID=yerel_anahtar_id
   AWS_SECRET_ACCESS_KEY=yerel_gizli_anahtar
   AWS_REGION=us-east-2
   S3_BUCKET_NAME=bucket_adiniz
   MONGO_URI=mongodb+srv://...
   ```

3. Uygulamayı başlatın:
   ```bash
   python app.py
   ```
4. Tarayıcınızdan `http://127.0.0.1:5000` adresine gidin.

## 🎬 Proje Sunumu ve Belgeler

- **Proje Videosu:** https://drive.google.com/drive/u/0/folders/1WNYOpuxZn-Ga60_xAiZYIOVon6rZ9hwY
