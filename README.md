<<<<<<< HEAD
# Swin SACA Web Prototype

## Run in VS Code
1. Open this folder in VS Code.
2. Open Terminal.
3. Create virtual environment:
   - Windows: `python -m venv .venv`
   - Mac: `python3 -m venv .venv`
4. Activate it:
   - Windows: `.venv\\Scripts\\activate`
   - Mac: `source .venv/bin/activate`
5. Install packages:
   - `pip install -r requirements.txt`
6. Start app:
   - `python app.py`
7. Open browser:
   - `http://127.0.0.1:5000`

## Demo examples
- English: `I have chest pain and hard to breathe`
- English: `I have vomiting, diarrhea and dry mouth`
- Prototype Yolŋu Matha mixed phrase: `rirri rerri and gorruŋ`

## Project structure
- `app.py` - Flask app entry point
- `app/routes.py` - Web routes and APIs
- `app/translation.py` - Prototype translation + symptom extraction
- `app/ml_service.py` - Model training and prediction
- `data/triage_training_data.csv` - Sample training data for the demo
- `data/yolngu_dictionary.json` - Prototype phrase dictionary
- `templates/index.html` - Frontend page
- `static/` - CSS and JavaScript

## Notes
- The app automatically compares **Random Forest** and **XGBoost** and chooses the better one based on weighted F1 score.
- Voice input depends on browser speech recognition support.
- For a stronger future version, you can replace browser speech recognition with **Vosk** or Android speech APIs and expand the community-approved translation dictionary.
=======
# TIRP_2026_GROUP4-
SACA for severity classification using Machine Learning and NLP techniques.
>>>>>>> 9e5535e51a3e3b25b72939d48aafa78d3bc1ca33
