# n8n — aprobacion por Telegram antes de publicar

Este stack recibe el video que genera AutoShorts (el pipeline ya lo manda solo,
via el `webhook_url` que se configura en el preset), te lo pasa por Telegram
con botones Aprobar/Rechazar, y desde ahi sigue hacia YouTube cuando lo
apruebes. Va separado del stack de AutoShorts para que reiniciar uno no
reinicie el otro.

## 1. Configurar

```bash
cd /opt/autoshorts/n8n
cp .env.example .env
```

Genera la clave de cifrado tu mismo, para que no pase por ningun chat:

```bash
openssl rand -hex 32
```

Edita `n8n/.env` y pon esa clave en `N8N_ENCRYPTION_KEY`, y tu subdominio real
en `N8N_HOST` (por ejemplo `n8n.tudominio.com`).

```bash
nano /opt/autoshorts/n8n/.env
```

## 2. Levantar

```bash
cd /opt/autoshorts/n8n && sudo docker compose up -d
```

## 3. Nginx Proxy Manager — el paso que rompe esto si se salta

En NPM: **Add Proxy Host**

| Campo | Valor |
|---|---|
| Domain Names | tu `N8N_HOST`, ej `n8n.tudominio.com` |
| Forward Hostname/IP | la IP del servidor (`10.0.0.100`) si NPM corre en su propio contenedor; `127.0.0.1` si corre directo en el host |
| Forward Port | `5678` |
| Websockets Support | **activado** — n8n lo necesita para el editor en vivo |
| SSL | pide un certificado Let's Encrypt nuevo, forzar HTTPS |

**Y en la pestaña Advanced de ese mismo Proxy Host, añade:**

```
client_max_body_size 128M;
```

Esto no es opcional. El webhook de AutoShorts manda el video entero en el
cuerpo del POST. Nginx por defecto solo deja pasar 1 MB — sin esta linea,
todo video real se rechaza con un 413 antes de llegar siquiera a n8n, y el
unico rastro es un timeout o un error generico en el log del pipeline.

Confirma que Cloudflare esta en modo proxy (nube naranja) para ese subdominio
si quieres que el certificado de NPM sea el que sirve; si esta en modo DNS
only (nube gris), Cloudflare no interviene y NPM sirve su certificado
directamente igual.

## 4. Primer arranque de n8n

Abre `https://TU_N8N_HOST/` — n8n pide crear la cuenta de owner (email y
contrasena) la primera vez. Es tuya, no pasa por aqui.

## 5. Credencial de Telegram

Dentro de n8n: **Credentials → New → Telegram API**, pega el token de tu bot
(el que ya tienes de @BotFather). n8n lo guarda cifrado con
`N8N_ENCRYPTION_KEY`; no vuelve a salir en texto plano en ningun sitio.

## 6. El workflow

A partir de aqui lo construyo contigo dentro del editor de n8n, en vivo, en
vez de darte un JSON para importar a ciegas — un flujo con botones de Telegram
tiene piezas (teclado inline, nodo Wait, credenciales) que solo se confirman
bien probandolas contra tu instancia real.

Cuando confirmes que `https://TU_N8N_HOST/` carga, seguimos desde ahi.

## 7. Conectar AutoShorts a este webhook

Cuando el workflow este creado y tengas la URL del nodo Webhook, se pega en el
preset del worker:

```bash
sed -i 's|"webhook_url": *""|"webhook_url": "https://TU_N8N_HOST/webhook/LA-RUTA-QUE-TE-DE-N8N"|' /opt/autoshorts/preset.ejemplo.json
sudo docker cp /opt/autoshorts/preset.ejemplo.json autoshorts-app:/datos/preset.json
```

A partir de ese momento, cada video que genere el worker (automatico o de
prueba con `--uno`) llega a tu Telegram antes de darse por publicado.

## Memoria

n8n en reposo pesa poco. El tope de 512 MB en su compose evita que una
ejecucion pesada le quite memoria al worker cuando este renderizando a la vez
— algo que solo puede coincidir en el instante justo en que un render termina
y dispara el webhook.
