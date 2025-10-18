from strands import Agent
import os

def main():
    """Simple query agent example with proper response handling."""
    
    try:
        # Create agent
        agent = Agent(
            model="apac.anthropic.claude-sonnet-4-20250514-v1:0"
        )
        
        # Make request
        response = agent("What is the capital of France?")
        
        # Extract the actual content from AgentResult
        if hasattr(response, 'message') and 'content' in response.message:
            content = response.message['content']
            if isinstance(content, list) and len(content) > 0:
                # Extract text from content
                text_content = content[0].get('text', str(content[0]))
                print(f"Response: {text_content}")
            else:
                print(f"Response: {content}")
        else:
            print(f"Response: {response}")
            
        # Print metrics if available
        if hasattr(response, 'metrics'):
            metrics = response.metrics
            print(f"Tokens used: {metrics.accumulated_usage.get('totalTokens', 'N/A')}")
            print(f"Latency: {metrics.accumulated_metrics.get('latencyMs', 'N/A')}ms")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have:")
        print("1. AWS credentials configured (aws configure)")
        print("2. Proper AWS permissions for Bedrock")
        print("3. The model 'apac.anthropic.claude-sonnet-4-20250514-v1:0' is available in your region")

if __name__ == "__main__":
    main()