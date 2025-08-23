#!/usr/bin/env python3
"""Script temporaire pour récupérer la clé API Keepa"""
import keyring
import sys

def main():
    # Essayons différentes variations de nom
    keepa_key_variations = ['KEEPA_API_KEY', 'keepa_api_key', 'Keepa_API_Key']
    
    keepa_api_key = None
    found_key_name = None
    
    for key_name in keepa_key_variations:
        try:
            key = keyring.get_password('memex', key_name)
            if key and key.strip():
                keepa_api_key = key.strip()
                found_key_name = key_name
                print(f'✅ Clé API Keepa récupérée avec le nom : {key_name}')
                print(f'Clé commence par : {key[:8]}...')
                break
        except Exception as e:
            continue
    
    if not keepa_api_key:
        # Listons tous les secrets disponibles  
        try:
            secrets_list = keyring.get_password('memex', 'secrets')
            print('Secrets disponibles dans Memex :')
            print(secrets_list)
        except Exception as e:
            print(f'Impossible de lister les secrets : {e}')
            print('Suggestion : Ajouter KEEPA_API_KEY via l\'interface Memex')
            sys.exit(1)
    
    # Retournons la clé pour utilisation
    return keepa_api_key, found_key_name

if __name__ == "__main__":
    key, name = main()
    print(f"KEY_FOUND:{name}")
    print(f"KEY_VALUE:{key}")