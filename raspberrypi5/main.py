from flask import Flask, request, jsonify
import RPi.GPIO as GPIO
from time import sleep

app = Flask(__name__)

# Configuración de GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Definición de pines
PINS = {
    'LED': {
        'BLUE': 2,
        'YELLOW': 3,
        'RED': 4,
        'WHITE': 17,
    },
    'BUZZER': 27,
    'SERVO': 22
}

# Estado de los dispositivos
devices = {}
available_leds = ['BLUE', 'YELLOW', 'RED', 'WHITE']
servo_position = 0  # 0 para posición inicial, 1 para 45 grados

# Configuración inicial de los pines
for pin in PINS['LED'].values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

GPIO.setup(PINS['BUZZER'], GPIO.OUT)
GPIO.output(PINS['BUZZER'], GPIO.LOW)

# Configuración del servo
servo_pwm = GPIO.PWM(PINS['SERVO'], 50)  # 50Hz
servo_pwm.start(0)

def get_available_led():
    if not available_leds:
        return None
    return available_leds[0]

def move_servo():
    global servo_position
    if servo_position == 0:
        servo_pwm.ChangeDutyCycle(7.5)  # 45 grados
        servo_position = 1
    else:
        servo_pwm.ChangeDutyCycle(2.5)  # 0 grados
        servo_position = 0
    sleep(0.5)
    servo_pwm.ChangeDutyCycle(0)  # Detiene el pulso para evitar vibraciones

@app.route('/device', methods=['POST'])
def handle_device():
    data = request.get_json()
    device_id = data.get('id')
    action = data.get('action')

    if action == 'add':
        device_type = data.get('type')
        
        if device_type == 'Luz':
            led = get_available_led()
            if not led:
                return jsonify({'error': 'No hay LEDs disponibles'}), 400
            devices[device_id] = {'type': 'Luz', 'pin': PINS['LED'][led], 'led_color': led}
            available_leds.remove(led)
            
        elif device_type == 'Alarma':
            if any(d.get('type') == 'Alarma' for d in devices.values()):
                return jsonify({'error': 'Buzzer ya está en uso'}), 400
            devices[device_id] = {'type': 'Alarma', 'pin': PINS['BUZZER']}
            
        elif device_type == 'Motor':
            if any(d.get('type') == 'Motor' for d in devices.values()):
                return jsonify({'error': 'Servo ya está en uso'}), 400
            devices[device_id] = {'type': 'Motor', 'pin': PINS['SERVO']}
        
        return jsonify({'message': 'Dispositivo agregado exitosamente'})

    elif action == 'toggle':
        if device_id not in devices:
            return jsonify({'error': 'Dispositivo no encontrado'}), 404
            
        device = devices[device_id]
        if device['type'] in ['Luz', 'Alarma']:
            current_state = GPIO.input(device['pin'])
            GPIO.output(device['pin'], not current_state)
        elif device['type'] == 'Motor':
            move_servo()
            
        return jsonify({'message': 'Estado cambiado exitosamente'})

    elif action == 'delete':
        if device_id not in devices:
            return jsonify({'error': 'Dispositivo no encontrado'}), 404
            
        device = devices[device_id]
        if device['type'] == 'Luz':
            available_leds.append(device['led_color'])
            GPIO.output(device['pin'], GPIO.LOW)
        elif device['type'] == 'Alarma':
            GPIO.output(device['pin'], GPIO.LOW)
        elif device['type'] == 'Motor':
            servo_pwm.ChangeDutyCycle(2.5)  # Regresa a 0 grados
            sleep(0.5)
            servo_pwm.ChangeDutyCycle(0)
            
        del devices[device_id]
        return jsonify({'message': 'Dispositivo eliminado exitosamente'})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        servo_pwm.stop()
        GPIO.cleanup()
