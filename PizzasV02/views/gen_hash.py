import hashlib

def generar_hash_sha256(pin):
    """
    Convierte una cadena (el PIN) en su representación hash SHA256.
    Este es el mismo método que usa la aplicación en login_view.py.
    """
    # 1. Codificar el PIN a bytes UTF-8
    pin_bytes = pin.encode('utf-8')
    
    # 2. Calcular el hash SHA256
    hash_obj = hashlib.sha256(pin_bytes)
    
    # 3. Obtener la representación hexadecimal del hash
    hash_hex = hash_obj.hexdigest()
    
    return hash_hex

# --- Programa Principal ---
if __name__ == "__main__":
    print("--- Generador de Hashes SHA256 para PINES ---")
    print("Introduce el PIN numérico que deseas convertir (o escribe 'salir' para terminar).")
    
    while True:
        pin_ingresado = input("PIN a convertir: ")
        
        if pin_ingresado.lower() == 'salir':
            break
            
        if not pin_ingresado.isdigit():
            print("Error: Por favor, introduce solo números.")
            continue
            
        # Generamos el hash
        pin_cifrado = generar_hash_sha256(pin_ingresado)
        
        print("\n✅ ¡Hash generado con éxito!")
        print("------------------------------------------------------------------")
        print(f"   PIN Original: {pin_ingresado}")
        print(f"   Hash SHA256:  {pin_cifrado}")
        print("------------------------------------------------------------------")
        print("Copia y pega este hash en tu archivo 'config.json'.\n")

