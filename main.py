from config.log import logger
from test.selenium import test_selenium
import sys
from Model.provider import ModelProvider
from test.test_model import test_model_provider
from configure.llama import configure_llama
from config.settings import BRAVE_API_KEY
from langchain_community.tools import BraveSearch, WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from agent.web_agent import WebAgent
import time

def print_banner():
    banner = """
\033[92m
 ____  _  _  ____  ____     __    ___  ____  __ _  ____ 
/ ___)/ )( \(  _ \(  __)   / _\  / __)(  __)(  ( \(_  _)
\___ \) \/ ( )   / ) _)   /    \( (_ \ ) _) /    /  )(  
(____/\____/(__\_)(__)    \_/\_/ \___/(____)\_)__) (__) 
\033[0m
"""
    print(banner)
    print("\033[92mSurf: Your Intelligent Web Companion!\033[0m\n")

def print_separator():
    print("=" * 80)

def main():
    print_banner()
    print("Initializing SurfAgent...")
    time.sleep(1)
    
    if not test_selenium():
        logger.error("Selenium service check failed")
        print("Error: Selenium service is not working. Exiting.")
        sys.exit(1)
    
    provider = input("Choose model provider (ollama/groq): ").lower().strip()
    if provider not in [ModelProvider.OLLAMA, ModelProvider.GROQ]:
        logger.error("Invalid provider choice")
        print("Error: Invalid provider. Exiting.")
        sys.exit(1)
    
    if not test_model_provider(provider):
        logger.error(f"Model provider {provider} check failed")
        print(f"Error: Model provider {provider} is not functioning correctly. Exiting.")
        sys.exit(1)
    
    llm, prompt, provider = configure_llama()
    
    if not BRAVE_API_KEY:
        logger.warning("Brave Search API key not set. Searches will not return results.")
        print("Warning: Brave Search API key not found. Limited functionality.")
    
    brave_search = BraveSearch.from_api_key(
        api_key=BRAVE_API_KEY,
        search_kwargs={"count": 6}
    )
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    retriever = None
    agent = WebAgent(retriever, llm, prompt, brave_search, wikipedia, provider)
    
    print("SurfAgent is ready to assist you! 🚀\n")
    print_separator()
    
    while True:
        try:
            topic = input("\n🌐 Enter a topic for web search (or type 'quit' to exit): ").strip()
            if topic.lower() == 'quit':
                print("\n👋 Thank you for using SurfAgent. Goodbye!")
                break
            
            if not topic:
                print("⚠️ Please enter a valid topic.")
                continue
            logger.info(f"Starting research for topic: {topic}")
            print(f"\n🔍 Researching: {topic}...")
            report = agent.generate_report(topic)
            
            print("\n📜 Response:")
            print_separator()
            print(report)
            print_separator()
            
            feedback = input("\n✅ Was this information accurate? (y/n): ").lower().strip()
            if feedback in ['y', 'n']:
                is_accurate = feedback == 'y'
                notes = input("📝 Any additional notes? (Enter to skip): ").strip()
                agent.record_human_feedback(topic, is_accurate, notes if notes else None)
                print("🙏 Thank you for your feedback!")
            
        except KeyboardInterrupt:
            print("\n🛑 Research interrupted by user.")
            break
        except Exception as e:
            logger.error(f"Error during research: {str(e)}")
            print("⚠️ An error occurred. Please try again.")
            continue

if __name__ == "__main__":
    main()
