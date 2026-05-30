from flask import Flask, render_template, request
import boto3
from pymongo import MongoClient
import os
import time
from dotenv import load_dotenv

# .env dosyasındaki gizli şifreleri ve anahtarları yükle
load_dotenv()

app = Flask(__name__)
# Videoların buluta gitmeden önce bilgisayarda 1-2 saniye duracağı geçici klasör
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ortam değişkenlerini (environment variables) çek
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_REGION') # us-east-2 (Ohio)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
MONGO_URI = os.getenv('MONGO_URI')

# 1. MongoDB Atlas Bağlantısı (N. Virginia'ya bağlanıyoruz)
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client['BulutProjesiDB']
    koleksiyon = db['VideoAnalizSonuclari']
    # Bağlantıyı test et
    mongo_client.admin.command('ping')
    print("MongoDB'ye başarıyla bağlanıldı!")
except Exception as e:
    print(f"MongoDB Bağlantı Hatası: {e}")

# 2. AWS İstemcilerini Ayarlama (Ohio'ya bağlanıyoruz)
s3_client = boto3.client('s3', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
rekognition = boto3.client('rekognition', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

# --- WEB SAYFALARI (ROUTE'LAR) ---

@app.route('/')
def index():
    # İlk açılışta video yükleme ekranını göster
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return "Lütfen bir video yükleyin", 400
    
    file = request.files['video']
    if file.filename == '':
        return "Dosya seçilmedi", 400

    # Videoyu bilgisayardaki 'uploads' klasörüne geçici olarak kaydet
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        # AŞAMA 1: Videoyu Ohio'daki S3'e Yükle
        print(f"\n[1] {file.filename} AWS S3'e yükleniyor...")
        s3_client.upload_file(file_path, BUCKET_NAME, file.filename)
        print("[1] S3'e yükleme başarılı!")
        
        # AŞAMA 2: Ohio'daki Rekognition ile Analizi Başlat
        print("[2] AWS Rekognition nesne analizi başlatılıyor...")
        response = rekognition.start_label_detection(
            Video={'S3Object': {'Bucket': BUCKET_NAME, 'Name': file.filename}},
            MinConfidence=75 # Sadece %75'ten emin olduğu nesneleri bul
        )
        job_id = response['JobId']

        # AŞAMA 3: İşlemin Bitmesini Bekle
        print("[3] Analiz sonuçları bekleniyor (Bu işlem videonun uzunluğuna göre biraz sürebilir)...")
        while True:
            result = rekognition.get_label_detection(JobId=job_id)
            status = result['JobStatus']
            
            if status == 'SUCCEEDED':
                print("\n[✓] Analiz tamamlandı! Sonuçlar veritabanına kaydediliyor...")
                
                # AWS'den gelen karmaşık JSON verisinin içinden sadece etiket isimlerini ayıkla
                bulunan_etiketler = list(set([label['Label']['Name'] for label in result['Labels']]))
                
                # AŞAMA 4: N. Virginia'daki MongoDB'ye Kaydet
                kayit_verisi = {
                    "dosya_adi": file.filename,
                    "bulunan_nesneler": bulunan_etiketler,
                    "islem_tarihi": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                koleksiyon.insert_one(kayit_verisi)
                print("[✓] Veriler MongoDB'ye başarıyla yazıldı!")
                
                # Bilgisayardaki geçici videoyu sil (Yer kaplamasın)
                os.remove(file_path)
                
                # İşlem bitince HTML sayfasını bulunan etiketlerle birlikte kullanıcıya göster
                return render_template('result.html', etiketler=bulunan_etiketler, dosya=file.filename)
                
            elif status == 'FAILED':
                os.remove(file_path)
                return "Video analizi AWS tarafında başarısız oldu."
            
            # Sistem 5 saniyede bir AWS'yi darlamasın diye bekleme süresi koyuyoruz
            time.sleep(5) 

    except Exception as e:
        return f"Bir hata oluştu: {str(e)}"

if __name__ == '__main__':
    # Uploads klasörü yoksa otomatik oluştur
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    print("\n--- Sistem Hazır! ---")
    print("Tarayıcınızı açın ve şu adrese gidin: http://127.0.0.1:5000\n")
    app.run(debug=True)