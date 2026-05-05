# AutoLux

AutoLux енді production-қа бейімделген Flask қосымша:

- `PostgreSQL` арқылы автомобильдер сақталады
- `SQLAlchemy` модельдері қолданылады
- фотолар `Cloudinary` арқылы сервер жағында жүктеледі
- Render deploy кезінде фото да, база да жоғалмайды

## Негізгі модель

`Car` моделі:

- `id`
- `name`
- `price`
- `image_url`
- `description`

## Жоба құрылымы

```text
app/
  routes/
  static/
    admin/
    public/
  templates/
    admin/
    public/
  auth.py
  config.py
  db.py
  models.py
  services.py
app.py
server.py
render.yaml
requirements.txt
```

## Орнату

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`.env.example` файлын `.env` қылып көшіріп, мәндерін толтырыңыз.

## Environment Variables

- `DATABASE_URL`
- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD` немесе `ADMIN_PASSWORD_HASH`
- `CLOUD_NAME`
- `API_KEY`
- `API_SECRET`
- `CLOUDINARY_FOLDER` (міндетті емес)
- `MAX_CONTENT_LENGTH` (міндетті емес)

## Іске қосу

```powershell
python app.py
```

Адрестер:

- public: `http://localhost:5000/`
- admin: `http://localhost:5000/admin`

## Upload қалай жұмыс істейді

Admin форма `multipart/form-data` арқылы `/upload` endpoint-іне жібереді.

Backend:

1. файлды тексереді (`jpg`, `jpeg`, `png`)
2. файлды Cloudinary-ге жүктейді
3. `secure_url` алады
4. сол URL-ды PostgreSQL базаға `image_url` ретінде сақтайды

Локальды `storage/uploads` немесе `/static/uploads` қолданылмайды.

## Render Deploy

1. Render ішінде алдымен PostgreSQL service жасаңыз.
2. Оның connection string мәнін web service-тағы `DATABASE_URL` env var-ына қойыңыз.
3. Web service үшін мына env мәндерді толтырыңыз:

```text
DATABASE_URL=...
SECRET_KEY=...
ADMIN_USERNAME=...
ADMIN_PASSWORD_HASH=... немесе ADMIN_PASSWORD=...
CLOUD_NAME=...
API_KEY=...
API_SECRET=...
```

4. Build command:

```text
pip install -r requirements.txt
```

5. Start command:

```text
gunicorn server:app --bind 0.0.0.0:$PORT
```

6. Deploy жасаңыз.

Неге деректер жоғалмайды:

- PostgreSQL Render managed database болғандықтан deploy кезінде сақталады
- фото Cloudinary-де сақталады, сондықтан сервер filesystem-іне тәуелді емес

## HTML форма мысалы

Нақты жұмыс істейтін форма [app/templates/admin/index.html](app/templates/admin/index.html) ішінде бар.

Қысқа нұсқа:

```html
<form action="/upload" method="post" enctype="multipart/form-data">
  <input type="text" name="name" required>
  <input type="text" name="price" required>
  <textarea name="description" required></textarea>
  <input type="file" name="image" accept=".jpg,.jpeg,.png" required>
</form>
```

## Тест

```powershell
python -m unittest discover -s tests
```
