
# 🌐 **SurfAgent: The  Web Search and Analysis Agent**

SurfAgent is a sophisticated **CLI-based agent** built from scratch. Powered by **Selenium** and **Brave Search**, SurfAgent extracts relevant information and even analyzes images related to your queries and **quotes** Sources of that information in the form of links as well, leveraging state-of-the-art **Llama Vision Models**. These models are compatible with **GROQ** or **OLLAMA**, offering seamless integration.

---

## ✨ **Key Features**

### 📁 Contextual Memory
SurfAgent remembers and learns from past interactions, storing details in a dynamic memory system. Memory snapshots are available in a JSON format, providing insights like:
```json
{
    "query_types": "",
    "last_success": "",
    "last_failure": "",
    "total_attempts": "",
    "successful_attempts": "",
    "average_response_time": "",
    "notes": ""
}
```

### 🚫 Intelligent Host Management
SurfAgent keeps a record of problematic hosts in a `HOSTS.txt` file, ensuring those hosts are avoided in future searches.

<img src="extras/pawelzmarlak-2025-01-22T16_41_02.675Z.png" alt="ALT TEXT" width="750">

### 🖼️ Image Analysis
Integrates advanced image processing capabilities by fetching relevant images based on user input or context, then passing these images to **Llama Vision Models**. These models analyze the images to extract key information, such as text, objects, patterns, or any visual data present, and process it to generate meaningful insights or responses.

### 🔗 LangChain Integration
Utilizes **LangChain tools** to enhance automation and analytical capabilities.

---

## 🚀 **How to Run SurfAgent**

To get started with SurfAgent, follow these simple steps:

### 🛠️ **Step 1: Clone the Repository**

First, clone the SurfAgent repository from GitHub to your local machine. Open your terminal or command prompt and run the following command:

```bash
git clone https://github.com/Haseebasif7/SurfAgent.git
```

### 🛠️ **Step 2: Install the Required Dependencies**

Navigate to the `SurfAgent` directory:

```bash
cd SurfAgent
```

Then, install the required libraries by running:

```bash
pip install -r requirements.txt
```

This will install the necessary packages, including **Selenium**, **Brave Search**, **Llama Vision Models**, **LangChain**, and more.

### 🔑 **Step 3: Set Up Environment Variables**

Create a `.env` file in the root directory of the SurfAgent project and add your API keys for **GROQ** and **Brave Search**:

```env
GROQ_API_KEY="your_groq_api_key"
BRAVE_API_KEY="your_brave_api_key"
```

Make sure to replace `"your_groq_api_key"` and `"your_brave_api_key"` with your actual API keys.

### 🖥️ **Step 4: Run the SurfAgent**

Once the dependencies are installed and environment variables are set, you're ready to run SurfAgent. Execute the following command to start the agent:

```bash
python main.py
```

SurfAgent will now initialize, begin processing web searches, and provide results based on your queries. Enjoy enhanced web search capabilities with intelligent memory, host management, and image analysis!

---

### 🧑‍💻 **Troubleshooting && Contributions**

If you encounter any issues during installation or want to add some new feature, feel free to :

- Open an Issue or Open an Pull Request to Contribute

---
