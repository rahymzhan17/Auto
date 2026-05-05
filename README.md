# AutoLux

Кәсіби құрылымға келтірілген автосалон жобасы. Енді жоба `Flask app factory` үлгісімен ұйымдастырылған, front/admin активтері бөлек папкаларда сақталады, ал база мен жүктелген файлдар жеке каталогтарға шығарылған.

## Құрылым

```text
app/
  routes/
  static/
    admin/
    public/
  templates/
    admin/
    public/
data/
storage/uploads/
tests/
server.py
```

## Негізгі жақсартулар

- backend модульдерге бөлінді: `config`, `db`, `auth`, `services`, `routes`
- public және admin беттері Flask арқылы бір origin-нен беріледі
- hardcoded `localhost` адресі алынып тасталды
- админ логині `.env` арқылы басқарылады
- public/admin рендерлеуде мәтіндер escape жасалады
- form validation және қате хабарламалары жақсарды
- public detail route енді жасырын машиналарды қайтармайды
- файл жүктеу өлшемі мен форматтары тексеріледі

## Іске қосу

1. Виртуалды орта құрыңыз және тәуелділіктерді орнатыңыз:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. `.env.example` файлын `.env` қылып көшіріп, мәндерін толтырыңыз.

3. Қосыңыз:

```powershell
python server.py
```

4. Сайт:

- public: `http://localhost:5000/`
- admin: `http://localhost:5000/admin`

## Render-ге шығару

Бұл жобаға қазір ең оңай жолдың бірі - Render.

Неге дәл осы нұсқа:

- Flask жобасын ресми түрде қолдайды
- custom domain пен HTTPS автоматты түрде беріледі
- persistent disk қосуға болады, бұл `SQLite` пен `uploads` үшін маңызды

Render құжаттары:

- Flask deploy: https://render.com/docs/deploy-flask
- Persistent disk: https://render.com/docs/disks
- Custom domain: https://render.com/docs/custom-domains
- Blueprint / `render.yaml`: https://render.com/docs/blueprint-spec

Қадамдар:

1. Жобаны GitHub-қа жүктеңіз.
2. Render ішінде `New +` -> `Blueprint` немесе `Web Service` таңдаңыз.
3. Репозиторийді қосыңыз.
4. Егер `render.yaml` арқылы ашсаңыз, сервис конфигі автоматты оқылады.
5. Render сізден мына құпия мәндерді сұрайды:
   - `ADMIN_USERNAME`
   - `ADMIN_PASSWORD`
6. `JWT_SECRET` автоматты түрде генерацияланады.
7. Deploy біткен соң сізге `.onrender.com` адресі беріледі.
8. Қаласаңыз кейін custom domain байлайсыз.

Ескерту:

- Render-дегі root filesystem әдетте уақытша, сондықтан бұл жоба үшін persistent disk міндетті.
- Дискі бар сервис multi-instance scale жасамайды және deploy кезінде қысқа downtime болуы мүмкін.
- Бұл жоба үшін ол қалыпты, себебі қазір `SQLite + local uploads` архитектурасы қолданылып тұр.

## Тест

```powershell
python -m unittest discover -s tests
```

## Ескерту

- production-та `ADMIN_PASSWORD_HASH` қолданған дұрыс
- `data/` және `storage/uploads/` git-ке қоспау ұсынылады
