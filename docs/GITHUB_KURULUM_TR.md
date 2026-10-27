# RegressionProof: GitHub'a yayımlama ve yerel kullanım

Bu kılavuz Windows 10/11 ve PowerShell kullanan geliştiriciler içindir. Projenin kodu hazırdır; GitHub üzerinde yeni depo açılması hesap sahibinin kendi oturumunda yapılmalıdır. Repo otomatik oluşturulduğu veya GitHub'a dosya gönderildiği iddia edilmez.

## 1. Depo oluştur

1. https://github.com/new adresine gir.
2. Owner: `rahokul55` (değişmişse GitHub hesabını seç).
3. Repository name: `regressionproof`.
4. Description: `Evidence-based test regression comparison across Git revisions.`
5. Visibility: **Public**.
6. **Add a README file**, **Add .gitignore** ve **Choose a license** seçimlerini boş bırak; proje bunları içeriyor.
7. Create repository ile boş depoyu oluştur.

## 2. Projeyi gönder

ZIP dosyasını aç ve `regressionproof` klasöründeki bir PowerShell penceresinde şu komutu çalıştır:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish.ps1
```

Betik `git init`, `git add`, `git commit` ve `git push` uygular. Git ismini ve e-postanı henüz ayarlamadıysan önce:

```powershell
git config --global user.name "GITHUB PROFIL ADIN"
git config --global user.email "GITHUB HESABINDA DOGRULANMIS E-POSTA"
```

Alternatif olarak, hiçbir betik kullanmadan:

```powershell
git init
git branch -M main
git add .
git commit -m "Initial RegressionProof source release"
git remote add origin https://github.com/rahokul55/repocare-oss.git
git push -u origin main
```

Kodu gönderdikten sonra `https://github.com/rahokul55/repocare-oss` aç. GitHub → Actions → CI iş akışını kontrol et. Bunun başarılı olduğunu doğrulamadan projeyi "CI passing" olarak tanıtma.

## 3. Bilgisayarda kur

```powershell
python -m pip install -e .
python -m pytest -q
regressionproof --version
regressionproof compare --base-xml examples/base.xml --head-xml examples/head.xml --no-fail
```

Rapor `.regressionproof/report.md` altında oluşur. Entegrasyon testi çalıştırmak ve kod kalite kontrolü yapmak için `python -m pip install -e ".[dev]"` kullan.

## 4. Kendi projenin iki commit'ini kontrol et

Bunun için hedef projede Python ve pytest kurulu olmalı. Hedef deponun klasörüne geçerek:

```powershell
regressionproof check --base main --head HEAD --test-command "{python} -m pytest -q --junitxml={report}" --runs 2
```

Python dışındaki test sistemleri de JUnit XML çıktısı verebiliyorsa `--test-command` ile kullanılabilir. Depo içindeki test kodu çalıştırıldığı için bilinmeyen kişilerin PR'larını kişisel bilgisayarda yürütme.

## 5. Açık kaynak bakım adımları

- GitHub Settings → Security altında Private vulnerability reporting'i etkinleştir.
- Issues ve Discussions kullanarak geri bildirim al.
- Releases bölümünde ancak sürümü doğruladıktan sonra `v0.1.0` etiketi ile bir sürüm yayımla.
- README'de gerçek kullanıcı sayısını ve performans verisini yalnızca ölçülmüşse belirt.
- PR'larda `CI` sonuçlarını kontrol et; korumalı `main` dalı ayarlarını düşün.
- Gerçek hata bildirimlerini ve katkıları takip ederek sınıflandırma kurallarını geliştir.

## 6. Codex for Open Source başvurusu

Başvuruda `primary maintainer` rolünü ancak bu repoyu gerçekten bakımını üstleniyorsan belirt. Yeni projeyi yaygın kullanılan bir altyapıymış gibi sunma. Yıldız/indirme sayısı sıfırsa doğru sayıyı kullan; ilk aşamada projenin hangi somut problemi çözdüğüne ve neyi kanıtlayabildiğine odaklan. Yeni bir proje programın seçilme önceliklerini karşılamayabilir.
