# EduLens: AI-Powered Academic Evaluation System

*Transforming Education Through Intelligent Assessment*

---

<div align="center">

**[Live Demo on Streamlit](https://your-streamlit-app-url.streamlit.app)**

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

## 💻 Tech Stack

- **Backend**: Python, FastAPI
- **Frontend**: Streamlit
- **Computer Vision**: OpenCV, YOLOv8
- **AI/ML**: Google Gemini, PyTorch, Transformers
- **Core Libraries**: Langchain, Pydantic

## 🚀 Local Development

For those who wish to contribute or run the project locally:

### Prerequisites

- Python 3.9+
- A `GOOGLE_API_KEY` environment variable.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/anisha816303/EduLens.git
    cd EduLens
    ```

2.  **Install dependencies:**
    ```bash
    # For the core evaluation service
    pip install -r acad_eval/requirements.txt

    # For the frontend dashboard
    pip install -r frontend/requirements.txt
    ```

3.  **Run the frontend:**
    ```bash
    streamlit run frontend/EduLens.py
    ```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
