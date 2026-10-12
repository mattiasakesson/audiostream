# Signal Group Messaging via Docker API

This project provides a clean setup for sending automated text messages to a Signal group using Python and the `signal-cli-rest-api` Docker container.

---

## 1. Start the Signal CLI Docker Container

Run the following command in your terminal to download the image, launch the container in JSON-RPC mode, and persist the account configuration locally:

```bash
docker run -d \
  --name signal-cli-rest-api \
  -p 8080:8080 \
  -v $(pwd)/signal-cli-config:/home/cli/.local/share/signal-cli \
  -e MODE=json-rpc \
  bbernhard/signal-cli-rest-api:latest
```

**Verification:**
Run `docker ps` to verify that the container `signal-cli-rest-api` status is `Up`.

---

## 2. Link Your Signal Account (QR Code)

Linking your existing Signal account as a secondary device is the easiest method (no SMS required):

1. Open your browser and go to: `http://localhost:8080/v1/qrcodelink?device_name=python-script`
2. Open the **Signal** app on your phone.
3. Navigate to **Settings** $\rightarrow$ **Linked Devices**.
4. Scan the QR code displayed in your browser.

---

## 3. Retrieve Your SENDER_ID and Group ID

Once linked, retrieve your group details by running the following command in your terminal (replace `+46XXXXXXXXX` with your registered phone number including the country code):

```bash
curl -s http://localhost:8080/v1/groups/+46XXXXXXXXX
```

Look through the JSON response to find your target group's ID (e.g., `group.Zm9vYmFy...`).

---

## 4. Run the Python Script

Configure `send_group_message.py` with your `SENDER_ID` and `GROUP_ID`, then execute the script:

```bash
python3 send_group_message.py
```

---

