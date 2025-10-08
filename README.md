

# InfoMosaic

<div align="center">
  <img src="assets/infomosaic.png" alt="InfoMosaic Logo" />
  <p><em>An Advanced Framework for Information Retrieval and Evaluation</em></p>
</div>

<div align="center">
  <img src="assets/overview.png" alt="InfoMosaic Overview" width="80%" />
  <p><em>InfoMosaic System Overview</em></p>
</div>

## 📚 Project Overview

InfoMosaic is a comprehensive framework designed for advanced information retrieval, multi-step reasoning, and performance evaluation of large language models (LLMs). This project is based on the research paper ["InfoMosaic: A Multimodal, Multi-Source Benchmark for Information Integration and Reasoning"](https://arxiv.org/pdf/2510.02271) and leverages the [InfoMosaic_Bench dataset](https://huggingface.co/datasets/Dorothydu/InfoMosaic_Bench) for evaluation.

The framework enables:
- Multi-source information retrieval and integration
- Rigorous evaluation of LLM's reasoning capabilities
- Flexible tool usage for enhanced information acquisition
- Parallel processing for efficient benchmarking

## 📁 Project Structure

```
InfoMosaic/
├── data/                   # Data preparation and management
│   ├── info_mosaic_gt_answer.jsonl  # Ground truth answers
│   ├── info_mosaic_w_gt.jsonl       # Combined query and ground truth data
│   └── prepare_data.py              # Script to prepare and combine datasets
├── eval/                   # Evaluation utilities
│   └── pass_rate_eval.py            # Evaluation script for calculating pass rates
├── inference/              # Inference components
│   ├── __init__.py
│   ├── gpt5_multi_tool.py           # Multi-tool integration
│   └── tool_manager.py              # Tool management
├── tool_backends/          # Backend services for tools
│   ├── MCP/                     # Multi-Content Protocol tools
│   ├── api_proxy/               # API proxies
│   ├── configs/                 # Configuration files
│   └── test/                    # Test scripts for tools
├── infer_answer.py         # Main inference script
├── ensemble_answer.py      # Script to avoid answer leakage
├── gen_result.py           # Result generation
├── utils.py                # Utility functions
└── README.md               # Project documentation
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+ or Docker
- API keys for external services (serper, google_map, youtube, serapi)

### Docker Deployment

For an easier setup, use our pre-built Docker image:

```bash
# Load the Docker image
cd tool_backends
chmod +x run_docker.sh

# Run the Docker container
./run_docker.sh backend_server backend_server_image:v1

# Enter the container
docker exec -it backend_server /bin/bash
```

### Manual Setup

```bash
# Clone the repository
git clone <repository-url> # If applicable
cd InfoMosaic

# Install dependencies
pip install -r requirements.txt  # Create this file based on project needs
```

## 🚀 Usage

### Data Preparation

First, prepare the dataset by combining the HuggingFace benchmark data with ground truth answers:

```bash
python data/prepare_data.py
```

This script will:
1. Download the [InfoMosaic_Bench dataset](https://huggingface.co/datasets/Dorothydu/InfoMosaic_Bench) from HuggingFace
2. Load the ground truth answers from `data/info_mosaic_gt_answer.jsonl`
3. Combine the datasets and save to `data/info_mosaic_w_gt.jsonl`

### Running Inference

Run the inference script to evaluate a model on the benchmark:

```bash
python infer_answer.py --model_name <model-name> --parallel_size <num-threads>
```

**Key arguments:**
- `--model_name`: Name of the model to evaluate
- `--parallel_size`: Number of parallel threads for processing
- `--api_base`: Base URL for the API (if using custom endpoint)
- `--api_key`: API key for accessing the model
- `--temperature`: Temperature setting for generation

### Starting Tool Backends

To enable the full functionality with tool use:

1. Start the SSE servers:
   ```bash
   cd tool_backends
   bash MCP/deploy_sse_servers.sh
   ```

2. Start the API proxy:
   ```bash
   cd api_proxy
   python api_server.py
   ```

3. Start the MCP server:
   ```bash
   cd ../MCP
   sh deploy_server.sh
   ```

## 🔑 API Key Configuration

To use the web search and other external services, configure your API keys in the `tool_backends/configs/web_agent.json` file:

```json
{
    "serper_api_key": "your_serper_api_key",
    "search_region": "us",
    "search_lang": "en",
    "USE_MODEL": "gpt-4o",
    "BASE_MODEL": "qwen-32b"
}
```

## 📊 Evaluation

Evaluate the model's performance using the pass rate evaluation script:

```bash
python eval/pass_rate_eval.py
```

This script will:
1. Load the model's generated answers
2. Use a judge LLM to evaluate the correctness of answers
3. Calculate pass rates for sub-questions and final answers
4. Generate detailed evaluation metrics

## 📚 Citation

If you use this framework or dataset in your research, please cite our paper:

```
@article{InfoMosaic2025,
  title={InfoMosaic: A Multimodal, Multi-Source Benchmark for Information Integration and Reasoning},
  author={Du, Dorothy and et al.},
  journal={arXiv preprint arXiv:2510.02271},
  year={2025}
}
```

And the dataset:

```
@dataset{InfoMosaic_Bench,
  title = {InfoMosaic_Bench},
  author = {Dorothydu},
  year = {2025},
  publisher = {Hugging Face},
  url = {https://huggingface.co/datasets/Dorothydu/InfoMosaic_Bench}
}
```

## 🔗 Links
- [Research Paper](https://arxiv.org/pdf/2510.02271)
- [HuggingFace Dataset](https://huggingface.co/datasets/Dorothydu/InfoMosaic_Bench)

## 🤝 Contributing

Contributions to improve InfoMosaic are welcome! Please refer to the project's GitHub repository (if available) for contribution guidelines.

## 📝 License

[Add license information here]