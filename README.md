# reInvent 👋

**reInvent is a self-hosted AI assistant platform designed to operate entirely offline.** It supports various LLM runners like **Ollama** and **OpenAI-compatible APIs**, with **built-in inference engine** for RAG, making it a **powerful AI deployment solution**.

## Key Features ⭐

- 🚀 **Effortless Setup**: Install seamlessly using Docker or Kubernetes for a hassle-free experience.

- 🤝 **Ollama/OpenAI API Integration**: Effortlessly integrate OpenAI-compatible APIs for versatile conversations alongside Ollama models.

- 🛡️ **Granular Permissions and User Groups**: Secure user environment with detailed user roles and permissions.

- 🔄 **SCIM 2.0 Support**: Enterprise-grade user and group provisioning through SCIM 2.0 protocol.

- 📱 **Responsive Design**: Seamless experience across Desktop PC, Laptop, and Mobile devices.

- 📱 **Progressive Web App (PWA)**: Native app-like experience on mobile devices with offline access.

- ✒️🔢 **Full Markdown and LaTeX Support**: Comprehensive Markdown and LaTeX capabilities for enriched interaction.

- 🎤📹 **Hands-Free Voice/Video Call**: Integrated hands-free voice and video call features.

- 🛠️ **Model Builder**: Easily create Ollama models via the Web UI.

- 🐍 **Native Python Function Calling Tool**: Built-in code editor support for custom Python functions.

- 📚 **Local RAG Integration**: Retrieval Augmented Generation (RAG) support with seamless document integration.

- 🔍 **Web Search for RAG**: Perform web searches and inject results directly into your chat experience.

- 🌐 **Web Browsing Capability**: Integrate websites into your chat using URL commands.

- 🎨 **Image Generation Integration**: Seamlessly incorporate image generation capabilities.

- ⚙️ **Many Models Conversations**: Engage with various models simultaneously.

- 🔐 **Role-Based Access Control (RBAC)**: Secure access with restricted permissions.

- 🌐🌍 **Multilingual Support**: Experience reInvent in your preferred language.

- 🧩 **Pipelines Plugin Support**: Integrate custom logic and Python libraries.

- 🌟 **Continuous Updates**: Regular updates, fixes, and new features.

## How to Install 🚀

### Installation via Python pip 🐍

reInvent can be installed using pip, the Python package installer. Before proceeding, ensure you're using **Python 3.11** to avoid compatibility issues.

1. **Install reInvent**:
   Open your terminal and run the following command:

   ```bash
   pip install open-webui
   ```

2. **Running reInvent**:
   After installation, you can start reInvent by executing:

   ```bash
   open-webui serve
   ```

This will start the reInvent server, which you can access at [http://localhost:8080](http://localhost:8080)

### Quick Start with Docker 🐳

> [!WARNING]
> When using Docker to install reInvent, make sure to include the `-v open-webui:/app/backend/data` in your Docker command. This step is crucial as it ensures your database is properly mounted and prevents any loss of data.

### Installation with Default Configuration

- **If Ollama is on your computer**, use this command:

  ```bash
  docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name reinvent --restart always ghcr.io/open-webui/open-webui:main
  ```

- **If Ollama is on a Different Server**, use this command:

  ```bash
  docker run -d -p 3000:8080 -e OLLAMA_BASE_URL=https://example.com -v open-webui:/app/backend/data --name reinvent --restart always ghcr.io/open-webui/open-webui:main
  ```

- **To run reInvent with Nvidia GPU support**, use this command:

  ```bash
  docker run -d -p 3000:8080 --gpus all --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name reinvent --restart always ghcr.io/open-webui/open-webui:cuda
  ```

### Installation for OpenAI API Usage Only

- **If you're only using OpenAI API**, use this command:

  ```bash
  docker run -d -p 3000:8080 -e OPENAI_API_KEY=your_secret_key -v open-webui:/app/backend/data --name reinvent --restart always ghcr.io/open-webui/open-webui:main
  ```

### Installing reInvent with Bundled Ollama Support

This installation method uses a single container image that bundles the application with Ollama, allowing for a streamlined setup via a single command.

- **With GPU Support**:

  ```bash
  docker run -d -p 3000:8080 --gpus=all -v ollama:/root/.ollama -v open-webui:/app/backend/data --name reinvent --restart always ghcr.io/open-webui/open-webui:ollama
  ```

- **For CPU Only**:

  ```bash
  docker run -d -p 3000:8080 -v ollama:/root/.ollama -v open-webui:/app/backend/data --name reinvent --restart always ghcr.io/open-webui/open-webui:ollama
  ```

After installation, you can access reInvent at [http://localhost:3000](http://localhost:3000). Enjoy! 😄

### Other Installation Methods

We offer various installation alternatives, including non-Docker native installation methods, Docker Compose, Kustomize, and Helm.

### Using the Dev Branch 🌙

> [!WARNING]
> The `:dev` branch contains the latest unstable features and changes. Use it at your own risk as it may have bugs or incomplete features.

```bash
docker run -d -p 3000:8080 -v open-webui:/app/backend/data --name reinvent --add-host=host.docker.internal:host-gateway --restart always ghcr.io/open-webui/open-webui:dev
```

### Offline Mode

If you are running reInvent in an offline environment, you can set the `HF_HUB_OFFLINE` environment variable to `1` to prevent attempts to download models from the internet.

```bash
export HF_HUB_OFFLINE=1
```

---

## Frontend Setup (User Interface)

### 2. Frontend Setup

#### Configure Environment Variables

```bash
cp -RPp .env.example .env
```

Open `.env` and customize values if needed.  
Do not commit sensitive environment variables.

#### Install Frontend Dependencies

Navigate to the project root:

```bash
cd reInvent
```

Install all required packages:

```bash
npm install
```

If warnings/errors appear:

```bash
npm install --force
```

#### Start the Frontend Development Server

```bash
npm run dev
```

Visit the frontend at:

http://localhost:5173

Leave this terminal running.

### 2.5 Build the Frontend (Recommended)

```bash
npm run build
```

This generates an optimized production-ready build inside the `build` directory.

---

## Authors

| Author            | Date          | Action             |
|-------------------|---------------|--------------------|
| Souveek Pradhan   | Nov 5, 2025   | Creation           |
| Hardik Prashar    | Dec 12, 2025  | First Modification |
