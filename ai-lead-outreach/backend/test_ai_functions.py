import sys
import os
sys.path.append(os.path.dirname(__file__))

from app import agent_analyze_business, agent_decide_outreach, agent_message_strategy, agent_generate_message

# Test the analysis function
lead = {'name': 'Test', 'company': 'Tech Corp', 'location': 'Chennai'}

print("Testing AI analysis functions...")
print("=" * 50)

# Test business analysis
print("1. Testing agent_analyze_business:")
result = agent_analyze_business(lead)
print(f"   Input: {lead}")
print(f"   Output: {result}")
print(f"   Type: {type(result)}")
print()

# Test outreach decision
print("2. Testing agent_decide_outreach:")
decision = agent_decide_outreach(result)
print(f"   Input analysis: {result}")
print(f"   Output: {decision}")
print(f"   Type: {type(decision)}")
print()

# Test message strategy
print("3. Testing agent_message_strategy:")
strategy = agent_message_strategy(lead, result)
print(f"   Input lead: {lead}")
print(f"   Input analysis: {result}")
print(f"   Output: {strategy}")
print(f"   Type: {type(strategy)}")
print()

# Test message generation
print("4. Testing agent_generate_message:")
message = agent_generate_message(result, strategy)
print(f"   Input analysis: {result}")
print(f"   Input strategy: {strategy}")
print(f"   Output: {message}")
print(f"   Type: {type(message)}")
print()

print("All tests completed!")