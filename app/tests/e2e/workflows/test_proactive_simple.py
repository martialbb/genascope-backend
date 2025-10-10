#!/usr/bin/env python3
import requests
import json

def test_proactive_chat():
    # Auth
    auth_data = {'username': 'admin@test.com', 'password': 'test123'}
    response = requests.post('http://localhost:8080/api/auth/token', data=auth_data)
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # Get patient and strategy
    patients_response = requests.get('http://localhost:8080/api/patients/', headers=headers)
    patient = patients_response.json()[0]

    strategies_response = requests.get('http://localhost:8080/api/v1/chat-configuration/strategies', headers=headers)
    strategy = strategies_response.json()[0]

    print('=== TESTING PROACTIVE AI CHAT ===')
    print(f'Patient: {patient["email"]}')
    print(f'Strategy: {strategy["name"]}')

    # Create session
    session_data = {
        'strategy_id': strategy['id'],
        'patient_id': patient['id'],
        'session_type': 'screening'
    }

    session_response = requests.post('http://localhost:8080/ai-chat/sessions', headers=headers, json=session_data)
    print(f'\nSession Status: {session_response.status_code}')

    if session_response.status_code == 200:
        session = session_response.json()
        print(f'Session ID: {session["id"]}')
        print(f'\nAI PROACTIVE MESSAGE:')
        print(f'"{session.get("initial_message", "[NO INITIAL MESSAGE!]")}"')
        
        # Test patient response
        patient_message = 'Yes, I have been having stomach pain and bloating'
        message_data = {'message': patient_message}
        
        message_response = requests.post(
            f'http://localhost:8080/ai-chat/sessions/{session["id"]}/messages',
            headers=headers,
            json=message_data
        )
        
        print(f'\nPATIENT: {patient_message}')
        
        if message_response.status_code == 200:
            ai_response = message_response.json()
            print(f'\nAI FOLLOW-UP: {ai_response.get("content", "No response")}')
        else:
            print(f'Message Error: {message_response.text}')
    else:
        print(f'Session Error: {session_response.text}')

if __name__ == '__main__':
    test_proactive_chat()
