import requests
from django.conf import settings

def notify_iot_server(action, device_data=None):
    SERVER_URL = "http://192.168.0.69:5000/toggle"
    
    try:
        if action == "add":
            response = requests.post(f"{SERVER_URL}/device", json={
                "id": device_data["id"],
                "type": device_data["type"],
                "action": "add"
            })
        elif action == "delete":
            response = requests.post(f"{SERVER_URL}/device", json={
                "id": device_data["id"],
                "action": "delete"
            })
        
        elif action == "toggle":
            toggle = "led 1" 
            if device_data["type"] == "Alarma":
                toggle = "buzzer"
            elif device_data["type"] == "Motor":
                toggle = "motor" 

            response = requests.post(f"{SERVER_URL}", data=f"toggle {toggle}")
        return response.status_code == 200
    except requests.RequestException:
        # Por ahora solo registramos el error pero no afectamos la operación
        return True