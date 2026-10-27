# RegressionProof — GitHub ve Windows kullanım kılavuzu

**Mevcut depo:** https://github.com/rahokul55/repocare-oss

Bu depo zaten herkese açık olarak oluşturuldu ve kaynak kodları yüklendi. Yeni depo açman gerekmez. GitHub Actions çalıştırmalarının sonuçlarını ayrıca kontrol etmek gerekir.

## 1. Bilgisayarına kur

Windows PowerShell'de:

```powershell
git clone https://github.com/rahokul55/repocare-oss.git
cd repocare-oss
python -m pip install -e ".[dev]"
python -m pytest -q
regressionproof --version
```

## 2. Test raporlarını karşılaştır

```powershell
regressionproof compare --base-xml examples/base.xml --head-xml examples/head.xml --no-fail
```

`.regressionproof` klasöründe JSON, Markdown ve `report.html` dosyaları oluşur. HTML raporunu çift tıklayarak açabilirsin.

## 3. Gerçek Git sürümlerini incele

Testleri JUnit XML üretebilen başka bir Git projesinde:

```powershell
regressionproof check --base main --head HEAD --test-command "{python} -m pytest -q --junitxml={report}" --runs 3
```

`--runs 3` komutu testi her sürümde üç kez çalıştırır. Uygulamanın beklenen test bağımlılıklarının ortamında kurulu olması gerekir. Test kodu dış kaynaklardan geliyorsa onu yalnızca yetkisiz, geçici CI sisteminde çalıştır.

## 4. GitHub CI

https://github.com/rahokul55/repocare-oss/actions adresini aç. **CI** iş akışında Python sürüm matrisini kontrol et. Gerekirse **Run workflow** kullan. Yeşil CI sonucunu gerçekten görmeden README veya başvuruda geçtiğini iddia etme.

Bir başka projede kullanım örneği: [`examples/github-actions.yml`](../examples/github-actions.yml). Bağımlılığı güvenilir bir commit SHA'sına sabitle ve proje test bağımlılıklarını kur.

## 5. Projeyi sürdürülebilir tut

- GitHub Issues üzerinden gerçek hata bildirimlerini takip et; rapor dosyalarında kimlik bilgileri bulunmamasına dikkat et.
- Private vulnerability reporting ayarını etkinleştir.
- Yenilikleri ayrı PR'lar ve çalışan CI ile incele; `main` için korumalı dal kuralı düşün.
- Sürümü ancak test, paketleme ve güvenlik kontrolleri tamamlandıktan sonra GitHub Releases üzerinden yayımla.
- Başvuruda kullanıcısı veya indirmesi kanıtlanmayan sayıları uydurma.
