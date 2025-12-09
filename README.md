# Job Resume Matching with Grok API

A FastAPI-based application for extracting and analyzing resume details using Grok AI.


## Prerequisites

- Python 3.8+
- Git
- Grok API Key

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/job-resume-matching-grokapi.git
cd job-resume-matching-grokapi
```

### 2. Navigate to Backend Folder

```bash
cd backend
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the `backend` folder:

```bash
# Create .env file
touch .env
```

Add your Grok API key to the `.env` file:

```env
GROK_API_KEY=your_grok_api_key_here
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The application will start on `http://localhost:8000`

## API Documentation

Once the server is running, access the interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
job-resume-matching-grokapi/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── schemas/
│   │   └── ...
│   ├── requirements.txt
│   ├── .env
│   └── venv/
└── README.md
```



## Troubleshooting

**Issue**: Module not found error
- **Solution**: Make sure you've activated the virtual environment and installed all dependencies

**Issue**: Port already in use
- **Solution**: Use a different port: `uvicorn app.main:app --reload --port 8001`

**Issue**: Grok API authentication error
- **Solution**: Verify your `GROK_API_KEY` in the `.env` file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please open an issue on GitHub.

---

Made with  using FastAPI and Grok AI
