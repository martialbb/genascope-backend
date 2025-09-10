#!/usr/bin/env python3
"""
Test script for proactive AI chat functionality.

This demonstrates how the AI chat system should proactively initiate conversations
with patients based on chat strategies and knowledge sources.
"""
import requests
import json
import sys

def test_proactive_chat():
    """Test the proactive AI chat system."""
    base_url = "http://localhost:8080"
    
    # Step 1: Authenticate
    print("=== AUTHENTICATION ===")
    auth_data = {'username': 'admin@test.com', 'password': 'test123'}
    response = requests.post(f"{base_url}/api/auth/token", data=auth_data)
    
    if response.status_code != 200:
        print(f"Authentication failed: {response.text}")
        return False
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print("✓ Authentication successful")
    
    # Step 2: Get available patients
    print("\n=== GETTING PATIENTS ===")
    patients_response = requests.get(f"{base_url}/api/patients/", headers=headers)
    
    if patients_response.status_code != 200:
        print(f"Failed to get patients: {patients_response.text}")
        return False
    
    patients = patients_response.json()
    if not patients:
        print("No patients found")
        return False
    
    patient = patients[0]
    print(f"✓ Using patient: {patient['email']} (ID: {patient['id'][:8]}...)")
    
    # Step 3: Get available chat strategies
    print("\n=== GETTING CHAT STRATEGIES ===")
    strategies_response = requests.get(f"{base_url}/api/v1/chat-configuration/strategies", headers=headers)
    
    if strategies_response.status_code != 200:
        print(f"Failed to get strategies: {strategies_response.text}")
        return False
    
    strategies = strategies_response.json()
    if not strategies:
        print("No strategies found")
        return False
    
    strategy = strategies[0]
    print(f"✓ Using strategy: {strategy['name']}")
    print(f"  Description: {strategy.get('description', 'No description')}")
    print(f"  Type: {strategy.get('strategy_type', 'Unknown')}")
    
    # Step 4: Create AI chat session - AI should initiate proactively
    print("\n=== CREATING PROACTIVE CHAT SESSION ===")
    session_data = {
        'strategy_id': strategy['id'],
        'patient_id': patient['id'],
        'session_type': 'screening'
    }
    
    session_response = requests.post(f"{base_url}/ai-chat/sessions", headers=headers, json=session_data)
    
    if session_response.status_code != 200:
        print(f"Failed to create session: {session_response.text}")
        return False
    
    session = session_response.json()
    session_id = session['session_id']
    initial_message = session.get('initial_message')
    
    print(f"✓ Session created: {session_id}")
    
    if initial_message:
        print(f"🤖 AI INITIATED CONVERSATION:")
        print(f"   '{initial_message}'")
        print("✓ PROACTIVE FUNCTIONALITY WORKING!")
    else:
        print("❌ NO INITIAL MESSAGE - AI DID NOT INITIATE PROACTIVELY")
        print("   This indicates the proactive functionality needs to be implemented")
    
    # Step 5: Patient responds to AI's initial question
    print("\n=== PATIENT RESPONSE TO AI ===")
    patient_message = "Hello, I'm ready to answer your questions about my health."
    
    message_data = {'message': patient_message}
    message_response = requests.post(
        f"{base_url}/ai-chat/sessions/{session_id}/messages",
        headers=headers,
        json=message_data
    )
    
    if message_response.status_code != 200:
        print(f"Failed to send message: {message_response.text}")
        return False
    
    ai_response = message_response.json()
    
    print(f"👤 Patient: '{patient_message}'")
    print(f"🤖 AI Response: '{ai_response.get('response', 'No response')}'")
    
    # Check if response is from real AI or fallback
    metadata = ai_response.get('metadata', {})
    ai_model = metadata.get('model', 'Unknown')
    tokens_used = metadata.get('tokens_used', 0)
    
    print(f"\n=== AI RESPONSE ANALYSIS ===")
    print(f"Model used: {ai_model}")
    print(f"Tokens used: {tokens_used}")
    
    if ai_model != 'Unknown' and tokens_used > 0:
        print("✓ REAL AI INTEGRATION WORKING!")
    else:
        print("❌ USING FALLBACK/MOCK RESPONSES")
        print("   Real OpenAI integration needs to be activated")
    
    # Step 6: Test follow-up questions for criteria determination
    print("\n=== TESTING FOLLOW-UP QUESTIONS ===")
    follow_up_message = "I have been experiencing some stomach pain recently."
    
    message_data = {'message': follow_up_message}
    message_response = requests.post(
        f"{base_url}/ai-chat/sessions/{session_id}/messages",
        headers=headers,
        json=message_data
    )
    
    if message_response.status_code == 200:
        ai_response = message_response.json()
        print(f"👤 Patient: '{follow_up_message}'")
        print(f"🤖 AI Follow-up: '{ai_response.get('response', 'No response')}'")
        
        # Check if AI is asking relevant follow-up questions
        response_text = ai_response.get('response', '').lower()
        if any(word in response_text for word in ['how long', 'describe', 'when', 'what type', 'scale', 'severity']):
            print("✓ AI IS ASKING RELEVANT FOLLOW-UP QUESTIONS")
        else:
            print("⚠️  AI response may not be asking appropriate follow-up questions")
    
    print("\n=== TEST SUMMARY ===")
    return True

if __name__ == "__main__":
    success = test_proactive_chat()
    sys.exit(0 if success else 1)
