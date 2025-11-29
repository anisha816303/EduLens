# EduLens: AI-Powered Academic Evaluation System

*Transforming Education Through Intelligent Assessment*

---

<div align="center">

**[Live Demo on Streamlit](https://edulens.streamlit.app/)**

</div>

---

## 🚀 Key Features

<div align="center">
  <table width="100%">
    <tr valign="top">
      <td width="50%">
        <h3>👨‍🏫 For Teachers</h3>
        <ul>
          <li>✅ Upload rubrics in PDF format</li>
          <li>✅ AI-powered rubric extraction</li>
          <li>✅ Automated bluebook marks extraction</li>
          <li>✅ Set deadlines & attempt limits</li>
          <li>✅ Real-time submission tracking</li>
          <li>✅ Comprehensive grading analytics</li>
        </ul>
      </td>
      <td width="50%">
        <h3>👨‍🎓 For Students</h3>
        <ul>
          <li>✅ Submit reports for instant grading</li>
          <li>✅ Get detailed AI feedback</li>
          <li>✅ Track submission attempts</li>
          <li>✅ View rubric-based scores</li>
          <li>✅ Download grading history</li>
          <li>✅ Monitor academic progress</li>
        </ul>
      </td>
    </tr>
  </table>
</div>

---

## 🤖 Powered by Advanced AI Technology

EduLens combines cutting-edge artificial intelligence with intuitive design to revolutionize academic evaluation. Our platform uses **YOLO** for precise bluebook detection and **Gemini AI** for intelligent assessment, providing instant, accurate feedback that helps both educators and students achieve excellence.

---

## ✨ Why Choose EduLens?

<div align="center">
  <table width="100%">
    <tr valign="top">
      <td align="center" width="25%">
        <h3>⚡<br>Lightning Fast</h3>
        <p>Instant results in seconds</p>
      </td>
      <td align="center" width="25%">
        <h3>🎯<br>Precision Grading</h3>
        <p>High accuracy grading</p>
      </td>
      <td align="center" width="25%">
        <h3>🤖<br>AI-Powered</h3>
        <p>Advanced machine learning</p>
      </td>
      <td align="center" width="25%">
        <h3>📊<br>Smart Analytics</h3>
        <p>Comprehensive insights</p>
      </td>
    </tr>
  </table>
</div>

---

## 💻 Tech Stack

- **Backend**: Python, FastAPI
- **Frontend**: Streamlit
- **Computer Vision**: OpenCV, YOLOv8
- **AI/ML**: Google Gemini, PyTorch, Transformers
- **Core Libraries**: Langchain, Pydantic

## 🚀 Getting Started (Local Development)

For those who wish to contribute or run the project locally:

### Prerequisites

- Python 3.9+
- Git

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/anisha816303/EduLens.git
    cd EduLens
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv .venv
    .venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    This project has dependencies in two separate files. Install both using pip:
    ```bash
    pip install -r acad_eval/requirements.txt
    pip install -r acad_eval/frontend/requirements.txt
    ```

4.  **Set up Environment Variables:**
    Create a file named `.env` in the project's root directory. Add your Google API key to this file:
    ```env
    GOOGLE_API_KEY="your_google_api_key_here"
    ```

### Running the Application

1.  **Launch the Streamlit App:**
    From the root directory of the project, run the following command:
    ```bash
    streamlit run acad_eval/frontend/EduLens.py
    ```

2.  Open your browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
