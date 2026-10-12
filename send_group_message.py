import requests

# 1. API-adressen till din Docker-container
API_URL = "http://localhost:8080/v2/send"

# 2. Ditt registrerade telefonnummer eller UUID i Signal
SENDER_ID = ""  # Byt ut mot ditt nummer (med landskod +46) eller ditt UUID

# 3. Klistra in Group ID du hämtade tidigare (börjar oftast på group...)
GROUP_ID = ""

# 4. Meddelandet du vill skicka
MESSAGE = "test message from python with new phone"

# Skapa anropets innehåll
payload = {
    "message": MESSAGE,
    "number": SENDER_ID,
    "recipients": [GROUP_ID],  # Grupp-ID placeras i recipients-listan
}

try:
    response = requests.post(API_URL, json=payload)

    if response.status_code == 201:
        print("Framgång! Meddelandet har skickats till gruppen.")
    else:
        print(f"Ett fel uppstod ({response.status_code}): {response.text}")

except requests.exceptions.ConnectionError:
    print(
        "Kunde inte ansluta till Docker-containern. Kontrollera att den körs på port 8080."
    )
