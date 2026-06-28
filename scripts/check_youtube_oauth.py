import os
import sys
import requests

def main():
    print("--- Running YouTube OAuth Credentials Preflight Check ---")
    client_id = os.environ.get('YOUTUBE_CLIENT_ID')
    client_secret = os.environ.get('YOUTUBE_CLIENT_SECRET')
    refresh_token = os.environ.get('YOUTUBE_REFRESH_TOKEN')
    
    # Check presence
    has_client_id = bool(client_id and client_id.strip())
    has_client_secret = bool(client_secret and client_secret.strip())
    has_refresh_token = bool(refresh_token and refresh_token.strip())
    
    print(f"credentials_present: {has_client_id and has_client_secret and has_refresh_token}")
    print(f"YOUTUBE_CLIENT_ID present: {has_client_id}")
    print(f"YOUTUBE_CLIENT_SECRET present: {has_client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN present: {has_refresh_token}")
    
    if not (has_client_id and has_client_secret and has_refresh_token):
        print("Error: One or more YouTube credentials are empty or missing.")
        sys.exit(1)
        
    # Attempt token refresh
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        res = requests.post(token_url, data=token_data, timeout=15)
        print(f"token_endpoint_status: {res.status_code}")
        
        if res.status_code == 200:
            res_json = res.json()
            if 'access_token' in res_json:
                print("refresh_success: True")
                print("Preflight Check Passed successfully.")
                sys.exit(0)
            else:
                print("refresh_success: False")
                print("error_type: missing_access_token_in_response")
                sys.exit(1)
        else:
            print("refresh_success: False")
            try:
                err_json = res.json()
                err_type = err_json.get('error', 'unknown_error')
                err_desc = err_json.get('error_description', '')
                print(f"error_type: {err_type}")
                if err_desc:
                    # Mask client secret or client id if they appear in description
                    safe_desc = err_desc
                    if client_id and client_id in safe_desc:
                        safe_desc = safe_desc.replace(client_id, "[CLIENT_ID]")
                    if client_secret and client_secret in safe_desc:
                        safe_desc = safe_desc.replace(client_secret, "[CLIENT_SECRET]")
                    print(f"error_description: {safe_desc}")
            except Exception:
                print("error_type: http_error_non_json")
            sys.exit(1)
            
    except Exception as e:
        print("refresh_success: False")
        print(f"error_type: connection_exception ({type(e).__name__})")
        sys.exit(1)

if __name__ == '__main__':
    main()
